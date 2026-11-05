#!/usr/bin/env python3
"""V99 R106 independent TRAIN boundary and provenance preflight.

Fail closed: only TRAIN rows strictly before 2023-10-01 UTC may enter
candidate evaluation. This program NEVER reads validation/holdout data.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

CUTOFF = dt.datetime(2023, 10, 1, tzinfo=dt.timezone.utc)
REQUIRED = ("timestamp", "btc_open", "eth_open")

def parse_time(raw):
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    t = dt.datetime.fromisoformat(s)
    if t.tzinfo is None:
        raise ValueError("timestamp missing timezone")
    return t.astimezone(dt.timezone.utc)

def audit(path, expected_sha256):
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if not expected_sha256 or digest.lower() != expected_sha256.lower():
        raise ValueError("source SHA256 mismatch or missing")
    count = 0
    previous = None
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if (not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames))
                or not set(REQUIRED).issubset(reader.fieldnames)):
            raise ValueError("missing or duplicate source columns")
        if not all(name and name.strip() == name for name in reader.fieldnames):
            raise ValueError("missing required source columns")
        for row in reader:
            if None in row or any(value is None or not value.strip() for value in row.values()):
                raise ValueError("malformed, truncated or blank CSV row")
            t = parse_time(row["timestamp"])
            if t >= CUTOFF:
                raise ValueError("SEALED_VALIDATION_OR_HOLDOUT_ROW")
            if previous is not None and t <= previous:
                raise ValueError("timestamps not strictly increasing")
            for key in ("btc_open", "eth_open"):
                value = float(row[key])
                if not math.isfinite(value) or value <= 0:
                    raise ValueError("invalid price: " + key)
            previous = t
            count += 1
    if count < 2:
        raise ValueError("insufficient TRAIN rows")
    return {"status": "TRAIN_ONLY_SOURCE_PREFLIGHT_PASS", "rows": count,
            "last_train_timestamp": previous.isoformat(), "sha256": digest,
            "economic_validation": False, "promotion": False}

def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        p = Path(directory) / "sample.csv"
        def check(data, success):
            p.write_text("timestamp,btc_open,eth_open\n" + data, encoding="utf-8")
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            try:
                audit(p, sha)
                got = True
            except ValueError:
                got = False
            assert got == success, (data, got, success)
        check("2023-09-29T00:00:00Z,100,10\n2023-09-30T00:00:00Z,101,11\n", True)
        check("2023-09-30T00:00:00Z,100,10\n2023-10-01T00:00:00Z,101,11\n", False)
        check("2023-09-30T00:00:00Z,100,10\n2023-09-30T00:00:00Z,101,11\n", False)
        check("2023-09-29T00:00:00,100,10\n2023-09-30T00:00:00,101,11\n", False)
        check("2023-09-29T00:00:00Z,100,10\n2023-09-30T00:00:00Z,-1,11\n", False)
        check("2023-09-29T00:00:00Z,100,10,EXTRA\n2023-09-30T00:00:00Z,101,11\n", False)
        check("2023-09-29T00:00:00Z,100,10\n2023-09-30T00:00:00Z,101\n", False)
        check("2023-09-29T00:00:00Z,100,10\n2023-09-30T00:00:00Z,,11\n", False)
    print("8/8 TRAIN boundary selftests PASS; NOT an economic backtest")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv")
    parser.add_argument("--sha256")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        if not args.csv or not args.sha256:
            parser.error("--csv and --sha256 required")
        print(json.dumps(audit(args.csv, args.sha256), sort_keys=True))
