#!/usr/bin/env python3
"""V98 Phase1009: frozen O complete seven-slot 90-cell authenticated economic gate.

Source and O target pins must pass BEFORE any historical PnL. No V99/V16,
no 2025+, no holdout, no rescue of rejected N.
"""
from __future__ import annotations
import hashlib
import json
import math
import tempfile
from pathlib import Path
from phase803_training_ohlc_official_replay import run as fresh_ohlc
from phase1000_four_asset_source_policy import (
    run as fresh_policy, OUT as POLICY_OUT, BOUNDS, MONTH_PINS,
)
from phase866_k_sevenslot_source import ASSETS, PINS
from phase877_k_official_economic_dispatch import load_source_arrays, PASS_OHLC
from phase876_k_funded_ledger import FEE_TIERS, ORDERS, CAPITAL_MODES
from phase1008_o_frozen_paths import ROOT, PATHS, FROZEN_O, verify_o_source, frozen_o_paths
from phase1007_o_funded_ledger_hourly import simulate_o_with_hourly

OUT = ROOT / "phase1009_o_90cell_training_result.json"
PASS_POLICY = "PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY"


def source_gate():
    verify_o_source()
    o = fresh_ohlc()
    if not isinstance(o,dict) or o.get("decision") != PASS_OHLC or o.get("vendor_origin_attested") is not True:
        raise PermissionError("O_FRESH_100_OHLC_NOT_ATTESTED")
    for asset in ASSETS:
        x = o.get("assets",{}).get(asset,{})
        if x.get("sha256") != PINS[asset] or x.get("monthly_archives") != 25 or x.get("hours") != 18288:
            raise PermissionError("O_OHLC_SOURCE_PIN_DRIFT_"+asset)
    if fresh_policy() != 0:
        raise PermissionError("O_FRESH_100_MARK_FUNDING_SOURCE_FAILED")
    p = json.loads(POLICY_OUT.read_text())
    expected = {
        "decision":PASS_POLICY,
        "verified_mark_monthly_archives":100,
        "verified_mark_daily_archives":112,
        "verified_funding_monthly_archives":100,
        "verified_asset_events":9144,
        "vendor_archive_checksum_attested":True,
        "historical_pnl_computed":False,
        "economic_clearance":False,
        "validation_2025_read":False,
        "holdout_accessed":False,
        "external_benchmarks_used":False,
        "api_mark_attested":False,
    }
    for k,v in expected.items():
        if type(p.get(k)) is not type(v) or p[k] != v:
            raise PermissionError("O_SOURCE_POLICY_RECEIPT_DRIFT_"+k)
    manifests = p.get("exception_manifests",{})
    if set(manifests) != set(ASSETS):
        raise PermissionError("O_FOUR_ASSET_EXCEPTION_MANIFEST_MISSING")
    for asset in ASSETS:
        item = manifests[asset]
        overlap = item.get("overlap",{})
        if (item.get("monthly_zip_sha256") != MONTH_PINS[asset] or
            len(item.get("daily_zip_sha256",{})) != 28 or
            item.get("monthly_rows") != 648 or item.get("daily_rows") != 672 or
            item.get("inserted_daily_rows") != 24 or
            overlap.get("shared") != 648 or overlap.get("missing_left") != 24 or
            overlap.get("missing_right") != 0 or overlap.get("different_rows") != 0):
            raise PermissionError("O_FEB_SOURCE_MANIFEST_DRIFT_"+asset)
    bounds_sha = hashlib.sha256(BOUNDS.read_bytes()).hexdigest()
    if bounds_sha != p.get("bounds_csv_sha256"):
        raise PermissionError("O_FUNDING_MARK_BOUNDS_DRIFT")
    return {"ohlc":o["decision"],"mark_funding":p["decision"],"bounds_sha256":bounds_sha}


def isolated_source_arrays():
    with tempfile.TemporaryDirectory(prefix="v98_o_source_") as tmp:
        root = Path(tmp)
        (root/"phase243_clean4_canonical").symlink_to(
            (ROOT/"phase243_clean4_canonical").resolve(), target_is_directory=True)
        (root/"phase797_conservative_training_funding_bounds.csv").symlink_to(BOUNDS.resolve())
        return load_source_arrays(root)


