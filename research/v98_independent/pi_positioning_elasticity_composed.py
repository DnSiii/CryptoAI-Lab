#!/usr/bin/env python3
"""V98 PI: preregistered funding-crowding seven-slot 2022-25 EXPOSED training.
No PG signal/parameter reuse, 2026+, holdout, benchmarks, paper or live.
"""
import json
import math
import numpy as np
from ot_breadth_dispersion import (
    source_gate, physical, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP
)
from ot_independent_oracle import independent_fills

CLOCK = tuple(range(WARMUP, HOURS, STEP))
BOOKS = {
    "PI_full": (0, 1, 2, 3),
    "PI_core_only": (0,),
    "PI_minus_opportunity": (0, 2, 3),
    "PI_minus_RV": (0, 1, 3),
    "PI_minus_stress": (0, 1, 2),
}
PRIORITY = {
    "expansion": (1, 2, 3),
    "contraction": (3, 2, 1),
    "neutral": (2, 1, 3),
    "unknown": (2, 1, 3),
}


def signals(d, oi, observed):
    close = np.asarray(d["c"], dtype=float)
    rates = np.asarray(d["rate"], dtype=float)
    event = np.asarray(d["event"], dtype=bool)
    oi = np.asarray(oi, dtype=float)
    observed = np.asarray(observed, dtype=bool)
    if (close.shape != (HOURS, 4) or rates.shape != (HOURS, 4)
            or event.shape != (HOURS, 4) or oi.shape != (HOURS, 4)
            or observed.shape != (HOURS, 4)
            or not np.array_equal(observed, np.isfinite(oi))
            or np.any(oi[observed] <= 0)
            or not np.isfinite(close).all() or np.any(close <= 0)
            or not np.isfinite(rates).all() or np.any(rates[~event] != 0)):
        raise ValueError("PI_SOURCE_GEOMETRY_OR_FUNDING")
    p = np.log(close)
    out = {}
    for t in CLOCK:
        r504 = p[t] - p[t-504]
        r168 = p[t] - p[t-168]
        r72 = p[t] - p[t-72]
        r24 = p[t] - p[t-24]
        sigma = np.std(np.diff(p[t-504:t+1], axis=0), axis=0)*math.sqrt(504)
        quality = (r504+0.5*r168)/np.maximum(sigma, 0.03)
        raw = np.zeros((4, 4), dtype=float)
        if r504[0] > 0 and int(np.sum(r504 > 0)) >= 2:
            ranked = sorted((j for j in range(4) if r168[j] > 0),
                            key=lambda j: (-quality[j], j))
            for j, weight in zip(ranked[:2], (0.38, 0.20)):
                raw[0, j] = weight
        elif r504[0] < 0 and int(np.sum(r504 > 0)) <= 1:
            ranked = sorted((j for j in range(4) if r168[j] < 0),
                            key=lambda j: (quality[j], j))
            for j, weight in zip(ranked[:2], (-0.34, -0.18)):
                raw[0, j] = weight
        # Stress is price-only: an OI outage must never erase its valid signal.
        btc_hourly = np.diff(p[t-168:t+1, 0])
        v24 = float(np.std(btc_hourly[-24:]))
        v168 = float(np.std(btc_hourly))
        if v168 > 1e-12 and v24/v168 > 1.8:
            if r24[0] < -0.05 and r168[0] < 0:
                raw[3, 0] = -0.18
            elif r24[0] > 0.05 and r72[0] < 0:
                raw[3, 0] = 0.18
        eligible = bool(observed[t-167:t+1].all())
        mode = "unknown"
        features = None
        if eligible:
            oi72 = np.log(oi[t] / oi[t-72])
            oi168 = np.log(oi[t] / oi[t-167])
            if not (np.isfinite(oi72).all() and np.isfinite(oi168).all()):
                raise ValueError("PI_FEATURE_NONFINITE")
            candidates = []
            for j in range(4):
                if oi72[j] <= 0.06:
                    continue
                if r72[j] > 0.06 and r24[j] > 0.01:
                    candidates.append((-abs(float(r72[j])), j, 0.22))
                elif r72[j] < -0.06 and r24[j] < -0.01:
                    candidates.append((-abs(float(r72[j])), j, -0.22))
            if candidates:
                _, j, signed = min(candidates)
                raw[1, j] = signed
            score = r168 - 0.5*oi168
            hi = min(range(4), key=lambda j: (-score[j], j))
            lo = min(range(4), key=lambda j: (score[j], j))
            if (hi != lo and score[hi]-score[lo] > 0.15
                    and r72[hi] > 0 and r72[lo] < 0
                    and abs(oi168[hi]-oi168[lo]) < 0.25):
                raw[2, hi] = 0.14
                raw[2, lo] = -0.14
            mode = ("expansion" if int(np.sum(oi168 > 0.025)) >= 3 else
                    "contraction" if int(np.sum(oi168 < -0.025)) >= 3
                    else "neutral")
            features = (oi72, oi168, score)
        out[t] = (raw, mode, eligible, features)
    if len(out) != 157:
        raise ValueError("PI_CLOCK")
    return out


