#!/usr/bin/env python3
"""V98 Phase997: fresh 100+28 mark ZIP and 100 funding ZIP source-only policy.

Exactly one preregistered exception: BTCUSDT Feb 2023 missing 24 monthly hours.
No historical PnL; no Phase797 modifications; no API mark attestation.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from phase797_official_mark_archive_attestor import (
    ASSETS, MONTHS, ROOT, STEP, BASE, native, audit, verify_month,
    conservative_rows, parse_zip,
)
from phase991_source_triangulation import (
    MONTH_NAME, authenticated_zip, fetch_day, TIMES,
)
from phase996_btc_feb_gap_resolution import reconcile, GAP

OUT = ROOT / "phase997_clean4_source_policy_receipt.json"
BOUNDS = ROOT / "phase997_clean4_conservative_funding_bounds_source_only.csv"
EXCEPTION = ("BTCUSDT", "2023-02")
MONTH_SHA = "f15d23370f252082d8741819800b82f62ac8bbc9001b53ab6abb5d65ccb3ed3d"
DERIVATIVE_SHA = "b0518f923587cea464abaa42a8bacf401ca65508f40be055cfdd53dd1b004597"
MANIFEST_SHA = "efbb721590f7a73126ed8357f8bc3f94944ab1691690ed51e5a160ff3a7d5f3f"


def canonical_derivative(monthly, day_rows):
    merged, overlap = reconcile(monthly, day_rows)
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator="\n").writerows(merged)
    raw = out.getvalue().encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != DERIVATIVE_SHA:
        raise PermissionError("PREREGISTERED_DERIVATIVE_SHA_DRIFT")
    with io.BytesIO() as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(MONTH_NAME[:-4] + ".csv", raw)
        rebuilt = stream.getvalue()
    bounds = parse_zip(rebuilt, MONTH_NAME, EXCEPTION[1])
    return bounds, overlap


def exceptional_month():
    _, monthly, sha = authenticated_zip(BASE, MONTH_NAME)
    if sha != MONTH_SHA:
        raise PermissionError("PREREGISTERED_MONTHLY_SHA_DRIFT")
    day_rows, day_sha = {}, {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch_day, day): day for day in range(1, 29)}
        for future in as_completed(futures):
            day, checked, mapped, digest = future.result()
            expected = TIMES[(day-1)*24:day*24]
            if checked["fault_count"] or set(mapped) != set(expected):
                raise ValueError("DAILY_ARCHIVE_INVALID_DAY_" + str(day))
            day_rows[day] = [mapped[t] for t in expected]
            day_sha[day] = digest
    bounds, overlap = canonical_derivative(monthly, day_rows)
    manifest = {
        "monthly_zip_sha256": sha,
        "daily_zip_sha256": {f"{day:02d}": day_sha[day] for day in range(1, 29)},
        "missing_utc": [datetime.fromtimestamp(t/1000, timezone.utc).isoformat()
                        for t in sorted(GAP)],
        "monthly_rows": 648, "daily_rows": 672, "inserted_daily_rows": 24,
        "overlap": overlap,
    }
    actual = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if actual != MANIFEST_SHA:
        raise PermissionError("PREREGISTERED_29_ZIP_MANIFEST_SHA_DRIFT")
    return bounds, sha, actual


def run():
    receipt = {
        "phase": 997, "decision": "QUARANTINE",
        "source_only": True, "historical_pnl_computed": False,
        "economic_clearance": False, "validation_2025_read": False,
        "holdout_accessed": False, "external_benchmarks_used": False,
        "api_mark_attested": False, "frozen_source_modified": False,
        "exception": "BTCUSDT 2023-02 24h vendor-daily checksum reconstruction",
    }
    BOUNDS.unlink(missing_ok=True)
    try:
        if len(ASSETS) != 4 or len(MONTHS) != 25 or MONTHS[0] != "2022-12" or MONTHS[-1] != "2024-12":
            raise ValueError("LOCKED_UNIVERSE_DRIFT")
        funding = {asset: audit(asset, native(asset)) for asset in ASSETS}
        if sum(x["archives"] for x in funding.values()) != 100 or sum(x["settlements"] for x in funding.values()) != 9144:
            raise ValueError("FUNDING_100_ARCHIVES_INCOMPLETE")
        marks = {}; mark_sha = {}; all_rows = []
        for asset in ASSETS:
            marks[asset] = {}; mark_sha[asset] = {}
            for month in MONTHS:
                if (asset, month) == EXCEPTION:
                    bounds, sha, manifest_sha = exceptional_month()
                    receipt["exception_manifest_sha256"] = manifest_sha
                else:
                    bounds, sha = verify_month(asset, month)
                if set(bounds) & set(marks[asset]):
                    raise ValueError("DUPLICATE_SETTLEMENT_MARK")
                marks[asset].update(bounds)
                mark_sha[asset][month] = sha
            all_rows.extend(conservative_rows(native(asset), marks[asset], asset))
        if len(all_rows) != 9144:
            raise ValueError("FUNDING_MARK_9144_COVERAGE_FAILURE")
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(("asset", "funding_slot_ms", "funding_time_ms", "funding_rate",
                         "mark_low", "mark_high", "conservative_mark"))
        writer.writerows(all_rows)
        raw = output.getvalue().encode("utf-8")
        receipt.update(
            decision="PASS_100_MARK_100_FUNDING_ONE_AUTHENTICATED_DAILY_GAP_SOURCE_ONLY",
            verified_mark_monthly_archives=100,
            verified_mark_daily_archives=28,
            verified_funding_monthly_archives=100,
            verified_asset_events=9144,
            vendor_archive_checksum_attested=True,
            mark_zip_manifest_sha256=hashlib.sha256(
                json.dumps(mark_sha, sort_keys=True).encode()
            ).hexdigest(),
            funding_manifest_sha256=hashlib.sha256(
                json.dumps(funding, sort_keys=True).encode()
            ).hexdigest(),
            bounds_csv_sha256=hashlib.sha256(raw).hexdigest(),
        )
        BOUNDS.write_bytes(raw)
    except Exception as exc:
        BOUNDS.unlink(missing_ok=True)
        receipt["reason"] = type(exc).__name__ + ": " + str(exc)[:300]
    OUT.write_text(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "phase": 997, "decision": receipt["decision"],
        "reason": receipt.get("reason"),
        "verified_asset_events": receipt.get("verified_asset_events", 0),
    }, sort_keys=True))
    return 0 if receipt["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(run())
