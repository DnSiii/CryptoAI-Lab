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

def run(positions_path, funding_root, output_path, *, initial_equity_usd, taker_fee_bps, slippage_bps, cost_multiplier, max_gross_leverage):
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
    for row in rows:
        t = int(row["hour_open_ms"])
        d = int(row["decision_time_ms"])
        if t < 0 or t >= 1767225600000 or d > t-HOUR_MS:
            raise ValueError("NONCAUSAL_DECISION_OR_TRAINING_BOUNDARY")
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
    a=p.parse_args()
    print(json.dumps(run(a.positions,a.funding_root,a.output,initial_equity_usd=a.initial_equity_usd,
        taker_fee_bps=a.taker_fee_bps,slippage_bps=a.slippage_bps,cost_multiplier=a.cost_multiplier,
        max_gross_leverage=a.max_gross_leverage),sort_keys=True))
if __name__=="__main__": main()