def allocate(raw, mode, active, history):
    if (raw.shape != (4, 4) or history.shape != (168, 4)
            or mode not in PRIORITY or not np.isfinite(raw).all()
            or not np.isfinite(history).all()):
        raise ValueError("PI_ALLOCATOR_INPUT")
    held = np.zeros((4, 4), dtype=float)
    if 0 in active:
        held[0] = raw[0]
    core_gross = float(np.abs(held[0]).sum())
    if core_gross > 0.58 + 1e-10:
        raise ValueError("PI_CORE_LIMIT")
    room = min(0.32, max(0., 0.84-core_gross))
    for sleeve in PRIORITY[mode]:
        if sleeve not in active or room <= 1e-12:
            continue
        gross = float(np.abs(raw[sleeve]).sum())
        if gross <= 1e-12:
            continue
        candidate = history @ raw[sleeve]
        existing = history @ held.sum(axis=0)
        if np.std(candidate) > 1e-12 and np.std(existing) > 1e-12:
            corr = float(np.corrcoef(candidate, existing)[0, 1])
        else:
            corr = 0.
        if not math.isfinite(corr):
            raise ValueError("PI_CORRELATION")
        request = gross * (0.5 if corr > 0.35 else 1.)
        take = min(room, request)
        held[sleeve] = raw[sleeve] * (take/gross)
        room -= take
    if (float(np.abs(held).sum()) > 0.84 + 1e-10
            or float(np.abs(held[1:]).sum()) > 0.32 + 1e-10):
        raise ValueError("PI_GROSS_LIMIT")
    return held


def target_books(d, decisions):
    p = np.log(np.asarray(d["c"], dtype=float))
    return {
        book: {
            t: allocate(raw, mode, active, np.diff(p[t-168:t+1], axis=0))
            for t, (raw, mode, eligible, features) in decisions.items()
        } for book, active in BOOKS.items()
    }


def synthetic_test():
    h = np.arange(HOURS, dtype=float)[:, None]
    j = np.arange(4, dtype=float)[None, :]
    c = 100*np.exp(0.00004*h*(1+j/10)+0.07*np.sin(h/65+j))
    oi = 20000*np.exp(0.000004*h*(1+j/5)+0.07*np.sin(h/105+j))
    rate = np.zeros((HOURS, 4))
    event = np.zeros((HOURS, 4), bool)
    event[::8] = True
    rate[::8] = 0.00005*np.sin(h[::8]/200+j)
    observed = np.ones((HOURS, 4), bool)
    a = signals({"c": c, "rate": rate, "event": event}, oi, observed)
    c2, oi2, rate2 = c.copy(), oi.copy(), rate.copy()
    c2[15000:] *= np.array([1.5, 0.6, 1.7, 0.8])
    oi2[15000:] *= 0.4
    rate2[15000:] *= -2.
    b = signals({"c": c2, "rate": rate2, "event": event}, oi2, observed)
    for t in CLOCK:
        if t < 15000:
            x, y = a[t], b[t]
            if (x[1:3] != y[1:3] or not np.array_equal(x[0], y[0])
                    or (x[3] is not None and any(not np.array_equal(v, w)
                                                for v, w in zip(x[3], y[3])))):
                raise ValueError("PI_FUTURE_MUTATION_LEAK")
    t = CLOCK[30]
    mask = observed.copy()
    mask[t-20, 2] = False
    oi2 = oi.copy()
    oi2[t-20, 2] = np.nan
    m = signals({"c": c, "rate": rate, "event": event}, oi2, mask)
    if (m[t][2] or np.any(m[t][0][1:3])
            or not np.array_equal(m[t][0][0], a[t][0][0])
            or not np.array_equal(m[t][0][3], a[t][0][3])):
        raise ValueError("PI_QUARANTINE_FAIL_OPEN")
    books = target_books({"c": c}, a)
    if (len(books) != 5 or any(len(v) != 157 for v in books.values())
            or any(np.abs(w).sum() > 0.84+1e-10
                   for v in books.values() for w in v.values())):
        raise ValueError("PI_SYNTHETIC_GROSS")
    return {"decision": "PASS_PI_SYNTHETIC_CAUSALITY_NOT_PNL",
            "decisions": 157, "books": 5,
            "future_price_oi_funding_mutation_safe": True,
            "missing_oi_window_fail_closed": True, "pnl_computed": False}


