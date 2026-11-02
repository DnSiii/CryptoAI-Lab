#!/usr/bin/env python3
"""V98-only fixed static-exposure controls, not a strategy or approved engine."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS, source_gate
from wg_funding_inventory_physical import simulate, TIERS, ORDERS, HEADER

BOOKS = {
    "cash": (0., 0., 0., 0.),
    "btc_80": (.80, 0., 0., 0.),
    "eth_80": (0., .80, 0., 0.),
    "bnb_80": (0., 0., .80, 0.),
    "sol_80": (0., 0., 0., .80),
    "equal_20": (.20, .20, .20, .20),
}
FIRST_SIGNAL_HOUR = 743
EXPECTED_EVENTS = 13524

def target_book(name):
    if name not in BOOKS:
        raise ValueError("UNKNOWN_STATIC_BOOK")
    return {FIRST_SIGNAL_HOUR: np.array(BOOKS[name], dtype=float)}

def self_test():
    assert HOURS == 27048 and len(BOOKS) == 6 and len(TIERS) == 3 and len(ORDERS) == 2
    assert len(set(BOOKS)) == 6
    for name in BOOKS:
        t = target_book(name)
        assert list(t) == [FIRST_SIGNAL_HOUR]
        assert np.all(np.array(t[FIRST_SIGNAL_HOUR]) >= 0)
        assert np.sum(t[FIRST_SIGNAL_HOUR]) <= .80 + 1e-12
    return {"decision": "PASS_STATIC_CONTROL_CONTRACT_NOT_PNL", "cells_planned": 36,
            "2026_accessed": False, "holdout_accessed": False}

def run(d, outdir):
    source_gate(d)
    if int(np.asarray(d["event"]).sum()) != EXPECTED_EVENTS:
        raise ValueError("STATIC_FUNDING_COUNT")
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    cells = []
    for tier in TIERS:
        for order in ORDERS:
            for name in BOOKS:
                keep = tier == "base" and order == "carried_before_fill" and name in ("cash", "equal_20")
                result, rows = simulate(d, target_book(name), tier, order, record=keep)
                result["book"] = name
                cells.append(result)
                if keep:
                    path = out / ("static_" + name + "_base_hourly.csv")
                    with path.open("w", newline="") as handle:
                        writer = csv.writer(handle, lineterminator="\n")
                        writer.writerow(HEADER)
                        for row in rows:
                            writer.writerow([
                                json.dumps(v.tolist(), separators=(",", ":")) if isinstance(v, np.ndarray)
                                else format(v, ".16g") if isinstance(v, float) else v
                                for v in row
                            ])
                print("STATIC_CELL", name, tier, order, result.get("passed"),
                      result.get("cagr"), result.get("reason"), "stop_hour",
                      result.get("hour"), "funding_paid",
                      result.get("signed_funding"), "fees",
                      result.get("fees_spread_impact"), flush=True)
    if len(cells) != 36:
        raise ValueError("STATIC_CELL_COUNT")
    summary = {
        "decision": "STATIC_DIAGNOSTIC_EXPOSED_ONLY_NOT_ENGINE",
        "source": "Clean-4 2022-12 warmup to 2025-12-31",
        "hours": HOURS,
        "native_funding_events": EXPECTED_EVENTS,
        "cells": cells,
        "account_costs_authenticated": False,
        "exact_exchange_marks_authenticated": False,
        "independent_audit_pending": True,
        "2026_accessed": False,
        "holdout_accessed": False,
        "benchmarks_accessed": False,
        "paper_live_authorized": False,
    }
    (out / "static_diagnostic.json").write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("STATIC_DECISION", summary["decision"], flush=True)
    return summary

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    for name in ("old-root", "old-envelope", "new-root", "corrected-root", "out-dir"):
        p.add_argument("--" + name)
    args = p.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        for key in ("old_root", "old_envelope", "new_root", "corrected_root", "out_dir"):
            if not getattr(args, key):
                p.error("--" + key.replace("_", "-") + " is required")
        run(load(args.old_root, args.old_envelope, args.new_root, args.corrected_root), args.out_dir)
