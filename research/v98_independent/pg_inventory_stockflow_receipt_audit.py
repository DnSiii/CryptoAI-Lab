#!/usr/bin/env python3
"""Independent V98 PG frozen-receipt arithmetic and preregistered gate replay.
No import of PG signals, execution engine or other strategies.
"""
import copy
import json
import math
import sys
from pathlib import Path

BOOKS = {"PG_full", "PG_core_only", "PG_minus_opportunity", "PG_minus_RV", "PG_minus_stress"}
TIERS = ("base", "severe", "supersevere")
ORDERS = ("carried_before_fill", "new_after_fill")
SLOTS = (
    ("Opportunity", "PG_minus_opportunity"),
    ("Relative_Value", "PG_minus_RV"),
    ("Stress_Recovery", "PG_minus_stress"),
)


def audit(receipt):
    assert receipt["architecture"] == "PG"
    assert receipt["2025_exposed_training_only"] is True
    assert receipt["exact_event_mark_attested"] is False
    for k in ("2026_plus_accessed", "holdout_accessed",
              "external_benchmarks_accessed", "paper_or_live_authorized"):
        assert receipt[k] is False
    assert receipt["weekly_decisions"] == 157
    assert receipt["oi_eligible_decisions"] == 143
    assert receipt["source"]["events"] == 13524
    oi = receipt["oi_source"]
    assert oi["verified_hourly_asset_rows"] == 106920
    assert oi["quarantined_hourly_asset_rows"] == 1272
    assert oi["eligible_168h_decisions"] == 143
    assert oi["blocked_168h_decisions"] == 14
    assert receipt["independent_decision_oracle"]["mismatches"] == 0
    accounting = receipt["independent_accounting"]
    fills = receipt["independent_fills"]
    assert accounting is not None and accounting["cash_identity_mismatches"] == 0
    assert accounting["hours_reconciled"] == 26303
    assert fills is not None and fills["independent_fee_slippage_funding_mismatches"] == 0
    assert fills["hours"] == 26303
    rows = receipt["cells"]
    assert len(rows) == 30
    index = {(r["tier"], r["order"], r["book"]): r for r in rows}
    assert len(index) == 30
    assert set(index) == {(tier, order, book) for tier in TIERS
                          for order in ORDERS for book in BOOKS}
    errors = 0
    max_error = 0.
    failures = []
    marginals = {}
    for tier in TIERS:
        for order in ORDERS:
            group = {book: index[(tier, order, book)] for book in BOOKS}
            for row in group.values():
                if row["passed"]:
                    equity = float(row["final_equity"])
                    assert equity > 0 and math.isfinite(equity)
                    reconstructed_growth = math.log(equity / 10000.)
                    reconstructed_cagr = (equity / 10000.)**(365.25/1096.)-1
                    error = max(abs(reconstructed_growth - row["log_growth"]),
                                abs(reconstructed_cagr - row["cagr"]))
                    max_error = max(max_error, error)
                    if error > 1e-10:
                        errors += 1
                    assert all(math.isfinite(v) for v in row["year_returns"].values())
            label = tier + "/" + order
            if not all(row["passed"] for row in group.values()):
                failures.append(label + ":physical")
                continue
            full = group["PG_full"]
            marginals[label] = {
                slot: full["log_growth"] - group[book]["log_growth"]
                for slot, book in SLOTS
            }
            if tier not in ("base", "severe"):
                continue
            if full["cagr"] <= (0.80 if tier == "base" else 0.60):
                failures.append(label + ":CAGR")
            if full["turnover"] > 1000000:
                failures.append(label + ":turnover")
            if tier == "severe":
                if full["max_dd"] <= -.45:
                    failures.append(label + ":drawdown")
                if any(v <= 0 for v in full["year_returns"].values()):
                    failures.append(label + ":annual")
            for slot, book in SLOTS:
                if marginals[label][slot] <= .02:
                    failures.append(label + ":" + slot + ":marginal")
                for year in ("2023", "2024", "2025"):
                    delta = (math.log1p(full["year_returns"][year]) -
                             math.log1p(group[book]["year_returns"][year]))
                    if delta < -.03:
                        failures.append(label + ":" + slot + ":" + year + ":annual_marginal")
    if accounting is None or accounting["cash_identity_mismatches"]:
        failures.append("independent_hourly_accounting")
    if fills is None or fills["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills_and_funding")
    assert errors == 0, errors
    assert failures == receipt["gate_failures"], {
        "expected": failures, "actual": receipt["gate_failures"]}
    for label, slots in marginals.items():
        for slot, val in slots.items():
            assert abs(val - receipt["marginals"][label][slot]) < 1e-10
    expected_decision = ("REJECT_PG_TRAINING" if failures
                         else "PASS_PROVISIONAL_PG_TRAINING_NOT_VALIDATED")
    assert receipt["decision"] == expected_decision
    return {
        "decision": "PASS_INDEPENDENT_PG_RECEIPT_RECONCILIATION_NOT_ENGINE",
        "cells": len(rows),
        "arithmetic_checks": 2 * sum(r["passed"] for r in rows),
        "gate_failures_rederived": len(failures),
        "max_arithmetic_error": max_error,
        "engine_decision": receipt["decision"],
        "training_only": True,
        "exact_tick_mark_attested": False,
    }


def tamper_checks(receipt):
    assert audit(receipt)["decision"].startswith("PASS_INDEPENDENT")
    cases = 0
    mutations = (
        lambda x: x["cells"][0].__setitem__("cagr", x["cells"][0].get("cagr", 0) + .05),
        lambda x: x["gate_failures"].append("fake_gate"),
        lambda x: x["oi_source"].__setitem__("eligible_168h_decisions", 157),
        lambda x: x.__setitem__("exact_event_mark_attested", True),
    )
    for mutate in mutations:
        bad = copy.deepcopy(receipt)
        mutate(bad)
        try:
            audit(bad)
        except (AssertionError, KeyError, ValueError):
            cases += 1
        else:
            raise AssertionError("PG_INDEPENDENT_AUDIT_TAMPER_ACCEPTED")
    return cases


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("pg_full_training_result.json")
    receipt = json.loads(path.read_text())
    out = audit(receipt)
    out["synthetic_receipt_tamper_cases_rejected"] = tamper_checks(receipt)
    print(json.dumps(out, sort_keys=True))
