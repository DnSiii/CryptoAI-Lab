#!/usr/bin/env python3
"""WR preregistered 30-cell physical exposed training. No live/paper."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS, source_gate
from wr_structural_beta_reversal import targets, books_from_decisions, incidence, synthetic_test
from wl_funding_buffer_physical import simulate, TIERS, ORDERS, HEADER

def run(d, outdir):
    source_gate(d)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    dec = targets(d)
    books = books_from_decisions(dec)
    counts = incidence(dec)
    (out/"wr_source.json").write_text(json.dumps({
        "hours": HOURS, "funding_events": int(d["event"].sum()),
        "weekly_decisions": len(dec), "sleeve_incidence": counts,
        "exact_marks_authenticated": False, "2026_accessed": False,
        "holdout_accessed": False
    }, indent=2, sort_keys=True)+"\n")
    failed_incidence = [s for s in ("Opportunity", "Relative_Value", "Stress_Recovery")
                        if counts[s] < 30]
    if failed_incidence:
        receipt = {
            "architecture": "WR", "decision": "REJECT_WR_PRE_ECONOMIC_INCIDENCE",
            "sleeve_incidence": counts, "failed_incidence": failed_incidence,
            "pnl_computed": False, "cells": [],
            "2026_accessed": False, "holdout_accessed": False,
            "paper_live_authorized": False
        }
        (out/"wr_exposed_physical.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True)+"\n")
        print("WR_PRE_ECONOMIC_REJECT", json.dumps(receipt, sort_keys=True), flush=True)
        return receipt
    cells = []
    ledger = None
    for tier in TIERS:
        for order in ORDERS:
            for name, book in books.items():
                keep = tier == "base" and order == "carried_before_fill" and name == "WR_full"
                result, rows = simulate(d, book, tier, order, record=keep)
                result["book"] = name
                cells.append(result)
                if keep:
                    ledger = rows
                print("WR_PHYSICAL", tier, order, name, result.get("passed"),
                      result.get("cagr"), result.get("reason"), result.get("hour"), flush=True)
    failures = []
    marginals = {}
    for tier in TIERS:
        for order in ORDERS:
            group = {x["book"]: x for x in cells
                     if x["tier"] == tier and x["order"] == order}
            label = tier + "/" + order
            if len(group) != 5 or not all(x["passed"] for x in group.values()):
                failures.append(label + ":physical")
                continue
            full = group["WR_full"]
            marginals[label] = {
                slot: full["log_growth"] - group[other]["log_growth"]
                for slot, other in (("Opportunity", "WR_minus_opportunity"),
                                    ("Relative_Value", "WR_minus_RV"),
                                    ("Stress_Recovery", "WR_minus_stress"))
            }
            if tier in ("base", "severe"):
                if full["cagr"] <= (.80 if tier == "base" else .60):
                    failures.append(label + ":cagr")
                if tier == "severe" and full["max_dd"] <= -.45:
                    failures.append(label + ":drawdown")
                if tier == "severe" and any(v <= 0 for v in full["annual_returns"].values()):
                    failures.append(label + ":negative_year")
                for slot, marginal in marginals[label].items():
                    if marginal <= 0:
                        failures.append(label + ":" + slot + ":negative_marginal")
    receipt = {
        "architecture": "WR",
        "decision": "REJECT_WR_EXPOSED_TRAINING" if failures
                    else "PASS_WR_EXPOSED_TRAINING_ONLY_NOT_VALIDATED",
        "cells": cells, "sleeve_incidence": counts, "failures": failures,
        "marginals": marginals, "pnl_computed": True,
        "2026_accessed": False, "holdout_accessed": False,
        "external_benchmarks_accessed": False,
        "account_costs_authenticated": False,
        "exact_exchange_marks_authenticated": False,
        "paper_live_authorized": False
    }
    (out/"wr_exposed_physical.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False)+"\n")
    if ledger:
        with (out/"wr_base_full_hourly_ledger.csv").open("w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(HEADER)
            for row in ledger:
                w.writerow([json.dumps(v.tolist(), separators=(",", ":"))
                            if isinstance(v, np.ndarray) else
                            format(v, ".16g") if isinstance(v, float) else v for v in row])
    print("WR_DECISION", receipt["decision"], "failed_gates", len(failures), flush=True)
    return receipt

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    for key in ("old-root", "old-envelope", "new-root", "corrected-root", "out-dir"):
        p.add_argument("--"+key)
    a = p.parse_args()
    if a.self_test:
        print(json.dumps(synthetic_test(), sort_keys=True))
    else:
        for key in ("old_root", "old_envelope", "new_root", "corrected_root", "out_dir"):
            if not getattr(a, key):
                p.error("--"+key.replace("_", "-")+" required")
        run(load(a.old_root, a.old_envelope, a.new_root, a.corrected_root), a.out_dir)
