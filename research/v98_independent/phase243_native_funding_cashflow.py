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
        raw_t = int(row["funding_time_ms"])
        # Binance native settlement timestamps can carry sub-second milliseconds.
        # Accept ONLY timestamps within the first 999 ms after an exact UTC hour;
        # retain original CSV + SHA256 provenance, and reject second-level drift.
        # This is timestamp representation normalization, never rate interpolation.
        offset_ms = raw_t % HOUR_MS
        t = raw_t - offset_ms if offset_ms < 1000 else raw_t
        r = float(row["funding_rate"])
        if (not math.isfinite(r) or abs(r) > 1 or t % HOUR_MS
                or t in events
                or (previous is not None and (t <= previous or t - previous > 24 * HOUR_MS))):
            reason = ("nonfinite_rate" if not math.isfinite(r) else
                      "rate_out_of_bounds" if abs(r) > 1 else
                      "non_hour_boundary" if t % HOUR_MS else
                      "duplicate_normalized_settlement" if t in events else
                      "nonmonotonic_timestamp" if previous is not None and t <= previous else
                      "gap_over_24_hours")
            raise ValueError(
                f"INVALID_NATIVE_FUNDING_EVENT file={Path(path).name} "
                f"row={len(events)+2} raw_time_ms={raw_t} normalized_time_ms={t} previous_ms={previous} "
                f"gap_hours={(t-previous)/HOUR_MS if previous is not None else None} "
                f"rate={r} reason={reason}")
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


def validate_complete_inventory(positions, funding):
    """Fail closed before cashflow: every Clean-4 hour and settlement must have inventory."""
    if not positions:
        raise ValueError("EMPTY_POSITION_TIMELINE")
    by_asset = {asset: set() for asset in ASSETS}
    for row in positions:
        asset = row["asset"]
        t = int(row["hour_open_ms"])
        if asset not in by_asset or t % HOUR_MS or t < 0:
            raise ValueError("INVALID_POSITION")
        if t in by_asset[asset]:
            raise ValueError("DUPLICATE_POSITION_HOUR")
        by_asset[asset].add(t)
    starts = {min(v) for v in by_asset.values() if v}
    ends = {max(v) for v in by_asset.values() if v}
    if len(starts) != 1 or len(ends) != 1 or any(not v for v in by_asset.values()):
        raise ValueError("INCOMPLETE_CLEAN4_INVENTORY")
    start, end = starts.pop(), ends.pop()
    if end >= 1767225600000:  # 2026-01-01 UTC, exclusive
        raise ValueError("TRAINING_BOUNDARY_VIOLATION")
    expected = (end - start) // HOUR_MS + 1
    for asset in ASSETS:
        if len(by_asset[asset]) != expected:
            raise ValueError("MISSING_POSITION_HOUR")
        # Never silently discard a native settlement outside the position window.
        # A truncated inventory would otherwise omit real funding cashflows.
        if any(t < start or t > end for t in funding[asset]):
            raise ValueError("SETTLEMENT_OUTSIDE_INVENTORY")
        if any(t not in by_asset[asset] for t in funding[asset]):
            raise ValueError("MISSING_SETTLEMENT_INVENTORY")
    return {"start_ms": start, "end_ms": end, "hours_per_asset": expected}

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
    coverage = validate_complete_inventory(positions, funding)
    ledger = settle(positions, funding)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("asset", "hour_open_ms",
            "signed_notional_usd_before_hour", "funding_rate", "funding_cashflow_usd"))
        writer.writeheader()
        writer.writerows(ledger)
    print(json.dumps({"rows": len(ledger), "inventory_coverage": coverage, "cashflow_usd": sum(x["funding_cashflow_usd"] for x in ledger),
                      "status": "FUNDING_ATTRIBUTION_ONLY_NOT_STRATEGY_VALIDATION",
                      "holdout_accessed": False}))

if __name__ == "__main__":
    main()
