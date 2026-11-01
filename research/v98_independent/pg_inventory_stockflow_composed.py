#!/usr/bin/env python3
"""V98 PG preregistered inventory stock-to-flow composed Clean-4 2022-25 training.
2025 exposed training only. No 2026+, XRP, V14/V15/V99, holdout, Frozen or paper.
"""
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from ot_breadth_dispersion import (
    source_gate, physical, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP
)
from ot_independent_oracle import independent_fills
from v98_oi_full_history_v2_independent_audit_20261027 import run as audit_old
from v98_oi_2025_full_native_independent_audit import audit as audit_new

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
START = dt.datetime(2022, 12, 1, tzinfo=dt.timezone.utc)
CLOCK = tuple(range(WARMUP, HOURS, STEP))
BOOKS = {
    "PG_full": (0, 1, 2, 3),
    "PG_core_only": (0,),
    "PG_minus_opportunity": (0, 2, 3),
    "PG_minus_RV": (0, 1, 3),
    "PG_minus_stress": (0, 1, 2),
}
PRIORITY = {
    "accumulation": (1, 2, 3),
    "liquidation": (3, 2, 1),
    "mixed": (2, 1, 3),
    "unknown": (1, 2, 3),
}


def unique(root, filename):
    paths = list(Path(root).rglob(filename))
    if len(paths) != 1:
        raise ValueError("PG_OI_ARTIFACT_INVENTORY_" + filename)
    return paths[0]


