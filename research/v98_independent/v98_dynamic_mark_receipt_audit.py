#!/usr/bin/env python3
"""V98 dynamic mark sensitivity receipt-only arithmetic oracle.
Independent of strategy, physical planner, funding implementation and NumPy.
This cannot attest historical source origin, exchange marks, fills or alpha.
"""
import copy
import json
import math
import sys

PAIRS = {(tier, order) for tier in ("base", "severe", "supersevere")
         for order in ("carried_before_fill", "new_after_fill")}
YEARS = {"2023", "2024", "2025"}
NAV0 = 10000.0
EXPONENT = 365.25 / 1096.0


def _check(ok, label):
    if not ok:
        raise ValueError("MARK_RECEIPT_" + label)


def verify(s):
    _check(s.get("decision") == "PASS_DYNAMIC_MARK_SENSITIVITY_NOT_ENGINE", "DECISION")
    _check(s.get("frozen_rejected_fixture") == "PU_NOT_REOPENED", "FIXTURE")
    for key in ("exact_exchange_marks_attested", "account_specific_execution_attested",
                "candidate_promoted", "2026_plus_accessed", "holdout_accessed",
                "benchmarks_accessed", "paper_live_authorized"):
        _check(s.get(key) is False, "ISOLATION_" + key)
    _check(s.get("2025_exposed_training_only") is True, "EXPOSED_2025")
    cells = s.get("cells", [])
    _check(len(cells) == 6, "SIX_PAIRS")
    _check({(x["tier"], x["funding_order"]) for x in cells} == PAIRS,
           "PAIR_UNIQUENESS")
    identities = 0
    for x in cells:
        audit = x["audit"]
        _check(audit["ledger_hours"] == 26303 and audit["funding_hours"] == 3287
               and audit["funding_asset_events"] == 13148, "EVENT_COVERAGE")
        _check(audit["independent_funding_fee_mismatches"] == 0 and
               audit["independent_cash_identity_mismatches"] == 0, "CASH_OR_FEE")
        _check(audit["max_funding_fee_error_usd"] < 1e-5 and
               audit["max_cash_identity_error_usd"] < 1e-5, "AUDIT_ERROR")
        worst = x["baseline_worst"]
        favorable = x["favorable_counterfactual"]
        for book in (worst, favorable):
            nav = book["final_equity"]
            _check(math.isfinite(nav) and nav > 0, "NAV")
            _check(math.isfinite(book["cagr"]) and
                   math.isclose(book["cagr"], (nav/NAV0)**EXPONENT-1,
                                rel_tol=1e-10, abs_tol=1e-10), "CAGR_IDENTITY")
            yr = book["year_returns"]
            _check(set(yr) == YEARS and all(math.isfinite(v) and v > -1
                                           for v in yr.values()), "YEAR_GEOMETRY")
            _check(math.isclose(math.prod(1+yr[y] for y in sorted(YEARS)),
                                nav/NAV0, rel_tol=1e-8, abs_tol=1e-8),
                   "YEAR_NAV_IDENTITY")
            _check(math.isfinite(book["turnover"]) and book["turnover"] >= 0 and
                   math.isfinite(book["funding"]), "TURNOVER_OR_FUNDING")
            identities += 1
        _check(math.isclose(x["paired_terminal_nav_delta_usd"],
                            favorable["final_equity"]-worst["final_equity"],
                            rel_tol=1e-9, abs_tol=1e-7), "DELTA_NAV")
        _check(math.isclose(x["paired_cagr_delta_not_a_bound"],
                            favorable["cagr"]-worst["cagr"],
                            rel_tol=1e-9, abs_tol=1e-10), "DELTA_CAGR")
        _check(math.isclose(x["paired_turnover_delta_usd"],
                            favorable["turnover"]-worst["turnover"],
                            rel_tol=1e-9, abs_tol=1e-6), "DELTA_TURNOVER")
    return {"decision": "PASS_RECEIPT_ARITHMETIC_NOT_SOURCE_OR_ENGINE",
            "physical_pairs": 6, "annual_nav_identities": identities,
            "source_origin_attested": False, "candidate_promoted": False}


def verify_with_tamper(s):
    result = verify(s)
    def bad_nav(z):
        z["cells"][0]["paired_terminal_nav_delta_usd"] += 1
    def bad_event(z):
        z["cells"][0]["audit"]["funding_asset_events"] = 1
    def bad_cagr(z):
        z["cells"][0]["favorable_counterfactual"]["cagr"] += .01
    def bad_promotion(z):
        z["candidate_promoted"] = True
    controls = (("delta_nav", bad_nav), ("event_count", bad_event),
                ("cagr", bad_cagr), ("promotion", bad_promotion))
    detected = []
    for label, mutate in controls:
        changed = copy.deepcopy(s)
        mutate(changed)
        try:
            verify(changed)
        except ValueError:
            detected.append(label)
        else:
            raise ValueError("MARK_RECEIPT_TAMPER_UNDETECTED_" + label)
    result["tamper_controls_detected"] = detected
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python v98_dynamic_mark_receipt_audit.py receipt.json")
    full = json.load(open(sys.argv[1], encoding="utf-8"))
    sensitivity = full.get("dynamic_mark_sensitivity", full)
    print(json.dumps(verify_with_tamper(sensitivity), sort_keys=True))
