#!/usr/bin/env python3
"""V98 Phase1000: strict four-asset Feb 24 daily-source gap attestation, no PnL.

96 unaffected monthly ZIPs pass unchanged Phase797; four fixed Feb ZIPs are
reconstructed from vendor-checksummed 28 daily ZIPs each. No frozen edits.
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
    ASSETS, MONTHS, BASE, ROOT, native, audit, verify_month,
    conservative_rows, parse_zip, download,
)
from phase206_acquire_funding_archive import checksum_expected
from phase991_source_triangulation import TIMES, inspect
from phase996_btc_feb_gap_resolution import reconcile, GAP

OUT = ROOT / "phase1000_four_asset_source_policy_receipt.json"
BOUNDS = ROOT / "phase1000_four_asset_conservative_bounds_source_only.csv"
MONTH_PINS = {
    "BTCUSDT": "f15d23370f252082d8741819800b82f62ac8bbc9001b53ab6abb5d65ccb3ed3d",
    "ETHUSDT": "47b99057e2ea8bda8a6d266a34066b8c23954c4b1fb2a21d29f3697b2f69358d",
    "BNBUSDT": "8e34d717980fd6e541ecb201961d8c2a4f55b3808a669282125b2e31afa72ccc",
    "SOLUSDT": "2bb2d49cac17d9b397811c17e5a23a6ee79b30c7c666a997eee340828b999845",
}
DAILY_BASE = "https://data.binance.vision/data/futures/um/daily/markPriceKlines"


def official_rows(base, asset, name):
    url = f"{base}/{asset}/1h/{name}"
    expected = checksum_expected(download_from(base, url + ".CHECKSUM"), name)
    raw = download_from(base, url)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected:
        raise ValueError("VENDOR_CHECKSUM_MISMATCH_" + name)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.namelist() != [name[:-4] + ".csv"]:
            raise ValueError("ZIP_MEMBER_MISMATCH_" + name)
        with archive.open(name[:-4] + ".csv") as stream:
            rows = list(csv.reader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline="")))
    if rows and rows[0] and rows[0][0].strip().lower() == "open_time":
        header = tuple(v.strip().lower() for v in rows.pop(0))
        if len(header) != 12 or header[:5] != ("open_time", "open", "high", "low", "close") or header[6] != "close_time":
            raise ValueError("INVALID_VENDOR_CSV_HEADER")
    return rows, digest


def download_from(base, url):
    if not url.startswith(base + "/") or not (url.endswith(".zip") or url.endswith(".zip.CHECKSUM")):
        raise ValueError("FORBIDDEN_OFFICIAL_SOURCE")
    if base == BASE:
        return download(url)
    # The daily source is restricted to the official USD-M markPriceKlines host/path.
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "V98-Independent-Phase1000/1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError("DAILY_SOURCE_REDIRECT_OR_STATUS")
        raw = response.read(10_000_001)
    if len(raw) > 10_000_000:
        raise ValueError("DAILY_SOURCE_TOO_LARGE")
    return raw


def exceptional_month(asset):
    name = f"{asset}-1h-2023-02.zip"
    monthly, monthly_sha = official_rows(BASE, asset, name)
    if monthly_sha != MONTH_PINS[asset]:
        raise PermissionError("PREREGISTERED_MONTH_SHA_DRIFT_" + asset)
    daily, day_sha = {}, {}
    def one(day):
        day_name = f"{asset}-1h-2023-02-{day:02d}.zip"
        rows, sha = official_rows(DAILY_BASE, asset, day_name)
        expected = TIMES[(day-1)*24:day*24]
        check, mapped = inspect(rows, expected)
        if check["fault_count"] or set(mapped) != set(expected):
            raise ValueError("DAILY_GEOMETRY_OR_COVERAGE_" + asset + "_" + str(day))
        return day, [mapped[t] for t in expected], sha
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(one, day) for day in range(1, 29)]
        for future in as_completed(futures):
            day, rows, sha = future.result()
            daily[day] = rows
            day_sha[day] = sha
    merged, overlap = reconcile(monthly, daily)
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(merged)
    raw = output.getvalue().encode("utf-8")
    derivative_sha = hashlib.sha256(raw).hexdigest()
    if asset == "BTCUSDT" and derivative_sha != "b0518f923587cea464abaa42a8bacf401ca65508f40be055cfdd53dd1b004597":
        raise PermissionError("PHASE996_BTC_DERIVATIVE_DRIFT")
    with io.BytesIO() as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(name[:-4] + ".csv", raw)
        reconstructed_zip = stream.getvalue()
    bounds = parse_zip(reconstructed_zip, name, "2023-02")
    manifest = {
        "monthly_zip_sha256": monthly_sha,
        "daily_zip_sha256": {f"{day:02d}": day_sha[day] for day in range(1, 29)},
        "missing_utc": [datetime.fromtimestamp(t/1000, timezone.utc).isoformat() for t in sorted(GAP)],
        "monthly_rows": 648, "daily_rows": 672, "inserted_daily_rows": 24,
        "overlap": overlap,
        "derivative_csv_sha256": derivative_sha,
    }
    return bounds, monthly_sha, manifest


def run():
    receipt = {
        "phase": 1000, "decision": "QUARANTINE", "source_only": True,
        "historical_pnl_computed": False, "economic_clearance": False,
        "validation_2025_read": False, "holdout_accessed": False,
        "external_benchmarks_used": False, "api_mark_attested": False,
        "source_substitution_authorized": False, "frozen_source_modified": False,
    }
    BOUNDS.unlink(missing_ok=True)
    current = None
    try:
        if len(ASSETS) != 4 or set(ASSETS) != set(MONTH_PINS) or len(MONTHS) != 25 or MONTHS[0] != "2022-12" or MONTHS[-1] != "2024-12":
            raise ValueError("LOCKED_CLEAN4_CALENDAR_DRIFT")
        funding = {asset: audit(asset, native(asset)) for asset in ASSETS}
        if sum(v["archives"] for v in funding.values()) != 100 or sum(v["settlements"] for v in funding.values()) != 9144:
            raise ValueError("FUNDING_SOURCE_NOT_COMPLETE")
        mark_shas, exception_manifests, rows = {}, {}, []
        for asset in ASSETS:
            mark_shas[asset] = {}
            marks = {}
            for month in MONTHS:
                current = asset + "/" + month
                if month == "2023-02":
                    block, sha, manifest = exceptional_month(asset)
                    exception_manifests[asset] = manifest
                else:
                    block, sha = verify_month(asset, month)
                if set(block) & set(marks):
                    raise ValueError("DUPLICATE_MARK_SETTLEMENT")
                marks.update(block)
                mark_shas[asset][month] = sha
            rows.extend(conservative_rows(native(asset), marks, asset))
        if len(rows) != 9144:
            raise ValueError("9144_SETTLEMENTS_NOT_ATTESTED")
        out = io.StringIO(newline="")
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(("asset", "funding_slot_ms", "funding_time_ms", "funding_rate",
                         "mark_low", "mark_high", "conservative_mark"))
        writer.writerows(rows)
        raw = out.getvalue().encode("utf-8")
        receipt.update(
            decision="PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY",
            verified_mark_monthly_archives=100, verified_mark_daily_archives=112,
            verified_funding_monthly_archives=100, verified_asset_events=9144,
            vendor_archive_checksum_attested=True,
            exception_manifests=exception_manifests,
            mark_zip_manifest_sha256=hashlib.sha256(
                json.dumps(mark_shas, sort_keys=True).encode()
            ).hexdigest(),
            funding_manifest_sha256=hashlib.sha256(
                json.dumps(funding, sort_keys=True).encode()
            ).hexdigest(),
            bounds_csv_sha256=hashlib.sha256(raw).hexdigest(),
        )
        BOUNDS.write_bytes(raw)
    except Exception as exc:
        BOUNDS.unlink(missing_ok=True)
        receipt["failed_at"] = current
        receipt["reason"] = type(exc).__name__ + ": " + str(exc)[:300]
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "phase": 1000, "decision": receipt["decision"],
        "failed_at": receipt.get("failed_at"),
        "reason": receipt.get("reason"),
        "verified_asset_events": receipt.get("verified_asset_events", 0),
    }, sort_keys=True))
    return 0 if receipt["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(run())
