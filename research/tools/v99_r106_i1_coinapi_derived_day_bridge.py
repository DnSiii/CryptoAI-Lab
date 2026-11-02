"""DERIVED-ONLY CoinAPI per-symbol -> one daily native-shape gzip.

Never original Deribit evidence, native fee/lot certification or economic TRAIN.
Prereg: research/V99_R106_I1_COINAPI_DERIVED_DAY_BRIDGE_PREREG_20261102.md
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import heapq
import io
import json
import os
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_coinapi_quote_intake import (
    SOURCE_KEY, SITE_UUID, SYMBOL, _original_rows, nonnegative,
    original_partition, ticks100ns,
)

COLUMNS = ("exchange", "symbol", "timestamp", "local_timestamp",
           "bid_price", "ask_price", "bid_amount", "ask_amount")
SCHEMA = "V99_I1_COINAPI_DERIVED_NATIVE_DAY_ONLY_V1"
START, END = date(2021, 12, 9), date(2023, 10, 1)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _source(spec, day):
    if not isinstance(spec, dict) or set(spec) != {"path", "source_key", "symbol", "sha256"}:
        raise ValueError("INCOMPLETE_DERIVED_SOURCE_DESCRIPTOR")
    path = Path(spec["path"])
    symbol = spec["symbol"]
    key = spec["source_key"]
    if (not path.is_file() or path.is_symlink() or path.suffix != ".gz"
            or not isinstance(symbol, str) or not SYMBOL.fullmatch(symbol)
            or not isinstance(key, str) or not SOURCE_KEY.fullmatch(key)
            or not isinstance(spec["sha256"], str) or len(spec["sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in spec["sha256"])):
        raise ValueError("UNSAFE_OR_UNBOUND_DERIVED_SOURCE")
    lower, _ = original_partition(key, symbol)
    expected = int(datetime(day.year, day.month, day.day,
                            tzinfo=timezone.utc).timestamp()) * 1_000_000
    if lower != expected or digest(path) != spec["sha256"]:
        raise ValueError("SOURCE_KEY_DAY_OR_ORIGINAL_SHA_MISMATCH")
    return path, symbol


def _events(path, symbol, day):
    start = int(datetime(day.year, day.month, day.day,
                         tzinfo=timezone.utc).timestamp()) * 10_000_000
    end = start + 86400 * 10_000_000
    prior = -1
    for original, _ in _original_rows(path):
        if (original.get(None) is not None
                or any(original.get(k) is None for k in (
                    "id_site_coinapi", "time_exchange", "time_coinapi",
                    "ask_px", "ask_sx", "bid_px", "bid_sx"))):
            raise ValueError("MALFORMED_COINAPI_DERIVED_SOURCE_ROW")
        site = original["id_site_coinapi"]
        if site and not SITE_UUID.fullmatch(site):
            raise ValueError("INVALID_DERIVED_SOURCE_SITE")
        event = ticks100ns(original["time_exchange"])
        arrival = ticks100ns(original["time_coinapi"])
        if not (0 <= event <= arrival and start <= arrival < end
                and arrival >= prior):
            raise ValueError("NONCAUSAL_OR_OUT_OF_DAY_DERIVED_SOURCE")
        prior = arrival
        bid, ask, bid_size, ask_size = (
            nonnegative(original[k]) for k in
            ("bid_px", "ask_px", "bid_sx", "ask_sx")
        )
        # Ceil arrival conservatively; a quote 100ns AFTER the decision
        # cannot be backdated to the decision's exact microsecond.
        arrival_us = (arrival + 9) // 10
        event_us = event // 10
        if arrival_us >= end // 10:
            raise ValueError("CEILED_ARRIVAL_ESCAPES_ORIGINAL_DAY")
        row = {
            "exchange": "deribit", "symbol": symbol,
            "timestamp": str(event_us),
            "local_timestamp": str(arrival_us),
            "bid_price": str(bid), "ask_price": str(ask),
            "bid_amount": str(bid_size), "ask_amount": str(ask_size),
        }
        yield arrival, row


def convert(specification, output_root, *, fixture=False, license_document=None):
    """Stream sorted original partitions; write derived day and sidecar exclusively."""
    if type(fixture) is not bool:
        raise ValueError("INVALID_DERIVED_FIXTURE_FLAG")
    spec = json.loads(Path(specification).read_text(encoding="utf-8"))
    if (not isinstance(spec, dict) or set(spec) != {"schema", "day", "sources"}
            or spec["schema"] != SCHEMA or not isinstance(spec["sources"], list)
            or not 2 <= len(spec["sources"]) <= 256):
        raise ValueError("INVALID_DERIVED_DAY_SPECIFICATION")
    try:
        day = date.fromisoformat(spec["day"])
    except (ValueError, TypeError) as exc:
        raise ValueError("INVALID_DERIVED_TRAIN_DAY") from exc
    if not START <= day < END:
        raise ValueError("SEALED_OR_INVALID_DERIVED_DAY")
    if not fixture:
        if license_document is None:
            raise ValueError("DERIVED_SOURCE_WRITTEN_LICENSE_REQUIRED")
        license_path = Path(license_document)
        if (not license_path.is_file() or license_path.is_symlink()
                or not 0 < license_path.stat().st_size <= 4_000_000):
            raise ValueError("INVALID_DERIVED_LICENSE_DOCUMENT")
        license_digest = digest(license_path)
    else:
        if license_document is not None:
            raise ValueError("FIXTURE_CANNOT_CLAIM_LICENSE")
        license_digest = None
    originals, keys, symbols, assets = [], set(), set(), set()
    for item in spec["sources"]:
        path, symbol = _source(item, day)
        if item["source_key"] in keys or symbol in symbols:
            raise ValueError("DUPLICATE_DERIVED_SOURCE_IDENTITY")
        keys.add(item["source_key"])
        symbols.add(symbol)
        assets.add(symbol.split("-", 1)[0])
        originals.append((path, symbol, item))
    if assets != {"BTC", "ETH"}:
        raise ValueError("INCOMPLETE_DERIVED_BTC_ETH_SOURCE")
    root = Path(output_root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("MISSING_DERIVED_OUTPUT_DIRECTORY")
    target = root / (day.isoformat() + ".csv.gz")
    sidecar = root / (day.isoformat() + ".coinapi-derived.json")
    if any(p.exists() or p.is_symlink() for p in (target, sidecar)):
        raise ValueError("REFUSE_OVERWRITE_DERIVED_SOURCE")
    fd, tmp = tempfile.mkstemp(prefix=".coinapi-day-", suffix=".tmp", dir=root)
    os.close(fd)
    count, invalid = 0, 0
    try:
        iterators = [iter(_events(path, symbol, day)) for path, symbol, _ in originals]
        heap = []
        for i, iterator in enumerate(iterators):
            item = next(iterator, None)
            if item is not None:
                heapq.heappush(heap, (item[0], i, item[1]))
        with open(tmp, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                    writer = csv.DictWriter(text, fieldnames=COLUMNS, lineterminator="\n")
                    writer.writeheader()
                    while heap:
                        _, i, row = heapq.heappop(heap)
                        writer.writerow(row)
                        count += 1
                        if (min(float(row[k]) for k in (
                                "bid_price", "ask_price", "bid_amount", "ask_amount")) == 0
                                or float(row["bid_price"]) >= float(row["ask_price"])):
                            invalid += 1
                        item = next(iterators[i], None)
                        if item is not None:
                            heapq.heappush(heap, (item[0], i, item[1]))
            raw.flush()
            os.fsync(raw.fileno())
        if not count:
            raise ValueError("EMPTY_DERIVED_DAY")
        for path, _, item in originals:
            if digest(path) != item["sha256"]:
                raise ValueError("ORIGINAL_COINAPI_BYTES_CHANGED_DURING_DERIVATION")
        report = {
            "schema": SCHEMA, "status": "DERIVED_ONLY_NOT_ORIGINAL_SOURCE",
            "day": day.isoformat(), "fixture": fixture,
            "derived_gzip_sha256": digest(tmp), "derived_rows": count,
            "non_executable_or_crossed_rows": invalid,
            "original_sources": [{
                "source_key": item["source_key"], "symbol": symbol,
                "original_gzip_sha256": item["sha256"]
            } for _, symbol, item in originals],
            "license_document_sha256_operator_supplied_not_verified": license_digest,
            "clock_conversion": "event_floor_100ns_to_us__arrival_ceil_100ns_to_us",
            "derived_file_must_never_be_attested_as_original": True,
            "vendor_capture_completeness_certified": False,
            "native_lot_fee_margin_delivery_certified": False,
            "original_economic_train_executed": False,
            "validation_opened": False, "holdout_opened": False,
            "orders_enabled": False, "promotion_authorized": False,
        }
        fd2, tmp2 = tempfile.mkstemp(prefix=".coinapi-manifest-", suffix=".tmp", dir=root)
        try:
            with os.fdopen(fd2, "w", encoding="utf-8") as stream:
                json.dump(report, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(tmp, target)
                try:
                    os.link(tmp2, sidecar)
                except OSError:
                    target.unlink()
                    raise
            except FileExistsError as exc:
                raise ValueError("REFUSE_OVERWRITE_DERIVED_SOURCE") from exc
        finally:
            Path(tmp2).unlink(missing_ok=True)
        return report
    finally:
        Path(tmp).unlink(missing_ok=True)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("specification")
    p.add_argument("output_root")
    p.add_argument("--fixture", action="store_true")
    p.add_argument("--license-document")
    args = p.parse_args()
    print(json.dumps(convert(args.specification, args.output_root,
                             fixture=args.fixture,
                             license_document=args.license_document), sort_keys=True))
