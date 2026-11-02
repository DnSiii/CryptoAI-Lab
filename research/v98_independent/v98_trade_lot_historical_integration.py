#!/usr/bin/env python3
"""Historical trade-level accounting integration using permanently rejected PU as fixture.

PU is never re-selected, changed, benchmarked or promoted by this diagnostic.
The historical sample is exposed TRAINING; markPrice is not exact; no live/paper.
"""
import json
import math
import os
from pathlib import Path

from ot_breadth_dispersion import COSTS, ORDERS, HOURS, WARMUP, independent_accounting, physical, source_gate
from ot_independent_oracle import independent_fills
from pu_expected_net_wealth_composed import signals, target_books
from v98_trade_lot_metrics import roundtrip_metrics, synthetic_tests
from v98_dynamic_mark_sensitivity import run_dynamic_sensitivity
from v98_2025_full_training_source_bridge import load

EXPECTED_HOURS = HOURS - WARMUP - 1
FROZEN_PU_POLICY = "pu_expected_net_wealth_prereg_20261101.md"
PRE_RUN_CONTRACT = "v98_trade_lot_historical_integration_prereg_20261101.md"


def run_historical(d):
    source = source_gate(d)
    synthetic = synthetic_tests()
    if synthetic["decision"] != "PASS_TRADE_LOT_ACCOUNTING_ONLY_NOT_ENGINE":
        raise ValueError("TRADE_SYNTHETIC_PRECHECK")
    decision = signals(d)
    books = target_books(decision)
    if len(decision) != 157 or len(books["PU_full"]) != 157:
        raise ValueError("TRADE_FROZEN_PU_DECISION_CLOCK")
    cells = []
    baseline_physical_rows = []
    for tier, (fee, slip) in COSTS.items():
        for order in ORDERS:
            physical_row, ledger = physical(d, books["PU_full"], "PU_full", tier, order, record=True)
            if not physical_row.get("passed") or len(ledger) != EXPECTED_HOURS:
                raise ValueError("TRADE_HISTORICAL_PHYSICAL_FAILURE_" + tier + "_" + order)
            cash = independent_accounting(d, ledger)
            fills = independent_fills(d, ledger, fee=fee, slip=slip, order=order)
            trade = roundtrip_metrics(d, ledger, fee, slip, order)
            if cash["cash_identity_mismatches"] or fills["independent_fee_slippage_funding_mismatches"]:
                raise ValueError("TRADE_INDEPENDENT_CASH_FILL_FAILURE_" + tier + "_" + order)
            if trade["mismatches"] or trade["decision"] != "PASS_TRADE_LOT_ACCOUNTING_ONLY_NOT_ENGINE":
                raise ValueError("TRADE_LOT_RECONCILIATION_FAILURE_" + tier + "_" + order)
            if not math.isclose(trade["nav_delta"], physical_row["final_equity"] - 10000., rel_tol=1e-9, abs_tol=1e-5):
                raise ValueError("TRADE_PHYSICAL_NAV_DISAGREEMENT_" + tier + "_" + order)
            if trade["closed_net_asset_roundtrips"] <= 0:
                raise ValueError("TRADE_EMPTY_HISTORICAL_EPISODES")
            if trade["closed_wins"] + trade["closed_losses"] > trade["closed_net_asset_roundtrips"]:
                raise ValueError("TRADE_CLASSIFICATION_INVALID")
            baseline_physical_rows.append(physical_row)
            cells.append({
                "tier": tier, "funding_order": order,
                "historical_ledger_hours": len(ledger),
                "physical_passed": True,
                "historical_cagr_not_validated": physical_row["cagr"],
                "historical_max_dd_not_validated": physical_row["max_dd"],
                "cash_reconciliation": cash,
                "fill_reconciliation": fills,
                "net_asset_trade_metrics": trade,
            })
            print("TRADE_HISTORICAL_CELL", tier, order,
                  "closed", trade["closed_net_asset_roundtrips"],
                  "PF", trade["trade_profit_factor"],
                  "payoff", trade["trade_payoff"],
                  "win_rate", trade["trade_win_rate"],
                  "NAV_ERROR", trade["nav_reconciliation_error"], flush=True)
    # Counterfactual source-uncertainty audit, preregistered separately.
    # Rejected PU is not reselected, altered, promoted or benchmarked.
    sensitivity = run_dynamic_sensitivity(d, books, baseline_physical_rows)
    if sensitivity["decision"] != "PASS_DYNAMIC_MARK_SENSITIVITY_NOT_ENGINE":
        raise ValueError("TRADE_DYNAMIC_MARK_SENSITIVITY_INCOMPLETE")
    result = {
        "decision": "PASS_HISTORICAL_TRADE_METRIC_INTEGRATION_ONLY_NOT_ENGINE",
        "historical_sample": "2023-2025_EXPOSED_TRAINING_ONLY",
        "architecture_fixture": "PU_PERMANENTLY_REJECTED_NOT_REOPENED",
        "frozen_policy": FROZEN_PU_POLICY,
        "preregistration": PRE_RUN_CONTRACT,
        "source": source,
        "cells": cells,
        "dynamic_mark_sensitivity": sensitivity,
        "physical_scenarios": len(cells),
        "ledger_hours_per_scenario": EXPECTED_HOURS,
        "exact_funding_mark_attested": False,
        "account_specific_execution_costs_attested": False,
        "future_holdout_accessed": False,
        "external_benchmarks_accessed": False,
        "paper_or_live_authorized": False,
    }
    if len(cells) != 6:
        raise ValueError("TRADE_HISTORICAL_SCENARIO_COUNT")
    json.dumps(result, allow_nan=False)
    return result


def main():
    d = load(os.environ["OLD_ROOT"], os.environ["OLD_ENVELOPE"],
             os.environ["NEW_ROOT"], os.environ["CORRECTED_ROOT"])
    result = run_historical(d)
    dest = Path("v98_trade_lot_historical_integration_result.json")
    dest.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("TRADE_HISTORICAL_INTEGRATION", result["decision"], "six_scenarios", len(result["cells"]), flush=True)
    print("MARK_DYNAMIC_SENSITIVITY", result["dynamic_mark_sensitivity"]["decision"],
          "six_paired_paths", len(result["dynamic_mark_sensitivity"]["cells"]), flush=True)


if __name__ == "__main__":
    main()
