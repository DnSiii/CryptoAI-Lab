#!/usr/bin/env python3
"""V98-only full physical funding-mark sensitivity on PERMANENTLY REJECTED PU.
No alpha selection, future holdout, external benchmark, exact marks, or live/paper.
Precommitted in v98_dynamic_mark_sensitivity_prereg_20261101.md.
"""
import json
import math
from unittest.mock import patch

import numpy as np

import ot_breadth_dispersion as ot

DECISION = "PASS_DYNAMIC_MARK_SENSITIVITY_NOT_ENGINE"
EXPECTED_HOURS = ot.HOURS - ot.WARMUP - 1
ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")


def favorable_funding(old, new, rate, event, lower, upper, order):
    """Favorable, non-executable envelope-side funding cash; no original function."""
    if order not in ot.ORDERS:
        raise ValueError("MARK_SENSITIVITY_ORDER")
    payer = np.asarray(old if order == "carried_before_fill" else new, dtype=float)
    rate = np.asarray(rate, dtype=float)
    event = np.asarray(event, dtype=bool)
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    if any(a.shape != (4,) for a in (payer, rate, event, lower, upper)):
        raise ValueError("MARK_SENSITIVITY_SHAPE")
    if not all(np.isfinite(a).all() for a in (payer, rate, lower[event], upper[event])):
        raise ValueError("MARK_SENSITIVITY_NONFINITE")
    if np.any(lower[event] <= 0) or np.any(upper[event] < lower[event]):
        raise ValueError("MARK_SENSITIVITY_ENVELOPE")
    obligation = payer * rate
    return -math.fsum(
        float(obligation[j]) * float(lower[j] if obligation[j] >= 0 else upper[j])
        for j in range(4) if event[j]
    )


def scalar_oracle_cash(old, new, rate, event, lower, upper, order):
    """Independent Python scalar implementation; never invokes favorable_funding."""
    if order not in ot.ORDERS:
        raise ValueError("MARK_ORACLE_ORDER")
    positions = old if order == "carried_before_fill" else new
    cash = []
    for j in range(4):
        if not bool(event[j]):
            continue
        signed_obligation = float(positions[j]) * float(rate[j])
        mark = float(lower[j]) if signed_obligation >= 0.0 else float(upper[j])
        cash.append(-signed_obligation * mark)
    return math.fsum(cash)


def independent_favorable_audit(d, ledger, fee, slip, order):
    if len(ledger) != EXPECTED_HOURS:
        raise ValueError("MARK_ORACLE_LEDGER_LENGTH")
    previous = np.zeros((4, 4), dtype=float)
    last_nav = 10000.0
    max_error = 0.0
    funding_hours = 0
    funding_asset_events = 0
    fills = 0
    turnover = 0.0
    for offset, item in enumerate(ledger):
        t, before, nav, cash, fees, slippage, virtual, gap = item
        if t != ot.WARMUP + 1 + offset or not math.isfinite(nav) or nav <= 0:
            raise ValueError("MARK_ORACLE_CLOCK_OR_NAV")
        if abs(float(before) - last_nav) > 1e-6:
            raise ValueError("MARK_ORACLE_NAV_CONTINUITY")
        virtual = np.asarray(virtual, dtype=float)
        if virtual.shape != (4, 4) or not np.isfinite(virtual).all():
            raise ValueError("MARK_ORACLE_VIRTUAL_SHAPE")
        px = np.asarray(d["o"][t], dtype=float)
        old = previous.sum(axis=0)
        new = virtual.sum(axis=0)
        delta = new - old
        trade_notional = math.fsum(abs(float(delta[j])) * float(px[j]) for j in range(4))
        turnover += trade_notional
        if trade_notional > 1e-8:
            fills += 1
        if np.any((np.abs(delta) > 1e-12) & (~d["execution_allowed"][t])):
            raise ValueError("MARK_ORACLE_ZERO_VOLUME_FILL")
        expected_fee = trade_notional * fee
        expected_slip = trade_notional * slip
        event = np.asarray(d["event"][t], dtype=bool)
        expected_cash = scalar_oracle_cash(
            old, new, d["rate"][t], event,
            d["mark_lower"][t], d["mark_upper"][t], order
        )
        if np.any(event):
            funding_hours += 1
            funding_asset_events += int(np.sum(event))
        err = max(abs(expected_fee - float(fees)),
                  abs(expected_slip - float(slippage)),
                  abs(expected_cash - float(cash)))
        max_error = max(max_error, err)
        if err > 1e-6:
            raise ValueError("MARK_ORACLE_FUNDING_OR_FEE_MISMATCH")
        previous = virtual
        last_nav = float(nav)
    cash_audit = ot.independent_accounting(d, ledger)
    if cash_audit["cash_identity_mismatches"]:
        raise ValueError("MARK_ORACLE_CASH_IDENTITY")
    return {
        "ledger_hours": len(ledger),
        "funding_hours": funding_hours,
        "funding_asset_events": funding_asset_events,
        "net_fill_hours": fills,
        "net_turnover_usd": turnover,
        "independent_funding_fee_mismatches": 0,
        "independent_cash_identity_mismatches": 0,
        "max_funding_fee_error_usd": max_error,
        "max_cash_identity_error_usd": cash_audit["max_absolute_cash_error"],
    }