def run(d, oi, observed, provenance):
    source = source_gate(d)
    decisions = signals(d, oi, observed)
    books = target_books(d, decisions)
    from pi_funding_crowding_independent_oracle import independent_decisions
    oracle = independent_decisions(d, oi, observed, decisions, books)
    if oracle["mismatches"]:
        raise ValueError("PI_INDEPENDENT_ORACLE")
    print("PI_ORACLE", json.dumps(oracle, sort_keys=True), flush=True)
    cells = []
    ledger = None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture = tier == "base" and order == "carried_before_fill" and book == "PI_full"
                row, detail = physical(d, books[book], book, tier, order, record=capture)
                cells.append(row)
                if capture:
                    ledger = detail
                print("PI_CELL", tier, order, book, row["passed"],
                      row.get("cagr"), row.get("failure"), flush=True)
    accounting = (independent_accounting(d, ledger)
                  if ledger is not None and len(ledger) == HOURS-WARMUP-1 else None)
    fills = independent_fills(d, ledger) if accounting is not None else None
    failures = []
    marginals = {}
    for tier in COSTS:
        for order in ORDERS:
            group = {r["book"]: r for r in cells if r["tier"] == tier and r["order"] == order}
            label = tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical")
                continue
            full = group["PI_full"]
            marginals[label] = {
                slot: full["log_growth"]-group[book]["log_growth"]
                for slot, book in (("Opportunity", "PI_minus_opportunity"),
                                   ("Relative_Value", "PI_minus_RV"),
                                   ("Stress_Recovery", "PI_minus_stress"))
            }
            if tier not in ("base", "severe"):
                continue
            if full["cagr"] <= (0.80 if tier == "base" else 0.60):
                failures.append(label+":CAGR")
            if full["turnover"] > 1000000:
                failures.append(label+":turnover")
            if tier == "severe":
                if full["max_dd"] <= -0.45:
                    failures.append(label+":drawdown")
                if any(v <= 0 for v in full["year_returns"].values()):
                    failures.append(label+":annual")
            for slot, book in (("Opportunity", "PI_minus_opportunity"),
                               ("Relative_Value", "PI_minus_RV"),
                               ("Stress_Recovery", "PI_minus_stress")):
                if marginals[label][slot] <= 0.02:
                    failures.append(label+":"+slot+":marginal")
                for year in ("2023", "2024", "2025"):
                    delta = (math.log1p(full["year_returns"][year]) -
                             math.log1p(group[book]["year_returns"][year]))
                    if delta < -0.03:
                        failures.append(label+":"+slot+":"+year+":annual_marginal")
    if accounting is None or accounting["cash_identity_mismatches"]:
        failures.append("independent_hourly_accounting")
    if fills is None or fills["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills_and_funding")
    out = {
        "architecture": "PI",
        "preregistration": "pi_positioning_elasticity_prereg_20261101.md",
        "source": source, "oi_source": provenance,
        "weekly_decisions": len(decisions),
        "oi_eligible_decisions": sum(x[2] for x in decisions.values()),
        "cells": cells, "marginals": marginals,
        "independent_decision_oracle": oracle,
        "independent_accounting": accounting,
        "independent_fills": fills,
        "gate_failures": failures,
        "decision": "REJECT_PI_TRAINING" if failures else "PASS_PROVISIONAL_PI_TRAINING_NOT_VALIDATED",
        "2025_exposed_training_only": True, "exact_event_mark_attested": False,
        "2026_plus_accessed": False, "holdout_accessed": False,
        "external_benchmarks_accessed": False, "paper_or_live_authorized": False,
    }
    print("PI_RESULT_JSON", json.dumps(out, separators=(",", ":"), allow_nan=False), flush=True)
    return out


if __name__ == "__main__":
    print(json.dumps(synthetic_test(), sort_keys=True))
