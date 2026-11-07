#!/usr/bin/env python3
"""Strict V98-only historical accounting entrypoint; never selects alpha or accesses holdout."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from research.v98_independent.phase243_economic_accounting import account, write_ledger
from research.v98_independent.phase243_native_funding_cashflow import ASSETS, HOUR_MS, load_funding

REQUIRED = {"asset","hour_open_ms","decision_time_ms","pre_trade_notional_usd","target_notional_usd","close_price","fill_price"}

def verify_native_prices(rows, price_root, price_manifest_path):
    """Bind executed fills and closes to authenticated Clean-4 Binance USD-M bars."""
    manifest = json.loads(price_manifest_path.read_text())
    if (manifest.get("mode") != "CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA"
            or manifest.get("holdout_accessed") is not False
            or set(manifest.get("prices", {})) != set(ASSETS)):
        raise ValueError("UNTRUSTED_PRICE_MANIFEST")
    expected = {}
    asset_hours = {}
    for asset in ASSETS:
        path = price_root / f"{asset}_1h.csv"
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["prices"][asset]["canonical_sha256"]:
            raise ValueError("PRICE_CANONICAL_HASH_MISMATCH")
        hours = []
        with path.open(newline="") as f:
            for bar in csv.DictReader(f):
                stamp = bar["open_time"]
                from datetime import datetime
                parsed = datetime.fromisoformat(stamp.replace("Z","+00:00"))
                from datetime import timezone, timedelta
                if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
                    raise ValueError("NON_UTC_AUTHENTICATED_PRICE_TIMESTAMP")
                t = int(parsed.timestamp()*1000)
                if t >= 1767225600000:
                    raise ValueError("PRICE_TRAINING_BOUNDARY")
                if t % HOUR_MS or (asset,t) in expected:
                    raise ValueError("DUPLICATE_OR_UNALIGNED_AUTHENTICATED_PRICE_HOUR")
                if hours and t != hours[-1] + HOUR_MS:
                    raise ValueError("NONCONTIGUOUS_AUTHENTICATED_PRICE_HOURS")
                op, cl = float(bar["open"]), float(bar["close"])
                import math
                if not all(math.isfinite(v) and v > 0 for v in (op,cl)):
                    raise ValueError("INVALID_AUTHENTICATED_PRICE")
                hours.append(t)
                expected[(asset,t)] = (op,cl)
        asset_hours[asset] = hours
    if not asset_hours[ASSETS[0]] or any(asset_hours[a] != asset_hours[ASSETS[0]] for a in ASSETS[1:]):
        raise ValueError("MISALIGNED_AUTHENTICATED_PRICE_ASSETS")
    for row in rows:
        key = (row["asset"],int(row["hour_open_ms"]))
        if key not in expected:
            raise ValueError("MISSING_AUTHENTICATED_PRICE_HOUR")
        op,cl = expected[key]
        # Execution uses native open; slippage is charged separately in account().
        if abs(float(row["fill_price"])-op)>1e-8*max(1,op) or abs(float(row["close_price"])-cl)>1e-8*max(1,cl):
            raise ValueError("EXECUTION_PRICE_SOURCE_MISMATCH")


def verify_full_training_coverage(hours):
    """A claimed full-history receipt must span all 2023-2025 hourly bars."""
    from datetime import datetime, timezone
    start = int(datetime(2023,1,1,tzinfo=timezone.utc).timestamp()*1000)
    end = int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
    warmup = int(datetime(2022,12,1,tzinfo=timezone.utc).timestamp()*1000)
    if not hours or hours[0] not in (start,warmup) or hours[-1] != end-HOUR_MS:
        raise ValueError("INCOMPLETE_2023_2025_TRAINING_COVERAGE")
    if len(hours) != (end-hours[0])//HOUR_MS:
        raise ValueError("INCOMPLETE_2023_2025_TRAINING_COVERAGE")

def run(positions_path, funding_root, output_path, *, initial_equity_usd, taker_fee_bps, slippage_bps, cost_multiplier, max_gross_leverage, price_root=None, price_manifest_path=None):
    for p in (positions_path, funding_root, output_path):
        if "v98_independent" not in Path(p).absolute().parts:
            raise ValueError("V98_NAMESPACE_REQUIRED")
    manifest_path = funding_root / "funding_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if (manifest.get("mode") != "V98_NATIVE_FUNDING_CANONICAL_SOURCE_ONLY"
            or manifest.get("holdout_accessed") is not False
            or set(manifest.get("assets",{})) != set(ASSETS)):
        raise ValueError("UNTRUSTED_FUNDING_MANIFEST")
    funding = {}
    for asset in ASSETS:
        path = funding_root / f"{asset}_native_funding.csv"
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["assets"][asset]["sha256"]:
            raise ValueError("FUNDING_CANONICAL_HASH_MISMATCH")
        funding[asset] = load_funding(path)
    with positions_path.open(newline="") as f:
        reader = csv.DictReader(f)
        if not REQUIRED.issubset(reader.fieldnames or ()):
            raise ValueError("MISSING_CAUSAL_EXECUTION_COLUMNS")
        rows = list(reader)
    if not rows:
        raise ValueError("EMPTY_POSITION_TIMELINE")
    # Reject duplicated asset-hour positions even in short diagnostic runs: duplicate
    # rows would double count exposures and funding without any distinct market hour.
    keys_all = [(row["asset"], int(row["hour_open_ms"])) for row in rows]
    if any(asset not in ASSETS for asset, _ in keys_all):
        raise ValueError("UNAUTHORIZED_CLEAN4_ASSET")
    if len(set(keys_all)) != len(keys_all):
        raise ValueError("DUPLICATE_POSITION_ASSET_HOUR")
    # A full-history economic receipt must cover each hour for every Clean-4 asset.
    # Prevent duplicated assets/hours from satisfying the 8760*4 length threshold.
    if len(rows) >= 8760 * len(ASSETS):
        from collections import Counter
        counts = Counter(int(row["hour_open_ms"]) for row in rows)
        if any(n != len(ASSETS) for n in counts.values()):
            raise ValueError("INCOMPLETE_HISTORICAL_ASSET_GRID")
        keys = [(row["asset"], int(row["hour_open_ms"])) for row in rows]
        if len(set(keys)) != len(keys) or set(row["asset"] for row in rows) != set(ASSETS):
            raise ValueError("DUPLICATE_OR_MISSING_HISTORICAL_ASSET")
        hours = sorted(counts)
        verify_full_training_coverage(hours)
        if any(b-a != HOUR_MS for a,b in zip(hours,hours[1:])):
            raise ValueError("NONCONTIGUOUS_HISTORICAL_POSITION_HOURS")
    for row in rows:
        t = int(row["hour_open_ms"])
        d = int(row["decision_time_ms"])
        if t < 0 or t >= 1767225600000 or d > t-HOUR_MS:
            raise ValueError("NONCAUSAL_DECISION_OR_TRAINING_BOUNDARY")
    if (price_root is None) != (price_manifest_path is None):
        raise ValueError("INCOMPLETE_PRICE_PROVENANCE")
    if len(rows) >= 8760 * len(ASSETS) and price_root is None:
        raise ValueError("HISTORICAL_RUN_REQUIRES_AUTHENTICATED_PRICES")
    if price_root is not None:
        for p in (price_root,price_manifest_path):
            if "v98_independent" not in Path(p).absolute().parts:
                raise ValueError("V98_NAMESPACE_REQUIRED")
        verify_native_prices(rows,price_root,price_manifest_path)
    ledger = account(rows, funding, initial_equity_usd=initial_equity_usd,
                     taker_fee_bps=taker_fee_bps, slippage_bps=slippage_bps,
                     cost_multiplier=cost_multiplier, max_gross_leverage=max_gross_leverage)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    write_ledger(output_path, ledger)
    receipt = {"status":"ACCOUNTING_ONLY_NOT_VALIDATED_ENGINE",
               "holdout_accessed":False, "hours":len(ledger),
               "initial_equity_usd":initial_equity_usd,
               "ending_equity_usd":ledger[-1]["ending_equity_usd"],
               "total_execution_cost_usd":sum(x["execution_cost_usd"] for x in ledger),
               "total_funding_cashflow_usd":sum(x["funding_cashflow_usd"] for x in ledger),
               "positions_sha256":hashlib.sha256(positions_path.read_bytes()).hexdigest(),
               "funding_manifest_sha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
               "price_manifest_sha256":hashlib.sha256(price_manifest_path.read_bytes()).hexdigest() if price_manifest_path is not None else None,
               "authenticated_prices":price_manifest_path is not None,
               "ledger_sha256":hashlib.sha256(output_path.read_bytes()).hexdigest()}
    output_path.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--positions",type=Path,required=True)
    p.add_argument("--funding-root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--initial-equity-usd",type=float,required=True)
    p.add_argument("--taker-fee-bps",type=float,required=True)
    p.add_argument("--slippage-bps",type=float,required=True)
    p.add_argument("--cost-multiplier",type=float,default=1)
    p.add_argument("--max-gross-leverage",type=float,default=2)
    p.add_argument("--price-root",type=Path)
    p.add_argument("--price-manifest",type=Path)
    a=p.parse_args()
    print(json.dumps(run(a.positions,a.funding_root,a.output,initial_equity_usd=a.initial_equity_usd,
        taker_fee_bps=a.taker_fee_bps,slippage_bps=a.slippage_bps,cost_multiplier=a.cost_multiplier,
        max_gross_leverage=a.max_gross_leverage,price_root=a.price_root,price_manifest_path=a.price_manifest),sort_keys=True))
if __name__=="__main__": main()