def synthetic_controls():
    """Explicitly exercised categories; no counters for unexecuted assertions."""
    old = np.array([2.0, -1.0, 3.0, -4.0])
    new = np.array([-2.0, 1.0, -3.0, 4.0])
    rate = np.array([0.001, -0.002, -0.003, 0.004])
    event = np.ones(4, dtype=bool)
    lower = np.array([100., 200., 300., 400.])
    upper = lower * 1.1
    controls = set()
    for order in ot.ORDERS:
        good = favorable_funding(old, new, rate, event, lower, upper, order)
        independent = scalar_oracle_cash(old, new, rate, event, lower, upper, order)
        worst = ot.worst_funding(old, new, rate, event, lower, upper, order)
        if abs(good - independent) > 1e-12 or good < worst - 1e-12:
            raise ValueError("MARK_SYNTHETIC_SIGN_OR_ORACLE")
        other = "new_after_fill" if order == "carried_before_fill" else "carried_before_fill"
        if abs(good - scalar_oracle_cash(old, new, rate, event, lower, upper, other)) < 1e-8:
            raise ValueError("MARK_SYNTHETIC_ORDER_TAMPER_UNDETECTED")
        controls.add("wrong_funding_order")
        if abs((good + 1.) - independent) <= 1e-8:
            raise ValueError("MARK_SYNTHETIC_CASH_TAMPER_UNDETECTED")
        controls.add("cash_tamper")
    if favorable_funding(old, new, np.zeros(4), event, lower, upper, ot.ORDERS[0]) != 0:
        raise ValueError("MARK_SYNTHETIC_ZERO_RATE")
    controls.add("zero_rate")
    if favorable_funding(old, new, rate, np.zeros(4, bool), lower, upper, ot.ORDERS[0]) != 0:
        raise ValueError("MARK_SYNTHETIC_NO_EVENT")
    controls.add("no_event")
    # A receiving short on positive funding must use upper, and altered upper
    # must change cash; compare to the independent original unmodified oracle.
    one_old = np.array([-1., 0., 0., 0.])
    one_rate = np.array([.001, 0., 0., 0.])
    original_cash = scalar_oracle_cash(one_old, one_old, one_rate, event,
                                       lower, upper, ot.ORDERS[0])
    altered = upper.copy()
    altered[0] *= 1.5
    changed = favorable_funding(one_old, one_old, one_rate, event,
                                 lower, altered, ot.ORDERS[0])
    if not changed > original_cash or abs(changed - original_cash) < 1e-8:
        raise ValueError("MARK_SYNTHETIC_MARK_TAMPER_UNDETECTED")
    controls.add("mark_tamper")
    try:
        favorable_funding(old, new, rate, event, upper, lower, ot.ORDERS[0])
    except ValueError:
        controls.add("inverted_interval")
    else:
        raise ValueError("MARK_SYNTHETIC_INVERTED_INTERVAL_ACCEPTED")
    if controls != {"wrong_funding_order", "cash_tamper", "zero_rate",
                    "no_event", "mark_tamper", "inverted_interval"}:
        raise ValueError("MARK_SYNTHETIC_CONTROL_COVERAGE")
    return {"signed_orders": 2, "negative_control_categories": sorted(controls),
            "decision": "PASS_MARK_SENSITIVITY_SYNTHETIC_NOT_PNL"}


