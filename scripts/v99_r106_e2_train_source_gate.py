#!/usr/bin/env python3
"""E2 preregistered TRAIN-only source gate. No orders, no synthesized market data."""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

CUTOFF = dt.datetime(2023, 10, 1, tzinfo=dt.timezone.utc)
REQUIRED = {"timestamp", "symbol", "market_type", "open", "high", "low", "close", "volume"}
SYMBOLS = {"BTC", "ETH"}

def parse_time(s):
    t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("timezone missing")
    return t.astimezone(dt.timezone.utc)

def audit(path, expected_sha256):
    p = Path(path)
    if not p.is_file():
        raise ValueError("original hourly source missing")
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    if not expected_sha256 or digest != expected_sha256:
        raise ValueError("original source hash missing or mismatch")
    # Never parse even one post-TRAIN row. Reject at the boundary.
    seen = set()
    rows = {"BTC": [], "ETH": []}
    with p.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError("required original OHLCV columns absent")
        for row in reader:
            t = parse_time(row["timestamp"])
            if t >= CUTOFF:
                raise ValueError("TRAIN boundary reached: fail closed, no post-TRAIN data accepted")
            if t.minute or t.second or t.microsecond:
                raise ValueError("non-hourly timestamp")
            symbol = row["symbol"]
            if symbol not in SYMBOLS or row["market_type"] != "perpetual":
                raise ValueError("BTC/ETH perpetual provenance required")
            key = (symbol, t)
            if key in seen:
                raise ValueError("duplicate bar")
            seen.add(key)
            vals = [float(row[k]) for k in ("open", "high", "low", "close", "volume")]
            o, h, l, c, v = vals
            if not all(map(math.isfinite, vals)) or min(o, h, l, c) <= 0 or v < 0:
                raise ValueError("invalid price/volume")
            if h < max(o, c, l) or l > min(o, c, h):
                raise ValueError("OHLC inconsistent")
            rows[symbol].append((t, o, h, l, c, v))
    for symbol, series in rows.items():
        series.sort()
        if len(series) < 180:
            raise ValueError("insufficient complete original TRAIN hours")
        for a, b in zip(series, series[1:]):
            if b[0] - a[0] != dt.timedelta(hours=1):
                raise ValueError("hourly gap: " + symbol)
    if [r[0] for r in rows["BTC"]] != [r[0] for r in rows["ETH"]]:
        raise ValueError("BTC/ETH timestamp misalignment")
    return {"status": "SOURCE_GATE_ONLY_NO_ECONOMICS", "sha256": digest,
            "hours_per_symbol": len(rows["BTC"]),
            "first_hour": rows["BTC"][0][0].isoformat(),
            "last_hour": rows["BTC"][-1][0].isoformat(),
            "no_orders": True, "promotion": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--original-hourly-csv", required=True)
    p.add_argument("--sha256", required=True)
    a = p.parse_args()
    print(json.dumps(audit(a.original_hourly_csv, a.sha256), sort_keys=True))

if __name__ == "__main__":
    main()