def complete_matrix_o(paths, prices, quote, rate, mark, event, years):
    if tuple(paths) != PATHS or tuple(FROZEN_O) != PATHS:
        raise PermissionError("O_PATH_ORDER_DRIFT")
    cases, failures, count = {}, [], 0
    for name in PATHS:
        cases[name] = {}
        for tier, fee in FEE_TIERS.items():
            cases[name][tier] = {}
            for order in ORDERS:
                cases[name][tier][order] = {}
                for mode in CAPITAL_MODES:
                    count += 1
                    try:
                        r = simulate_o_with_hourly(
                            paths[name], prices["open"], prices["high"], prices["low"], prices["close"],
                            quote, rate, mark, event, fee, order=order, mode=mode,
                            years=years, require_full_sample=True)
                    except Exception as exc:
                        r = {"survived":False, "reason":type(exc).__name__+": "+str(exc)[:200]}
                    cases[name][tier][order][mode] = r
                    if not r.get("survived",False):
                        failures.append({"path":name,"fee_tier":tier,"order":order,"mode":mode,
                                         "reason":r.get("reason"),"breach_index":r.get("breach_index")})
    if count != 90:
        raise AssertionError("O_INCOMPLETE_90_CELL_MATRIX")
    return {"cells_attempted":count,"cells_survived":count-len(failures),
            "failures":failures,"cases":cases}


def growth_gate_o(matrix):
    if matrix["cells_attempted"] != 90 or matrix["failures"]:
        return {"passed":False,"reason":"incomplete_or_failed_survival",
                "failed_cells":len(matrix["failures"])}
    for path in PATHS:
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    folds = matrix["cases"][path][tier][order][mode].get("folds",{})
                    if set(folds) != {"2023","2024"} or folds["2023"].get("days") != 365 or folds["2024"].get("days") != 366:
                        return {"passed":False,"reason":"incomplete_chronological_folds"}
    failures, edges = [], {}
    for year in ("2023","2024"):
        for tier in ("base","severe"):
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    key = "/".join((year,tier,order,mode))
                    full = matrix["cases"]["O_full"][tier][order][mode]["folds"][year]["log_wealth"]
                    if not math.isfinite(full) or full <= 0:
                        failures.append({"cell":key,"reason":"nonpositive_full_growth","value":full})
                    marginal = {}
                    for path in PATHS:
                        if path == "O_full":
                            continue
                        alt = matrix["cases"][path][tier][order][mode]["folds"][year]["log_wealth"]
                        diff = full-alt
                        marginal[path] = diff
                        if not math.isfinite(diff) or diff <= 0:
                            failures.append({"cell":key,"reason":"nonpositive_marginal","path":path,"value":diff})
                    edges[key] = {"O_full_log_wealth":full,"marginal":marginal}
    return {"passed":not failures,"reason":"training_only_pending_validation" if not failures else "failed_growth_or_marginal",
            "failures":failures,"edges":edges}


def run():
    result = {"phase":1009,"decision":"BLOCKED_BEFORE_PNL","historical_pnl_computed":False,
              "ledger_invocations":0,"promotion_eligible":False,
              "validation_2025_read":False,"holdout_accessed":False,
              "external_benchmarks_used":False,"frozen_source_modified":False}
    try:
        result["source_receipts"] = source_gate()
        frames, hashes = frozen_o_paths()
        if hashes != FROZEN_O:
            raise PermissionError("O_FROZEN_TARGET_DRIFT")
        arrays, rate, mark, event, years = isolated_source_arrays()
        prices = {k:arrays[k] for k in ("open","high","low","close")}
        matrix = complete_matrix_o({k:v.to_numpy(float) for k,v in frames.items()},
                                   prices,arrays["quote_volume"],rate,mark,event,years)
        result["historical_pnl_computed"] = True
        result["ledger_invocations"] = matrix["cells_attempted"]
        result["matrix"] = matrix
        result["growth_gate"] = growth_gate_o(matrix)
        result["decision"] = "PASS_O_TRAINING_ONLY_PENDING_SEPARATE_VALIDATION" if result["growth_gate"]["passed"] else "REJECT_O_TRAINING_NO_RESCUE"
    except Exception as exc:
        result["decision"] = "BLOCKED_AFTER_PNL_NO_PROMOTION" if result["historical_pnl_computed"] else "BLOCKED_BEFORE_PNL"
        result["reason"] = type(exc).__name__+": "+str(exc)[:350]
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"phase":1009,"decision":result["decision"],
                      "historical_pnl_computed":result["historical_pnl_computed"],
                      "ledger_invocations":result["ledger_invocations"],
                      "cells_survived":result.get("matrix",{}).get("cells_survived"),
                      "reason":result.get("reason")},sort_keys=True))
    return 0 if result["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(run())