def run_dynamic_sensitivity(d, pu_books, baseline_rows):
    ot.source_gate(d)
    tests = synthetic_controls()
    if len(pu_books["PU_full"]) != 157:
        raise ValueError("MARK_SENSITIVITY_FROZEN_PU_CLOCK")
    baseline = {(r["tier"], r["order"]): r for r in baseline_rows}
    if len(baseline) != 6 or set(baseline) != {
        (tier, order) for tier in ot.COSTS for order in ot.ORDERS
    } or any(not r["passed"] for r in baseline_rows):
        raise ValueError("MARK_SENSITIVITY_BASELINE_PHYSICAL")
    original = ot.worst_funding
    cells = []
    for tier, (fee, slip) in ot.COSTS.items():
        for order in ot.ORDERS:
            with patch.object(ot, "worst_funding", favorable_funding):
                favorable, ledger = ot.physical(
                    d, pu_books["PU_full"], "PU_PERMANENTLY_REJECTED", tier,
                    order, record=True
                )
            if ot.worst_funding is not original:
                raise ValueError("MARK_SENSITIVITY_GLOBAL_FUNCTION_NOT_RESTORED")
            if not favorable.get("passed") or len(ledger) != EXPECTED_HOURS:
                raise ValueError("MARK_SENSITIVITY_FAVORABLE_PHYSICAL_" + tier + "_" + order)
            audit = independent_favorable_audit(d, ledger, fee, slip, order)
            base = baseline[(tier, order)]
            if audit["funding_asset_events"] != int(d["event"][ot.WARMUP+1:].sum()):
                raise ValueError("MARK_SENSITIVITY_EVENT_COVERAGE")
            cells.append({
                "tier": tier, "funding_order": order,
                "baseline_worst": {k: base[k] for k in
                    ("final_equity", "cagr", "year_returns", "max_dd",
                     "turnover", "funding", "physical_fills", "forced_safety_fills")},
                "favorable_counterfactual": {k: favorable[k] for k in
                    ("final_equity", "cagr", "year_returns", "max_dd",
                     "turnover", "funding", "physical_fills", "forced_safety_fills")},
                "paired_terminal_nav_delta_usd": favorable["final_equity"] - base["final_equity"],
                "paired_cagr_delta_not_a_bound": favorable["cagr"] - base["cagr"],
                "paired_turnover_delta_usd": favorable["turnover"] - base["turnover"],
                "audit": audit,
            })
            print("MARK_SENSITIVITY_CELL", tier, order,
                  "worst_NAV", base["final_equity"],
                  "favorable_NAV", favorable["final_equity"],
                  "paired_delta", cells[-1]["paired_terminal_nav_delta_usd"],
                  flush=True)
    return {
        "decision": DECISION,
        "frozen_rejected_fixture": "PU_NOT_REOPENED",
        "preregistration": "v98_dynamic_mark_sensitivity_prereg_20261101.md",
        "physical_pairs": len(cells),
        "synthetic": tests,
        "cells": cells,
        "exact_exchange_marks_attested": False,
        "account_specific_execution_attested": False,
        "favorable_path_is_not_executable": True,
        "paired_difference_is_not_a_dynamic_nav_bound": True,
        "candidate_promoted": False,
        "2025_exposed_training_only": True,
        "2026_plus_accessed": False,
        "holdout_accessed": False,
        "benchmarks_accessed": False,
        "paper_live_authorized": False,
    }


if __name__ == "__main__":
    print(json.dumps(synthetic_controls(), sort_keys=True))
