#!/usr/bin/env python3
"""V98 Clean-4 fixed-cost stress gate; no alpha selection and no holdout reads.

Runs the identical immutable position timeline under three preregistered
execution-cost multipliers. A failure in ANY scenario is a failed gate.
No scenario may change signals, notional, or execution timestamps.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from research.v98_independent.phase243_strict_historical_accounting_run import run

SCENARIOS = (("normal", 1.0), ("severe", 2.0), ("supersevere", 3.0))

def stress(positions, funding_root, output_root, *, initial_equity_usd,
           taker_fee_bps, slippage_bps, max_gross_leverage,
           minimum_hours=24 * 365):
    if minimum_hours < 1:
        raise ValueError("INVALID_MINIMUM_HISTORY")
    original = hashlib.sha256(positions.read_bytes()).hexdigest()
    receipts = {}
    for label, multiplier in SCENARIOS:
        path = output_root / f"v98_independent_{label}_ledger.csv"
        result = run(positions, funding_root, path,
                     initial_equity_usd=initial_equity_usd,
                     taker_fee_bps=taker_fee_bps,
                     slippage_bps=slippage_bps,
                     cost_multiplier=multiplier,
                     max_gross_leverage=max_gross_leverage)
        if result["positions_sha256"] != original or result["hours"] < minimum_hours:
            raise ValueError("INCOMPLETE_OR_MUTATED_HISTORICAL_TIMELINE")
        receipts[label] = result
    ending = [receipts[label]["ending_equity_usd"] for label, _ in SCENARIOS]
    if not all(math.isfinite(x) and x > 0 for x in ending):
        raise ValueError("INVALID_STRESS_EQUITY")
    if not (ending[0] >= ending[1] >= ending[2]):
        raise ValueError("COST_STRESS_MONOTONICITY_BREACH")
    summary = {
        "status": "COST_STRESS_ACCOUNTING_ONLY_NOT_ENGINE_VALIDATION",
        "holdout_accessed": False,
        "positions_sha256": original,
        "hours": receipts["normal"]["hours"],
        "scenarios": receipts,
        "cost_stress_monotonic": True,
    }
    (output_root / "v98_independent_cost_stress_receipt.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--positions", required=True, type=Path)
    parser.add_argument("--funding-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--initial-equity-usd", required=True, type=float)
    parser.add_argument("--taker-fee-bps", required=True, type=float)
    parser.add_argument("--slippage-bps", required=True, type=float)
    parser.add_argument("--max-gross-leverage", type=float, default=2.0)
    parser.add_argument("--minimum-hours", type=int, default=24 * 365)
    args = parser.parse_args()
    print(json.dumps(stress(args.positions, args.funding_root, args.output_root,
        initial_equity_usd=args.initial_equity_usd,
        taker_fee_bps=args.taker_fee_bps, slippage_bps=args.slippage_bps,
        max_gross_leverage=args.max_gross_leverage,
        minimum_hours=args.minimum_hours), sort_keys=True))
if __name__ == "__main__":
    main()
