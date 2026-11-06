#!/usr/bin/env python3
"""Fail-closed V98-only funding ledger completeness audit. No PnL claims."""
import argparse
import csv
import json
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
HOUR = 3600000
START = 1672531200000  # 2023-01-01 UTC; Dec-2022 is warmup only
END = 1767225600000    # 2026-01-01 UTC, exclusive

def audit(positions, funding, start=START, end=END):
    if start % HOUR or end % HOUR or not START <= start < end <= END:
        raise ValueError("INVALID_TRAINING_WINDOW")
    observed = set()
    for row in positions:
        asset = row["asset"]
        t = int(row["hour_open_ms"])
        if asset not in ASSETS or not start <= t < end or t % HOUR:
            raise ValueError("POSITION_OUTSIDE_TRAINING")
        key = (asset, t)
        if key in observed:
            raise ValueError("DUPLICATE_POSITION_HOUR")
        observed.add(key)
    expected = len(ASSETS) * ((end-start)//HOUR)
    if len(observed) != expected:
        raise ValueError(f"INCOMPLETE_POSITION_PANEL:{len(observed)}/{expected}")
    event_count = 0
    for asset in ASSETS:
        if asset not in funding:
            raise ValueError("MISSING_FUNDING_ASSET")
        for t in funding[asset]:
            if start <= t < end:
                if (asset, t) not in observed:
                    raise ValueError("MISSING_SETTLEMENT_INVENTORY")
                event_count += 1
    if not event_count:
        raise ValueError("NO_NATIVE_FUNDING_EVENTS")
    return {"status": "PASS_FULL_INVENTORY_COVERAGE_NOT_PNL", "position_hours": expected,
            "native_events": event_count, "holdout_accessed": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--positions", type=Path, required=True)
    p.add_argument("--funding-root", type=Path, required=True)
    p.add_argument("--start-ms", type=int, default=START)
    p.add_argument("--end-ms", type=int, default=END)
    a = p.parse_args()
    if any("v98_independent" not in x.absolute().parts for x in (a.positions, a.funding_root)):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    from phase243_native_funding_cashflow import load_funding
    funding = {asset: load_funding(a.funding_root / f"{asset}_native_funding.csv")
               for asset in ASSETS}
    with a.positions.open(newline="") as f:
        positions = csv.DictReader(f)
        result = audit(positions, funding, a.start_ms, a.end_ms)
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
