#!/usr/bin/env python3
"""V98 Phase998 preregistered N 90-cell economic training, one-gap source policy.

No frozen file edits. All data freshly attested before PnL; no 2025+ or benchmark.
"""
from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path

from phase803_training_ohlc_official_replay import run as fresh_ohlc
from phase997_clean4_source_policy import run as fresh_policy, OUT as POLICY_OUT, BOUNDS
from phase877_k_official_economic_dispatch import load_source_arrays, PASS_OHLC
from phase866_k_sevenslot_source import ASSETS, PINS
from phase920_n_composed_source import freeze_n, N_PATHS
from phase924_n_official_90cell_dispatch import FROZEN_N, growth_gate_n
from phase940_n_official_90cell_hourly_dispatch import complete_matrix_hourly

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "phase998_n_provenance_90cell_result.json"
FROZEN_FILES = {
    "phase876_k_funded_ledger.py": "1bef3273eb1961697fbcf77912af3ef0a0027f83ddd8e94aa58d26ed2238f21c",
    "phase877_k_official_economic_dispatch.py": "1441959bb9ae5e4c14ca0baa95562995199882dbe808c0d6caf8be4586323453",
    "phase900_m_persistent_growth_source.py": "f77d9f745f8bcaafe2988b9b574cd98d245afa49e270c185db79442f9769bd64",
    "phase903_m_frozen_paths.py": "36040ebc7d1244c5ff0c477c21dc569024e349abb91398ab46d704468bbfa5e9",
    "phase915_n_open_repair.py": "9275cb642863d4dc0a79ac15ee0e31058ad5ea7caac1173278046c4b5c6bdcbd",
    "phase920_n_composed_source.py": "b5a63f06522a0ca37e65d936170559832ed7dbb7c43064e7075f845a3ac281c7",
    "phase923_n_funded_ledger.py": "a47672bed98d770c384747d5dca8f2211aee24e71099e9f3f75425d9c6a1750c",
    "phase924_n_official_90cell_dispatch.py": "0c114cd25c327e368a655a63feaadb2ea93244611e74a367f364349330da754b",
    "phase939_n_funded_ledger_hourly.py": "dfcf3c913f810721e3f983c05385bf3183f7c1dad14d0ad1adc65365cf1b28ad",
    "phase940_n_official_90cell_hourly_dispatch.py": "255905082938044068ba347b96f37c5fdd85fb0a910c558737fa1988bb5f4042",
}


def verify_frozen_files(root=ROOT):
    for name, expected in FROZEN_FILES.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise PermissionError("FROZEN_N_SOURCE_SHA_DRIFT: " + name)


def fresh_source_gate():
    verify_frozen_files()
    ohlc = fresh_ohlc()
    if not isinstance(ohlc, dict) or ohlc.get("decision") != PASS_OHLC or ohlc.get("vendor_origin_attested") is not True:
        raise PermissionError("FRESH_100_OHLC_SOURCE_FAILED")
    for asset in ASSETS:
        item = ohlc.get("assets", {}).get(asset, {})
        if item.get("sha256") != PINS[asset] or item.get("monthly_archives") != 25 or item.get("hours") != 18288:
            raise PermissionError("FRESH_OHLC_PIN_DRIFT_" + asset)
    if fresh_policy() != 0:
        raise PermissionError("FRESH_100_MARK_100_FUNDING_ONE_GAP_SOURCE_FAILED")
    receipt = json.loads(POLICY_OUT.read_text())
    required = {
        "decision": "PASS_100_MARK_100_FUNDING_ONE_AUTHENTICATED_DAILY_GAP_SOURCE_ONLY",
        "verified_mark_monthly_archives": 100,
        "verified_mark_daily_archives": 28,
        "verified_funding_monthly_archives": 100,
        "verified_asset_events": 9144,
        "historical_pnl_computed": False,
        "economic_clearance": False,
        "api_mark_attested": False,
        "validation_2025_read": False,
        "holdout_accessed": False,
        "external_benchmarks_used": False,
        "vendor_archive_checksum_attested": True,
        "exception_manifest_sha256": "efbb721590f7a73126ed8357f8bc3f94944ab1691690ed51e5a160ff3a7d5f3f",
    }
    for key, expected in required.items():
        if type(receipt.get(key)) is not type(expected) or receipt[key] != expected:
            raise PermissionError("PHASE997_SOURCE_RECEIPT_INVALID_" + key)
    if hashlib.sha256(BOUNDS.read_bytes()).hexdigest() != receipt.get("bounds_csv_sha256"):
        raise PermissionError("PHASE997_BOUNDS_SHA_MISMATCH")
    return {"ohlc": ohlc["decision"], "mark": receipt["decision"],
            "bounds_csv_sha256": receipt["bounds_csv_sha256"],
            "mark_source_policy": "one_checksum_verified_daily_24h_gap"}


def isolated_arrays(root=ROOT):
    """Unmodified Phase877 loader with isolated temporary V98-only data view."""
    with tempfile.TemporaryDirectory(prefix="v98_phase998_source_") as d:
        tmp = Path(d)
        (tmp / "phase243_clean4_canonical").symlink_to(
            (root / "phase243_clean4_canonical").resolve(), target_is_directory=True
        )
        (tmp / "phase797_conservative_training_funding_bounds.csv").symlink_to(
            BOUNDS.resolve()
        )
        return load_source_arrays(tmp)


def run():
    result = {
        "phase": 998, "decision": "BLOCKED_BEFORE_PNL",
        "historical_pnl_computed": False, "ledger_invocations": 0,
        "source_policy": "Phase997 preregistered one-gap daily reconciliation",
        "validation_2025_read": False, "holdout_accessed": False,
        "external_benchmarks_used": False, "promotion_eligible": False,
        "frozen_source_modified": False,
    }
    try:
        receipts = fresh_source_gate()
        result["source_receipts"] = receipts
        arrays, rate, mark, event, years = isolated_arrays()
        paths, info = freeze_n(ROOT)
        if tuple(info["paths_sha256"]) != N_PATHS or info["paths_sha256"] != FROZEN_N:
            raise PermissionError("FROZEN_N_TARGET_SHA_DRIFT")
        result["economic_execution_started"] = True
        matrix = complete_matrix_hourly(
            {name: frame.to_numpy(float) for name, frame in paths.items()},
            {key: arrays[key] for key in ("open", "high", "low", "close")},
            arrays["quote_volume"], rate, mark, event, years,
        )
        result["historical_pnl_computed"] = True
        result["ledger_invocations"] = matrix["cells_attempted"]
        result["matrix"] = matrix
        result["growth_gate"] = growth_gate_n(matrix)
        result["decision"] = (
            "PASS_N_SOURCE_POLICY_TRAINING_ONLY_PENDING_VALIDATION"
            if result["growth_gate"]["passed"] else "REJECT_N_TRAINING_NO_RESCUE"
        )
    except Exception as exc:
        result["decision"] = "BLOCKED_AFTER_PNL_NO_PROMOTION" if result["historical_pnl_computed"] else "BLOCKED_BEFORE_PNL"
        result["reason"] = type(exc).__name__ + ": " + str(exc)[:350]
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "phase": 998, "decision": result["decision"],
        "ledger_invocations": result["ledger_invocations"],
        "historical_pnl_computed": result["historical_pnl_computed"],
        "reason": result.get("reason"),
    }, sort_keys=True))
    return 0 if result["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(run())
