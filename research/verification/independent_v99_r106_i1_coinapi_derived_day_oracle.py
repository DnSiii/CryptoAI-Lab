"""Independent source-byte replay of CoinAPI DERIVED-only day; no primary imports.

Not an independent exchange certification or a source of trade/fill/ROI claims.
"""
from __future__ import annotations
import csv
import gzip
import hashlib
import heapq
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HEAD = ("exchange", "symbol", "timestamp", "local_timestamp",
        "bid_price", "ask_price", "bid_amount", "ask_amount")
ORIGINAL = ("id_site_coinapi", "time_exchange", "time_coinapi",
            "ask_px", "ask_sx", "bid_px", "bid_sx")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def ticks(value):
    if "." in value:
        fraction = value.split(".", 1)[1].split("+", 1)[0].rstrip("Z")
    else:
        fraction = ""
    if len(fraction) > 7 and any(x != "0" for x in fraction[7:]):
        raise AssertionError("INDEPENDENT_SUB100NS_CLOCK")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if dt.utcoffset().total_seconds() != 0:
        raise AssertionError("INDEPENDENT_NONUTC_CLOCK")
    return int(dt.replace(microsecond=0).timestamp()) * 10000000 + int(
        fraction[:7].ljust(7, "0") or "0")


def original_rows(path, symbol):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        header = stream.readline().rstrip("\r\n")
        if header not in (",".join(ORIGINAL), ";".join(ORIGINAL)):
            raise AssertionError("INDEPENDENT_ORIGINAL_HEADER")
        delimiter = "," if header == ",".join(ORIGINAL) else ";"
        reader = csv.DictReader(stream, fieldnames=ORIGINAL, delimiter=delimiter, strict=True)
        last = -1
        for row in reader:
            if row.get(None) is not None or any(row.get(k) is None for k in ORIGINAL):
                raise AssertionError("INDEPENDENT_ORIGINAL_MALFORMED_ROW")
            e, a = ticks(row["time_exchange"]), ticks(row["time_coinapi"])
            if e > a or a < last:
                raise AssertionError("INDEPENDENT_ORIGINAL_CLOCK")
            last = a
            vals = [str(Decimal(row[k])) for k in (
                "bid_px", "ask_px", "bid_sx", "ask_sx")]
            yield a, {
                "exchange": "deribit", "symbol": symbol,
                "timestamp": str(e//10), "local_timestamp": str((a+9)//10),
                "bid_price": vals[0], "ask_price": vals[1],
                "bid_amount": vals[2], "ask_amount": vals[3],
            }


def verify(specification, root):
    spec = json.loads(Path(specification).read_text(encoding="utf-8"))
    day = spec["day"]
    root = Path(root)
    report = json.loads((root/(day+".coinapi-derived.json")).read_text(encoding="utf-8"))
    target = root/(day+".csv.gz")
    if (report.get("status") != "DERIVED_ONLY_NOT_ORIGINAL_SOURCE"
            or report.get("promotion_authorized") is not False
            or report.get("original_economic_train_executed") is not False
            or report.get("derived_file_must_never_be_attested_as_original") is not True
            or report.get("derived_gzip_sha256") != sha(target)
            or len(spec["sources"]) != len(report.get("original_sources", []))):
        raise AssertionError("INDEPENDENT_DERIVED_PROVENANCE_MISMATCH")
    pending = []
    generators = []
    for i, entry in enumerate(spec["sources"]):
        attested = report["original_sources"][i]
        if (sha(entry["path"]) != entry["sha256"]
                or attested["original_gzip_sha256"] != entry["sha256"]
                or attested["source_key"] != entry["source_key"]
                or attested["symbol"] != entry["symbol"]):
            raise AssertionError("INDEPENDENT_ORIGINAL_BYTES_OR_IDENTITY_MISMATCH")
        iterator = iter(original_rows(entry["path"], entry["symbol"]))
        generators.append(iterator)
        first = next(iterator, None)
        if first is not None:
            heapq.heappush(pending, (first[0], i, first[1]))
    count = 0
    with gzip.open(target, "rt", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream, strict=True)
        if tuple(reader.fieldnames or ()) != HEAD:
            raise AssertionError("INDEPENDENT_DERIVED_COLUMNS_MISMATCH")
        for actual in reader:
            if not pending:
                raise AssertionError("INDEPENDENT_DERIVED_EXTRA_ROW")
            _, i, expected = heapq.heappop(pending)
            if actual != expected:
                raise AssertionError("INDEPENDENT_DERIVED_ROW_OR_CLOCK_MISMATCH")
            count += 1
            following = next(generators[i], None)
            if following is not None:
                heapq.heappush(pending, (following[0], i, following[1]))
    if pending or count != report.get("derived_rows"):
        raise AssertionError("INDEPENDENT_DERIVED_INCOMPLETE_ROWS")
    return {"status": "INDEPENDENT_DERIVED_BYTE_REPLAY_MATCH_NOT_ORIGINAL_ECONOMICS",
            "rows": count, "original_files": len(generators),
            "promotion_authorized": False, "economic_train_executed": False}
