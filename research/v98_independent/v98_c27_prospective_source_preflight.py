"""V98 C27 prospective source preflight. Validation-only; never imports training reader.

Run only AFTER preregistering a future validation window. Does not execute trades.
The receipt is supplied by the data custodian; no future data is downloaded here.
"""
import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
HOUR = 3600000
TRAIN_END = 1767225600000
BASELINE = "6c609dacde9f197ba58ed23546bd14fda968a035"

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def stamp_ms(value):
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.utcoffset() is None or d.utcoffset().total_seconds() != 0:
        raise ValueError("VALIDATION_NON_UTC")
    return int(d.timestamp() * 1000)

def validate(root, receipt_path):
    root, receipt_path = Path(root).resolve(), Path(receipt_path).resolve()
    if "v98_independent" not in root.parts or "v98_independent" not in receipt_path.parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    receipt = json.loads(receipt_path.read_text())
    if (receipt.get("mode") != "V98_C27_PROSPECTIVE_SOURCE_ONLY"
            or receipt.get("candidate_commit") != BASELINE
            or receipt.get("exchange") != "Binance"
            or receipt.get("product") != "USD-M"
            or receipt.get("interval") != "1h"
            or receipt.get("phase083_used") is not False
            or receipt.get("fitting_allowed") is not False
            or set(receipt.get("assets", {})) != set(ASSETS)):
        raise ValueError("INVALID_PROSPECTIVE_RECEIPT")
    start, end = stamp_ms(receipt["start_utc"]), stamp_ms(receipt["end_utc"])
    if start < TRAIN_END or end <= start or start % HOUR or end % HOUR:
        raise ValueError("VALIDATION_WINDOW_NOT_PROSPECTIVE")
    if receipt.get("window_precommitted") is not True or not receipt.get("precommit_reference"):
        raise ValueError("VALIDATION_WINDOW_NOT_PRECOMMITTED")
    hours = (end - start) // HOUR
    for asset in ASSETS:
        entry = receipt["assets"][asset]
        if set(entry) != {"price_file", "price_sha256", "funding_file", "funding_sha256"}:
            raise ValueError("INVALID_ASSET_RECEIPT_" + asset)
        for name, hash_name in (("price_file", "price_sha256"), ("funding_file", "funding_sha256")):
            path = (root / entry[name]).resolve()
            if root not in path.parents or not path.is_file() or digest(path) != entry[hash_name]:
                raise ValueError("PROVENANCE_HASH_OR_PATH_" + asset + "_" + name)
        price = root / entry["price_file"]
        count = 0
        with price.open(newline="") as stream:
            for row in csv.DictReader(stream):
                t = stamp_ms(row["open_time"])
                if t != start + count * HOUR or t >= end:
                    raise ValueError("PROSPECTIVE_PRICE_GAP_" + asset)
                o, h, l, c, q = (float(row[k]) for k in ("open", "high", "low", "close", "quote_volume"))
                if not all(map(math.isfinite, (o, h, l, c, q))) or min(o, h, l, c) <= 0 or q < 0 or l > min(o, c) or h < max(o, c):
                    raise ValueError("PROSPECTIVE_BAD_BAR_" + asset)
                count += 1
        if count != hours:
            raise ValueError("PROSPECTIVE_INCOMPLETE_PRICES_" + asset)
        seen = set()
        with (root / entry["funding_file"]).open(newline="") as stream:
            for row in csv.DictReader(stream):
                t = stamp_ms(row["timestamp_utc"])
                rate = float(row["funding_rate"])
                if t in seen or t < start or t >= end or not math.isfinite(rate):
                    raise ValueError("PROSPECTIVE_BAD_FUNDING_" + asset)
                seen.add(t)
        if not seen:
            raise ValueError("PROSPECTIVE_EMPTY_FUNDING_" + asset)
        # Funding schedules may change; do not fabricate missing events.
        # Coverage is reported, never silently imputed or assumed 8-hourly.
    return {"status": "SOURCE_PREFLIGHT_ONLY_NOT_ECONOMIC_VALIDATION",
            "candidate_commit": BASELINE, "start_utc": receipt["start_utc"],
            "end_utc": receipt["end_utc"], "hours": hours,
            "receipt_sha256": digest(receipt_path), "assets": list(ASSETS)}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--receipt", required=True)
    args = p.parse_args()
    print(json.dumps(validate(args.root, args.receipt), sort_keys=True))
