"""Original 2022-06-01 Deribit options_chain same-row reference, source only.

Preregistered at 950c02b. No NAV, fills, trading, or settlement certification.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DAY = "2022-06-01"
URL = "https://datasets.tardis.dev/v1/deribit/options_chain/2022/06/01/OPTIONS.csv.gz"
MAX_BYTES = 512 * 1024 * 1024
FIELDS = {"exchange", "symbol", "timestamp", "local_timestamp",
          "type", "bid_price", "ask_price", "bid_amount", "ask_amount",
          "underlying_index", "underlying_price"}
LOWER = int(datetime(2022, 6, 1, tzinfo=timezone.utc).timestamp() * 1_000_000)
UPPER = LOWER + 86_400_000_000
FLAGS = {name: False for name in (
    "native_spot_index_authenticated", "delivery_index_authenticated",
    "native_lot_size_authenticated", "native_fee_tier_authenticated",
    "full_661d_archive_authenticated", "economic_train_executed",
    "roi_calculated", "validation_opened", "final_holdout_opened",
    "freeze_authorized", "promotion_authorized",
    "paper_publication_authorized", "orders_enabled",
)}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(target):
    """Bounded public source only. Caller owns temp file; never publish bytes."""
    target = Path(target)
    if target.exists() or target.is_symlink():
        raise ValueError("REFUSE_OVERWRITE_ORIGINAL_SOURCE")
    request = urllib.request.Request(URL, headers={
        "User-Agent": "V99-I1-public-options-chain-reference/1.0"})
    start = time.monotonic()
    total = 0
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            if response.status != 200:
                raise ValueError("ORIGINAL_CHAIN_HTTP_NOT_200")
            declared = response.headers.get("Content-Length")
            if declared is not None and int(declared) > MAX_BYTES:
                raise ValueError("ORIGINAL_CHAIN_SOURCE_OVERSIZE")
            with target.open("xb") as out:
                while True:
                    if time.monotonic() - start > 600:
                        raise ValueError("ORIGINAL_CHAIN_TRANSFER_TIMEOUT")
                    block = response.read(min(1024 * 1024, MAX_BYTES - total + 1))
                    if not block:
                        break
                    total += len(block)
                    if total > MAX_BYTES:
                        raise ValueError("ORIGINAL_CHAIN_SOURCE_OVERSIZE")
                    out.write(block)
            if declared is not None and total != int(declared):
                raise ValueError("ORIGINAL_CHAIN_TRUNCATED")
            with target.open("rb") as f:
                if f.read(2) != bytes.fromhex("1f8b"):
                    raise ValueError("ORIGINAL_CHAIN_NOT_GZIP")
        return {"status": "ORIGINAL_PUBLIC_CHAIN_TRANSFER_COMPLETE",
                "compressed_bytes": total, "sha256": digest(target)}
    except Exception:
        target.unlink(missing_ok=True)
        raise


def scan(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("ORIGINAL_CHAIN_SOURCE_MISSING")
    counts = {a: {"put_rows": 0, "valid_bbo_rows": 0,
                  "same_row_underlying_bbo_rows": 0,
                  "same_row_hour_mask": 0,
                  "index_labels": {"SYN": 0, "OTHER": 0}} for a in ("BTC", "ETH")}
    previous = -1
    rows = 0
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not FIELDS.issubset(reader.fieldnames or []):
            raise ValueError("ORIGINAL_CHAIN_REQUIRED_COLUMNS_MISSING")
        for row in reader:
            rows += 1
            if row["exchange"] != "deribit":
                raise ValueError("ORIGINAL_CHAIN_VENUE_MISMATCH")
            try:
                venue, arrival = int(row["timestamp"]), int(row["local_timestamp"])
            except (ValueError, TypeError) as exc:
                raise ValueError("ORIGINAL_CHAIN_CLOCK_INVALID") from exc
            if not (0 <= venue <= arrival and LOWER <= arrival < UPPER
                    and arrival >= previous):
                raise ValueError("ORIGINAL_CHAIN_NONCAUSAL_OR_OUT_OF_ORDER")
            previous = arrival
            parts = row["symbol"].split("-")
            if (len(parts) != 4 or parts[0] not in counts
                    or parts[-1] != "P" or row["type"] != "put"):
                continue
            asset = parts[0]
            counts[asset]["put_rows"] += 1
            try:
                bid, ask, bs, az = (float(row[k]) for k in
                                    ("bid_price", "ask_price", "bid_amount", "ask_amount"))
                good = all(math.isfinite(x) for x in (bid, ask, bs, az))
                good = good and 0 < bid < ask and bs > 0 and az > 0
            except (ValueError, TypeError):
                good = False
            if not good:
                continue
            counts[asset]["valid_bbo_rows"] += 1
            label = row["underlying_index"].strip()
            try:
                index = float(row["underlying_price"])
            except (ValueError, TypeError):
                index = float("nan")
            if not label or not math.isfinite(index) or index <= 0:
                continue
            counts[asset]["same_row_underlying_bbo_rows"] += 1
            counts[asset]["same_row_hour_mask"] |= 1 << ((arrival - LOWER) // 3_600_000_000)
            counts[asset]["index_labels"]["SYN" if label.startswith("SYN.") else "OTHER"] += 1
    if rows == 0:
        raise ValueError("ORIGINAL_CHAIN_EMPTY")
    for asset in counts:
        counts[asset]["same_row_arrival_hours"] = counts[asset].pop(
            "same_row_hour_mask").bit_count()
    return {
        "schema": "V99_I1_ORIGINAL_CHAIN_REFERENCE_SOURCE_V1",
        "status": "SOURCE_ONLY_SAME_ROW_REFERENCE_NOT_SPOT_OR_SETTLEMENT",
        "day": DAY, "source": "TARDIS_DERIBIT_OPTIONS_CHAIN_PUBLIC_SAMPLE",
        "original_compressed_sha256": digest(path),
        "original_compressed_bytes": path.stat().st_size,
        "original_rows": rows, "assets": counts,
        "source_is_public_sample_not_complete_archive": True,
        "index_may_be_synthetic_forward_not_spot": True,
        **FLAGS,
    }


def main(argv):
    if len(argv) == 3 and argv[1] == "download":
        print(json.dumps(download(argv[2]), sort_keys=True))
    elif len(argv) == 4 and argv[1] == "scan":
        result = scan(argv[2])
        Path(argv[3]).write_text(json.dumps(result, indent=2, sort_keys=True) + chr(10))
        print(json.dumps({"status": result["status"], "original_rows": result["original_rows"],
                          "assets": result["assets"], "promotion_authorized": False}, sort_keys=True))
    else:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_options_chain_reference download FILE | scan FILE REPORT")


if __name__ == "__main__":
    main(sys.argv)
