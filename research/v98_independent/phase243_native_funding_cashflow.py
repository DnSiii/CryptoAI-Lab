#!/usr/bin/env python3
"""V98-only causal native-funding cashflow ledger; no trading signal or PnL claim.

Position at the start of the settlement hour is the only eligible exposure.
Positive funding rate: long pays, short receives. USD-M linear contract.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
HOUR_MS = 3600000

def load_funding(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    events = {}
    previous = None
    for row in rows:
        t = int(row["funding_time_ms"])
        r = float(row["funding_rate"])
        if (not math.isfinite(r) or abs(r) > 1 or t % HOUR_MS
                or (previous is not None and (t <= previous or t - previous > 24 * HOUR_MS))):
            raise ValueError("INVALID_NATIVE_FUNDING_EVENT")
        events[t] = r
        previous = t
    if not events:
        raise ValueError("EMPTY_NATIVE_FUNDING")
    return events

def settle(positions, funding):
    """positions: rows with asset, hour_open_ms, signed_notional_usd_before_hour.
    This ledger does not infer prices, rebalance, or fabricate missing inventory.
    """
    output = []
    seen = set()
    for row in positions:
        asset = row["asset"]
        t = int(row["hour_open_ms"])
        n = float(row["signed_notional_usd_before_hour"])
        if asset not in ASSETS or not math.isfinite(n) or t % HOUR_MS:
            raise ValueError("INVALID_POSITION")
        key = (asset, t)
        if key in seen:
            raise ValueError("DUPLICATE_POSITION_HOUR")
        seen.add(key)
        # Event at hour boundary t settles exposure held BEFORE that boundary.
        rate = funding[asset].get(t)
        cash = -n * rate if rate is not None else 0.0
        output.append({"asset": asset, "hour_open_ms": t,
                       "signed_notional_usd_before_hour": n,
                       "funding_rate": rate, "funding_cashflow_usd": cash})
    return output

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--funding-root", type=Path, required=True)
    p.add_argument("--positions", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    paths = [a.funding_root, a.positions, a.output]
    if any("v98_independent" not in x.absolute().parts for x in paths):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    manifest = json.loads((a.funding_root / "funding_manifest.json").read_text())
    if (manifest.get("mode") != "V98_NATIVE_FUNDING_CANONICAL_SOURCE_ONLY"
            or manifest.get("holdout_accessed") is not False
            or set(manifest.get("assets", {})) != set(ASSETS)):
        raise ValueError("UNTRUSTED_FUNDING_MANIFEST")
    funding = {}
    for asset in ASSETS:
        path = a.funding_root / f"{asset}_native_funding.csv"
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["assets"][asset]["sha256"]:
            raise ValueError("FUNDING_CANONICAL_HASH_MISMATCH")
        funding[asset] = load_funding(path)
    with a.positions.open(newline="") as f:
        positions = list(csv.DictReader(f))
    ledger = settle(positions, funding)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("asset", "hour_open_ms",
            "signed_notional_usd_before_hour", "funding_rate", "funding_cashflow_usd"))
        writer.writeheader()
        writer.writerows(ledger)
    print(json.dumps({"rows": len(ledger), "cashflow_usd": sum(x["funding_cashflow_usd"] for x in ledger),
                      "status": "FUNDING_ATTRIBUTION_ONLY_NOT_STRATEGY_VALIDATION",
                      "holdout_accessed": False}))

if __name__ == "__main__":
    main()