def native_oi(old_root, new_root):
    """Independently re-audit both pinned artifacts, then load exact, never-filled OI."""
    old = audit_old(old_root)
    new = audit_new(new_root)
    if not old["decision"].startswith("PASS_OI_ARTIFACT_INTEGRITY"):
        raise ValueError("PG_OLD_OI_AUDIT")
    if new["decision"] != "PASS_2025_NATIVE_OI_INDEPENDENT_ARTIFACT_AUDIT_NOT_PNL":
        raise ValueError("PG_NEW_OI_AUDIT")
    oi = np.full((HOURS, 4), np.nan, dtype=np.float64)
    manifest_mask = np.zeros((HOURS, 4), dtype=bool)
    hashes = []
    specs = (
        (old_root, "v98_oi_full_history_source_v2_report_20261027.json",
         "v98_oi_full_history_v2_verified_hourly_20261027.csv",
         "2022-12-01", "2024-12-31"),
        (new_root, "v98_oi_2025_native_source_report.json",
         "v98_oi_2025_verified_hourly.csv",
         "2025-01-01", "2025-12-31"),
    )
    for root, report_name, csv_name, first, last in specs:
        report = json.loads(unique(root, report_name).read_text())
        csv_path = unique(root, csv_name)
        digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        if (digest != report["hourly_csv_sha256"] or
                report["date_start"] != first or report["date_end"] != last):
            raise ValueError("PG_OI_SHA_OR_SCOPE")
        hashes.append(digest)
        manifest = {(row["asset"], row["date"]): row for row in report["manifest"]}
        for (asset, date), meta in manifest.items():
            if asset not in ASSETS:
                raise ValueError("PG_OI_UNKNOWN_ASSET")
            day = dt.date.fromisoformat(date)
            t = (dt.datetime.combine(day, dt.time(), dt.timezone.utc) - START).days * 24
            if not 0 <= t <= HOURS - 24:
                raise ValueError("PG_OI_MANIFEST_RANGE")
            if meta["passed"] is True:
                manifest_mask[t:t + 24, ASSETS.index(asset)] = True
        with csv_path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                stamp = dt.datetime.fromisoformat(row["bar_open_utc"])
                if (stamp.tzinfo is None or stamp.utcoffset() != dt.timedelta(0)
                        or stamp.minute or stamp.second or stamp.microsecond
                        or not START <= stamp < dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)):
                    raise ValueError("PG_OI_FUTURE_OR_BAD_TIME")
                t = int((stamp - START).total_seconds() // 3600)
                asset = row["asset"]
                if asset not in ASSETS:
                    raise ValueError("PG_OI_UNKNOWN_CSV_ASSET")
                j = ASSETS.index(asset)
                key = (asset, stamp.date().isoformat())
                if key not in manifest or manifest[key]["passed"] is not True:
                    raise ValueError("PG_OI_QUARANTINED_ROW")
                if row["source_zip_sha256"] != manifest[key]["sha256"]:
                    raise ValueError("PG_OI_VENDOR_SHA")
                if np.isfinite(oi[t, j]):
                    raise ValueError("PG_OI_DUPLICATE_HOUR")
                value = float(row["oi_contracts"])
                if not math.isfinite(value) or value <= 0:
                    raise ValueError("PG_OI_VALUE")
                oi[t, j] = value
    observed = np.isfinite(oi)
    if (not np.array_equal(observed, manifest_mask)
            or int(observed.sum()) != 106920
            or int((~observed).sum()) != 1272):
        raise ValueError("PG_OI_MANIFEST_RECONCILIATION")
    eligible = {t: bool(observed[t-167:t+1].all()) for t in CLOCK}
    if len(CLOCK) != 157 or sum(eligible.values()) != 143:
        raise ValueError("PG_OI_PREDECLARED_CLOCK_COVERAGE")
    return oi, observed, {
        "source_sha256": hashes,
        "verified_hourly_asset_rows": int(observed.sum()),
        "quarantined_hourly_asset_rows": int((~observed).sum()),
        "eligible_168h_decisions": sum(eligible.values()),
        "blocked_168h_decisions": len(CLOCK) - sum(eligible.values()),
        "independent_old_audit": old["decision"],
        "independent_new_audit": new["decision"],
    }


def signals(d, oi, observed):
    p = np.log(np.asarray(d["c"], float))
    q = np.asarray(d["q"], float)
    if (p.shape != (HOURS, 4) or q.shape != (HOURS, 4)
            or oi.shape != (HOURS, 4) or observed.shape != (HOURS, 4)
            or not np.array_equal(observed, np.isfinite(oi))
            or np.any(oi[observed] <= 0)):
        raise ValueError("PG_SIGNAL_SOURCE_GEOMETRY")
    out = {}
    for t in CLOCK:
        r672 = p[t] - p[t-672]
        r168 = p[t] - p[t-168]
        r72 = p[t] - p[t-72]
        r24 = p[t] - p[t-24]
        sigma = np.std(np.diff(p[t-336:t+1], axis=0), axis=0) * math.sqrt(336)
        quality = (r672 + r168) / np.maximum(0.02, sigma)
        raw = np.zeros((4, 4), dtype=float)
        if r672[0] > 0:
            rank = sorted((j for j in range(4) if r168[j] > 0),
                          key=lambda j: (-quality[j], j))
            for j, w in zip(rank[:2], (0.36, 0.20)):
                raw[0, j] = w
        elif r672[0] < 0:
            rank = sorted((j for j in range(4) if r168[j] < 0),
                          key=lambda j: (quality[j], j))
            for j, w in zip(rank[:2], (-0.34, -0.18)):
                raw[0, j] = w
        eligible = bool(observed[t-167:t+1].all())
        sf = None
        mode = "unknown"
        if eligible:
            current = np.sum(q[t-167:t+1], axis=0)
            prior = np.sum(q[t-335:t-167], axis=0)
            if np.any(current <= 0) or np.any(prior <= 0):
                eligible = False
            else:
                sf = np.log(oi[t] / oi[t-167]) - np.log(current / prior)
                if not np.isfinite(sf).all():
                    raise ValueError("PG_STOCKFLOW_NONFINITE")
                candidates = [j for j in range(4)
                              if abs(r72[j]) < 0.04 and sf[j] > 0.12]
                if candidates:
                    j = min(candidates, key=lambda k: (-sf[k], k))
                    raw[1, j] = 0.20
                hi = min(range(4), key=lambda j: (-sf[j], j))
                lo = min(range(4), key=lambda j: (sf[j], j))
                if sf[hi] - sf[lo] > 0.20 and abs(r168[hi]-r168[lo]) < 0.06:
                    raw[2, hi] = 0.12
                    raw[2, lo] = -0.12
                recent = np.diff(p[t-72:t+1, 0])
                prior_vol = np.diff(p[t-336:t-71, 0])
                if (int(np.sum(sf < -0.10)) >= 3
                        and float(np.var(recent)) > 1.3 * float(np.var(prior_vol))):
                    raw[3, 0] = -0.18
                elif (int(np.sum(sf > 0.10)) >= 3
                      and r72[0] < 0 and r24[0] > 0):
                    raw[3, 0] = 0.18
                mode = ("accumulation" if int(np.sum(sf > 0)) >= 3 else
                        "liquidation" if int(np.sum(sf < 0)) >= 3 else "mixed")
        if not eligible:
            raw[1:] = 0
            sf = None
            mode = "unknown"
        out[t] = (raw, mode, eligible, sf)
    if len(out) != 157:
        raise ValueError("PG_DECISION_COUNT")
    return out


def allocate(raw, mode, active, past_returns):
    if (raw.shape != (4, 4) or past_returns.shape != (168, 4)
            or mode not in PRIORITY or not np.isfinite(raw).all()
            or not np.isfinite(past_returns).all()):
        raise ValueError("PG_ALLOCATOR_INPUT")
    held = np.zeros((4, 4), dtype=float)
    if 0 in active:
        held[0] = raw[0]
    core_gross = float(np.abs(held[0]).sum())
    if core_gross > 0.56 + 1e-10:
        raise ValueError("PG_CORE_CAP")
    room = min(0.30, max(0.0, 0.84 - core_gross))
    for k in PRIORITY[mode]:
        if k not in active or room <= 1e-12:
            continue
        gross = float(np.abs(raw[k]).sum())
        if gross <= 1e-12:
            continue
        candidate_path = past_returns @ raw[k]
        existing_path = past_returns @ np.sum(held, axis=0)
        if np.std(candidate_path) > 1e-12 and np.std(existing_path) > 1e-12:
            corr = float(np.corrcoef(candidate_path, existing_path)[0, 1])
        else:
            corr = 0.0
        if not math.isfinite(corr):
            raise ValueError("PG_ALLOCATOR_CORRELATION")
        desired = gross * (0.5 if corr > 0.50 else 1.0)
        take = min(room, desired)
        held[k] = raw[k] * (take / gross)
        room -= take
    if (float(np.abs(held).sum()) > 0.84 + 1e-10
            or float(np.abs(held[1:]).sum()) > 0.30 + 1e-10):
        raise ValueError("PG_GROSS_LIMIT")
    return held


def target_books(d, decisions):
    p = np.log(d["c"])
    return {book: {
        t: allocate(raw, mode, active, np.diff(p[t-168:t+1], axis=0))
        for t, (raw, mode, eligible, sf) in decisions.items()
    } for book, active in BOOKS.items()}


def synthetic_test():
    h = np.arange(HOURS, dtype=float)[:, None]
    j = np.arange(4, dtype=float)[None, :]
    c = 100 * np.exp(0.00003 * h * (1+j/10) + 0.04 * np.sin(h/71+j))
    q = 5000 * (1 + 0.10 * np.sin(h/63+j))
    oi = 20000 * np.exp(0.000004 * h * (1+j/5) + 0.06 * np.sin(h/110+j))
    observed = np.ones((HOURS, 4), bool)
    a = signals({"c": c, "q": q}, oi, observed)
    changed_c = c.copy()
    changed_q = q.copy()
    changed_oi = oi.copy()
    changed_c[15000:] *= np.array([1.5, .6, 1.7, .8])
    changed_q[15000:] *= 2.5
    changed_oi[15000:] *= 0.4
    b = signals({"c": changed_c, "q": changed_q}, changed_oi, observed)
    for t in CLOCK:
        if t < 15000:
            x, y = a[t], b[t]
            if (x[1:3] != y[1:3] or not np.array_equal(x[0], y[0])
                    or (x[3] is not None and not np.array_equal(x[3], y[3]))):
                raise ValueError("PG_FUTURE_MUTATION_LEAK")
    t = CLOCK[30]
    mask = observed.copy()
    mask[t-20, 2] = False
    oi_masked = oi.copy()
    oi_masked[t-20, 2] = np.nan
    masked = signals({"c": c, "q": q}, oi_masked, mask)
    if masked[t][2] or np.any(masked[t][0][1:]) or not np.array_equal(masked[t][0][0], a[t][0][0]):
        raise ValueError("PG_QUARANTINE_FAIL_OPEN")
    books = target_books({"c": c}, a)
    if (len(books) != 5 or any(len(x) != 157 for x in books.values())
            or any(float(np.abs(w).sum()) > 0.84+1e-10
                   for x in books.values() for w in x.values())):
        raise ValueError("PG_SYNTHETIC_BOOKS")
    return {"decision": "PASS_PG_SYNTHETIC_CAUSALITY_NOT_PNL",
            "decisions": 157, "books": 5,
            "future_price_volume_oi_mutation_safe": True,
            "missing_oi_window_fail_closed": True, "pnl_computed": False}


def run(d, oi, observed, provenance):
    source = source_gate(d)
    decisions = signals(d, oi, observed)
    books = target_books(d, decisions)
    from pg_inventory_stockflow_independent_oracle import independent_decisions
    oracle = independent_decisions(d, oi, observed, decisions, books)
    if oracle["mismatches"]:
        raise ValueError("PG_INDEPENDENT_DECISION_ORACLE_MISMATCH")
    print("PG_ORACLE", json.dumps(oracle, sort_keys=True), flush=True)
    cells = []
    ledger = None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture = tier == "base" and order == "carried_before_fill" and book == "PG_full"
                row, detail = physical(d, books[book], book, tier, order, record=capture)
                cells.append(row)
                if capture:
                    ledger = detail
                print("PG_CELL", tier, order, book, row["passed"],
                      row.get("cagr"), row.get("failure"), flush=True)
    audit = independent_accounting(d, ledger) if ledger is not None and len(ledger) == HOURS-WARMUP-1 else None
    fills = independent_fills(d, ledger) if audit else None
    failures = []
    marginals = {}
    for tier in COSTS:
        for order in ORDERS:
            group = {r["book"]: r for r in cells if r["tier"] == tier and r["order"] == order}
            label = tier + "/" + order
            if not all(r["passed"] for r in group.values()):
                failures.append(label + ":physical")
                continue
            full = group["PG_full"]
            marginals[label] = {
                slot: full["log_growth"] - group[book]["log_growth"]
                for slot, book in (
                    ("Opportunity", "PG_minus_opportunity"),
                    ("Relative_Value", "PG_minus_RV"),
                    ("Stress_Recovery", "PG_minus_stress"),
                )
            }
            if tier not in ("base", "severe"):
                continue
            if full["cagr"] <= (0.80 if tier == "base" else 0.60):
                failures.append(label + ":CAGR")
            if full["turnover"] > 1000000:
                failures.append(label + ":turnover")
            if tier == "severe":
                if full["max_dd"] <= -0.45:
                    failures.append(label + ":drawdown")
                if any(v <= 0 for v in full["year_returns"].values()):
                    failures.append(label + ":annual")
            for slot, book in (
                ("Opportunity", "PG_minus_opportunity"),
                ("Relative_Value", "PG_minus_RV"),
                ("Stress_Recovery", "PG_minus_stress"),
            ):
                if marginals[label][slot] <= 0.02:
                    failures.append(label + ":" + slot + ":marginal")
                for year in ("2023", "2024", "2025"):
                    delta = math.log1p(full["year_returns"][year]) - math.log1p(group[book]["year_returns"][year])
                    if delta < -0.03:
                        failures.append(label + ":" + slot + ":" + year + ":annual_marginal")
    if audit is None or audit["cash_identity_mismatches"]:
        failures.append("independent_hourly_accounting")
    if fills is None or fills["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills_and_funding")
    out = {
        "architecture": "PG",
        "preregistration": "pg_inventory_stockflow_composed_prereg_20261101.md",
        "source": source, "oi_source": provenance,
        "weekly_decisions": len(decisions),
        "oi_eligible_decisions": sum(x[2] for x in decisions.values()),
        "cells": cells, "marginals": marginals,
        "independent_decision_oracle": oracle,
        "independent_accounting": audit, "independent_fills": fills,
        "gate_failures": failures,
        "decision": "REJECT_PG_TRAINING" if failures else "PASS_PROVISIONAL_PG_TRAINING_NOT_VALIDATED",
        "2025_exposed_training_only": True, "exact_event_mark_attested": False,
        "2026_plus_accessed": False, "holdout_accessed": False,
        "external_benchmarks_accessed": False, "paper_or_live_authorized": False,
    }
    print("PG_RESULT_JSON", json.dumps(out, separators=(",", ":"), allow_nan=False), flush=True)
    return out


if __name__ == "__main__":
    print(json.dumps(synthetic_test(), sort_keys=True))
