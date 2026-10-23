#!/usr/bin/env python3
"""V98 Phase1001: 90 frozen N economic cells after fresh four-gap source attestation.

Never edits frozen source; 2023/2024 chronological training only; no benchmarks.
"""
from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path

from phase998_n_provenance_90cell import (
    ROOT, verify_frozen_files, PASS_OHLC, ASSETS, PINS,
    load_source_arrays, freeze_n, N_PATHS, FROZEN_N,
    complete_matrix_hourly, growth_gate_n, fresh_ohlc,
)
from phase1000_four_asset_source_policy import (
    run as fresh_policy, OUT as POLICY_OUT, BOUNDS, MONTH_PINS,
)

OUT = ROOT / "phase1001_n_four_gap_90cell_result.json"
PASS_POLICY = "PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY"


def fresh_source_gate():
    verify_frozen_files()
    o = fresh_ohlc()
    if not isinstance(o, dict) or o.get("decision") != PASS_OHLC or o.get("vendor_origin_attested") is not True:
        raise PermissionError("FRESH_100_OHLC_SOURCE_FAILED")
    for asset in ASSETS:
        item = o.get("assets", {}).get(asset, {})
        if item.get("sha256") != PINS[asset] or item.get("monthly_archives") != 25 or item.get("hours") != 18288:
            raise PermissionError("FRESH_OHLC_PIN_DRIFT_" + asset)
    if fresh_policy() != 0:
        raise PermissionError("FRESH_FOUR_GAP_SOURCE_POLICY_FAILED")
    receipt = json.loads(POLICY_OUT.read_text())
    required = {
        "decision": PASS_POLICY, "verified_mark_monthly_archives": 100,
        "verified_mark_daily_archives": 112,
        "verified_funding_monthly_archives": 100, "verified_asset_events": 9144,
        "historical_pnl_computed": False, "economic_clearance": False,
        "validation_2025_read": False, "holdout_accessed": False,
        "external_benchmarks_used": False, "api_mark_attested": False,
        "vendor_archive_checksum_attested": True,
    }
    for key, expected in required.items():
        if type(receipt.get(key)) is not type(expected) or receipt[key] != expected:
            raise PermissionError("PHASE1000_SOURCE_RECEIPT_INVALID_" + key)
    manifests = receipt.get("exception_manifests", {})
    if set(manifests) != set(ASSETS):
        raise PermissionError("FOUR_ASSET_EXCEPTION_MANIFEST_INCOMPLETE")
    for asset in ASSETS:
        item = manifests[asset]
        overlap = item.get("overlap", {})
        if (item.get("monthly_zip_sha256") != MONTH_PINS[asset]
            or len(item.get("daily_zip_sha256", {})) != 28
            or item.get("monthly_rows") != 648
            or item.get("daily_rows") != 672
            or item.get("inserted_daily_rows") != 24
            or overlap.get("shared") != 648
            or overlap.get("missing_left") != 24
            or overlap.get("missing_right") != 0
            or overlap.get("different_rows") != 0):
            raise PermissionError("FOUR_ASSET_SOURCE_MANIFEST_DRIFT_" + asset)
    if hashlib.sha256(BOUNDS.read_bytes()).hexdigest() != receipt.get("bounds_csv_sha256"):
        raise PermissionError("SOURCE_BOUNDS_SHA_DRIFT")
    return {
        "ohlc": o["decision"], "mark": receipt["decision"],
        "bounds_csv_sha256": receipt["bounds_csv_sha256"],
        "source_policy": "four_checksum_verified_daily_feb24_gaps",
    }


def isolated_arrays():
    with tempfile.TemporaryDirectory(prefix="v98_phase1001_source_") as d:
        root = Path(d)
        (root / "phase243_clean4_canonical").symlink_to(
            (ROOT / "phase243_clean4_canonical").resolve(), target_is_directory=True
        )
        (root / "phase797_conservative_training_funding_bounds.csv").symlink_to(BOUNDS.resolve())
        return load_source_arrays(root)


def run():
    out = {
        "phase": 1001, "decision": "BLOCKED_BEFORE_PNL",
        "historical_pnl_computed": False, "ledger_invocations": 0,
        "source_policy": "Phase1000 preregistered four Feb24 daily gaps",
        "validation_2025_read": False, "holdout_accessed": False,
        "external_benchmarks_used": False, "promotion_eligible": False,
        "frozen_source_modified": False,
    }
    try:
        out["source_receipts"] = fresh_source_gate()
        arrays, rate, mark, event, years = isolated_arrays()
        paths, info = freeze_n(ROOT)
        if tuple(info["paths_sha256"]) != N_PATHS or info["paths_sha256"] != FROZEN_N:
            raise PermissionError("FROZEN_N_TARGET_SHA_DRIFT")
        out["economic_execution_started"] = True
        matrix = complete_matrix_hourly(
            {name: frame.to_numpy(float) for name, frame in paths.items()},
            {key: arrays[key] for key in ("open", "high", "low", "close")},
            arrays["quote_volume"], rate, mark, event, years,
        )
        out["historical_pnl_computed"] = True
        out["ledger_invocations"] = matrix["cells_attempted"]
        out["matrix"] = matrix
        out["growth_gate"] = growth_gate_n(matrix)
        out["decision"] = (
            "PASS_N_FOUR_GAP_TRAINING_ONLY_PENDING_SEPARATE_VALIDATION"
            if out["growth_gate"]["passed"] else "REJECT_N_TRAINING_NO_RESCUE"
        )
    except Exception as exc:
        out["decision"] = "BLOCKED_AFTER_PNL_NO_PROMOTION" if out["historical_pnl_computed"] else "BLOCKED_BEFORE_PNL"
        out["reason"] = type(exc).__name__ + ": " + str(exc)[:350]
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "phase": 1001, "decision": out["decision"],
        "historical_pnl_computed": out["historical_pnl_computed"],
        "ledger_invocations": out["ledger_invocations"],
        "reason": out.get("reason"),
    }, sort_keys=True))
    return 0 if out["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(run())
