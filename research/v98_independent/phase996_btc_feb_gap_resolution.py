#!/usr/bin/env python3
"""V98 Phase996: source-only, checksum-bound BTC 2023-02 24-hour gap reconstruction.

Prerecorded exact gap; no PnL, no 2025+, no economic source-gate bypass.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from phase991_source_triangulation import (
    ALL_COLS, ASSET, BASE, DAILY, MONTH, MONTH_NAME, TIMES,
    authenticated_zip, diff, fetch_day, inspect,
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "phase996_btc_feb_gap_resolution_receipt.json"
CSV = ROOT / "phase996_btc_feb_gap_reconstructed_source_only.csv"
GAP = frozenset(TIMES[23 * 24:24 * 24])
EXPECTED_MONTH = tuple(t for t in TIMES if t not in GAP)


def reconcile(monthly_rows, daily_blocks):
    """Fail-closed deterministic pure reconstruction, never source substitution."""
    month_audit, month_map = inspect(monthly_rows, EXPECTED_MONTH)
    if month_audit["fault_count"] or len(month_map) != 648:
        raise ValueError("MONTHLY_NOT_EXACT_648_VALID_ROWS")
    if set(month_map) != set(EXPECTED_MONTH):
        raise ValueError("MONTHLY_HOLE_NOT_EXACT_FEB24")
    if set(daily_blocks) != set(range(1, 29)):
        raise ValueError("NOT_EXACTLY_28_DAILY_BLOCKS")
    daily_map = {}
    for day in range(1, 29):
        rows = daily_blocks[day]
        expected = TIMES[(day - 1) * 24:day * 24]
        check, mapped = inspect(rows, expected)
        if check["fault_count"] or len(mapped) != 24 or set(mapped) != set(expected):
            raise ValueError(f"DAILY_COVERAGE_OR_GEOMETRY_DAY_{day}")
        if set(daily_map) & set(mapped):
            raise ValueError("CROSS_DAY_DUPLICATE")
        daily_map.update(mapped)
    if set(daily_map) != set(TIMES):
        raise ValueError("DAILY_UNIVERSE_INCOMPLETE")
    overlap = diff(month_map, daily_map, ALL_COLS)
    if not (overlap["shared"] == 648 and overlap["missing_left"] == 24
            and overlap["missing_right"] == 0 and overlap["different_rows"] == 0):
        raise ValueError("MONTHLY_DAILY_OVERLAP_CONFLICT")
    if set(daily_map) - set(month_map) != GAP:
        raise ValueError("DAILY_FILL_NOT_EXACT_FEB24")
    merged = [month_map[t] if t in month_map else daily_map[t] for t in TIMES]
    final, final_map = inspect(merged, TIMES)
    if final["fault_count"] or set(final_map) != set(TIMES):
        raise ValueError("RECONSTRUCTED_SOURCE_FAILED_UTC_OR_GEOMETRY")
    return merged, overlap


def run():
    receipt = {
        "phase": 996, "asset": ASSET, "month": MONTH, "source_only": True,
        "historical_pnl_computed": False, "economic_clearance": False,
        "holdout_accessed": False, "validation_2025_read": False,
        "external_benchmarks_used": False, "frozen_source_modified": False,
        "source_substitution_authorized": False,
        "decision": "QUARANTINE",
    }
    CSV.unlink(missing_ok=True)
    try:
        _, monthly, monthly_sha = authenticated_zip(BASE, MONTH_NAME)
        receipt["monthly_sha256"] = monthly_sha
        day_rows, day_sha = {}, {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(fetch_day, day): day for day in range(1, 29)}
            for future in as_completed(futures):
                day, audit, mapped, sha = future.result()
                if audit["fault_count"] or len(mapped) != 24:
                    raise ValueError(f"OFFICIAL_DAILY_INVALID_DAY_{day}")
                day_rows[day] = [mapped[t] for t in TIMES[(day - 1) * 24:day * 24]]
                day_sha[day] = sha
        merged, overlap = reconcile(monthly, day_rows)
        output = io.StringIO(newline="")
        csv.writer(output, lineterminator="\n").writerows(merged)
        raw = output.getvalue().encode("utf-8")
        manifest = {
            "monthly_zip_sha256": monthly_sha,
            "daily_zip_sha256": {f"{day:02d}": day_sha[day] for day in range(1, 29)},
            "missing_utc": [datetime.fromtimestamp(t / 1000, timezone.utc).isoformat() for t in sorted(GAP)],
            "monthly_rows": 648, "daily_rows": 672, "inserted_daily_rows": 24,
            "overlap": overlap,
        }
        receipt.update(
            source_manifest=manifest,
            source_manifest_sha256=hashlib.sha256(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            derivative_csv_sha256=hashlib.sha256(raw).hexdigest(),
            reconstructed_hours=672,
            decision="SOURCE_GAP_RECONSTRUCTED_DAILY_CHECKSUM_BOUND",
        )
        CSV.write_bytes(raw)
    except Exception as exc:
        CSV.unlink(missing_ok=True)
        receipt["error"] = type(exc).__name__ + ": " + str(exc)[:250]
    OUT.write_text(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "phase": 996, "decision": receipt["decision"],
        "reconstructed_hours": receipt.get("reconstructed_hours", 0),
        "error": receipt.get("error"),
        "derivative_csv_sha256": receipt.get("derivative_csv_sha256"),
    }, sort_keys=True))
    return 0 if receipt["decision"] == "SOURCE_GAP_RECONSTRUCTED_DAILY_CHECKSUM_BOUND" else 2


if __name__ == "__main__":
    raise SystemExit(run())
