"""Fail-closed ORIGINAL options quote tape intake for I1. No economics/orders.

Unlike the two-day sample gate, accepts 91 original Sunday CSV(.gz) captures
for Monday TRAIN decisions. No sealed future data, no inferred fills.
"""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
START = datetime(2021, 12, 9, tzinfo=UTC)
END = datetime(2023, 10, 1, tzinfo=UTC)
ASSETS = ("BTC", "ETH")
REQUIRED = ("exchange", "symbol", "timestamp", "local_timestamp",
            "bid_price", "ask_price", "bid_amount", "ask_amount")


def decisions():
    first = START + timedelta(days=(7 - START.weekday()) % 7)
    return [first + timedelta(days=7*i) for i in range(94)]


def eligible():
    ds = decisions()
    assert len(ds) == 94 and ds[0] >= START and ds[-1] < END
    yes = [d for d in ds if d + timedelta(days=21) < END]
    assert len(yes) == 91
    return yes


def file_digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def instrument(symbol):
    p = symbol.split("-")
    if len(p) != 4 or p[0] not in ASSETS or p[3] != "P":
        return None
    try:
        expiry = datetime.strptime(p[1], "%d%b%y").replace(hour=8, tzinfo=UTC)
        strike = float(p[2])
    except (ValueError, OverflowError):
        return None
    if not math.isfinite(strike) or strike <= 0:
        return None
    return p[0], expiry, strike


def safe_path(root, name):
    if not isinstance(name, str) or Path(name).name != name or not (
            name.endswith(".csv") or name.endswith(".csv.gz")):
        raise ValueError("INVALID_ARCHIVE_FILENAME")
    path = root / name
    if not path.is_file() or path.is_symlink():
        raise ValueError("ARCHIVE_MISSING_OR_SYMLINK")
    return path


def evaluate(root):
    root = Path(root)
    manifest = json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != "I1_FULL_TRAIN_SUNDAY_ARCHIVE_V1":
        raise ValueError("BAD_ARCHIVE_SCHEMA")
    if manifest.get("venue") != "deribit" or type(manifest.get("fixture")) is not bool:
        raise ValueError("BAD_VENUE_OR_FIXTURE_FLAG")
    days = manifest.get("days")
    ds = eligible()
    if not isinstance(days, list) or len(days) != 91:
        raise ValueError("INCOMPLETE_OR_DUPLICATED_DECISION_DAYS")
    if [x.get("date") for x in days] != [
            (d-timedelta(days=1)).strftime("%Y-%m-%d") for d in ds]:
        raise ValueError("NOT_EXACT_FROZEN_SUNDAY_SCHEDULE")
    if len({x.get("file") for x in days}) != 91:
        raise ValueError("DUPLICATED_ARCHIVE_FILE")
    fold_edges = [datetime(2021,12,9,tzinfo=UTC),
                  datetime(2022,4,20,4,tzinfo=UTC),
                  datetime(2022,8,30,9,tzinfo=UTC),
                  datetime(2023,1,9,14,tzinfo=UTC),
                  datetime(2023,5,21,19,tzinfo=UTC), END]
    folds = {str(i): {a: 0 for a in ASSETS} for i in range(1,6)}
    coverage = []
    total_rows = 0
    for d, item in zip(ds, days):
        if item.get("complete_capture") is not True:
            raise ValueError("MISSING_VENDOR_COMPLETENESS_ATTESTATION")
        path = safe_path(root, item["file"])
        if file_digest(path) != item.get("sha256"):
            raise ValueError("ARCHIVE_SHA256_MISMATCH")
        open_fn = gzip.open if path.name.endswith(".gz") else open
        sunday = d - timedelta(days=1)
        lower = int(sunday.timestamp()*1_000_000)
        upper = int(d.timestamp()*1_000_000)
        cutoff = upper - 300_000_000
        latest = {}
        rows = 0
        with open_fn(path, "rt", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if not set(REQUIRED).issubset(reader.fieldnames or []):
                raise ValueError("MISSING_REQUIRED_QUOTE_COLUMNS")
            for row in reader:
                rows += 1
                if row["exchange"] != "deribit":
                    raise ValueError("UNEXPECTED_EXCHANGE")
                try:
                    arrival = int(row["local_timestamp"])
                    exchange = int(row["timestamp"])
                except (ValueError, TypeError):
                    raise ValueError("INVALID_SOURCE_TIMESTAMP")
                if not lower <= arrival < upper or exchange > arrival:
                    raise ValueError("FUTURE_OR_OUTSIDE_SUNDAY_SOURCE")
                if arrival < cutoff:
                    continue
                parsed = instrument(row["symbol"])
                if parsed is None:
                    continue
                asset, expiry, strike = parsed
                if not (timedelta(days=21) <= expiry-d <= timedelta(days=45)
                        and expiry < END):
                    continue
                try:
                    bid, ask, bs, az = (float(row[k]) for k in
                        ("bid_price","ask_price","bid_amount","ask_amount"))
                except (ValueError, TypeError):
                    continue
                if not all(map(math.isfinite,(bid,ask,bs,az))):
                    continue
                # A newer invalid quote must supersede an older valid quote.
                prior = latest.get(row["symbol"])
                if prior is None or (arrival,exchange) >= prior[:2]:
                    latest[row["symbol"]] = (arrival,exchange,asset,expiry,
                        strike,0 < bid < ask and bs > 0 and az > 0)
        if rows != item.get("rows"):
            raise ValueError("ARCHIVE_ROW_COUNT_MISMATCH")
        total_rows += rows
        strikes = defaultdict(set)
        for _,_,asset,expiry,strike,valid in latest.values():
            if valid:
                strikes[(asset,expiry)].add(strike)
        fold = next(i for i in range(1,6) if fold_edges[i-1] <= d < fold_edges[i])
        good = {}
        for asset in ASSETS:
            good[asset] = any(a == asset and len(s) >= 2
                              for (a,_),s in strikes.items())
            folds[str(fold)][asset] += int(good[asset])
        coverage.append({"decision_utc":d.isoformat(),"fold":fold,
                         "BTC":good["BTC"],"ETH":good["ETH"]})
    pairs = sum(sum(v.values()) for v in folds.values())
    return {
        "schema":"I1_FULL_TRAIN_ARCHIVE_INTAKE_RESULT_V1",
        "status":("SYNTHETIC_FIXTURE_ONLY_NO_ECONOMICS" if manifest["fixture"]
                  else "ORIGINAL_ARCHIVE_INPUT_CHECKED_NOT_EXECUTION_CERTIFIED"),
        "source_declared_complete_not_independently_vendor_certified":True,
        "fixture":manifest["fixture"],"train_decisions":94,
        "maturity_eligible_weeks":91,"right_censored_weeks":3,
        "required_asset_weeks":182,"two_strike_asset_weeks":pairs,
        "rows":total_rows,"folds":folds,"weekly":coverage,
        "economic_train_executed":False,"native_fee_authenticated":False,
        "native_margin_authenticated":False,"fills_authenticated":False,
        "validation_opened":False,"holdout_opened":False,
        "orders_enabled":False,"promotion_authorized":False
    }


def main(root, output):
    result = evaluate(root)
    out = Path(output)
    out.mkdir(parents=True,exist_ok=True)
    (out/"intake.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="weekly"},sort_keys=True))
    assert not result["promotion_authorized"] and not result["economic_train_executed"]


if __name__ == "__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_full_archive_intake ROOT OUT")
    main(sys.argv[1],sys.argv[2])
