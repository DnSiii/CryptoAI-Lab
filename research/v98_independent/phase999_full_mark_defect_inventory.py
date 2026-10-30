#!/usr/bin/env python3
"""V98 Phase999: 100-month official mark ZIP source-only defect inventory.

Never repairs a source, reads 2025+, computes PnL, or changes Phase797.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from phase797_official_mark_archive_attestor import (
    ASSETS, MONTHS, BASE, ROOT, download, calendar_ms, parse_zip,
)
from phase206_acquire_funding_archive import checksum_expected

OUT = ROOT / "phase999_full_mark_defect_inventory_result.json"


def analyze(rows, expected):
    observed = {}
    duplicates = []
    malformed = []
    for index, row in enumerate(rows):
        try:
            if len(row) != 12:
                raise ValueError("ROW_WIDTH")
            ts, close_ts = int(row[0]), int(row[6])
            op, hi, lo, cl = (Decimal(v) for v in row[1:5])
            if ts in observed:
                duplicates.append(ts)
            observed[ts] = row
            if close_ts != ts + 3599999 or not all(x.is_finite() for x in (op, hi, lo, cl)) or lo <= 0 or lo > min(op,cl) or hi < max(op,cl):
                raise ValueError("CLOSE_TIME_OR_OHLC_GEOMETRY")
        except (ValueError, InvalidOperation, IndexError, TypeError) as exc:
            malformed.append({"index": index, "fault": str(exc)[:100], "raw_first7": row[:7]})
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    def utc(t):
        return datetime.fromtimestamp(t / 1000, timezone.utc).isoformat()
    return {
        "rows": len(rows), "expected_rows": len(expected),
        "missing_hours": len(missing), "missing_utc": [utc(t) for t in missing[:100]],
        "extra_hours": len(extra), "extra_utc": [utc(t) for t in extra[:20]],
        "duplicate_count": len(duplicates), "duplicate_utc": [utc(t) for t in duplicates[:20]],
        "malformed_count": len(malformed), "first_malformed": malformed[:5],
    }


def inspect_month(asset, month):
    name = f"{asset}-1h-{month}.zip"
    url = f"{BASE}/{asset}/1h/{name}"
    expected_sha = checksum_expected(download(url + ".CHECKSUM"), name)
    raw = download(url)
    sha = hashlib.sha256(raw).hexdigest()
    if sha != expected_sha:
        raise ValueError("VENDOR_SHA256_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.namelist() != [name[:-4] + ".csv"]:
            raise ValueError("ZIP_MEMBER_MISMATCH")
        with archive.open(name[:-4] + ".csv") as stream:
            rows = list(csv.reader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline="")))
    if rows and rows[0] and rows[0][0].strip().lower() == "open_time":
        rows.pop(0)
    diagnostic = analyze(rows, calendar_ms(month))
    try:
        parse_zip(raw, name, month)
        diagnostic["unchanged_phase797_parser"] = "PASS"
    except Exception as exc:
        diagnostic["unchanged_phase797_parser"] = type(exc).__name__ + ": " + str(exc)[:160]
    diagnostic["vendor_zip_sha256"] = sha
    return diagnostic


def run():
    receipt = {
        "phase": 999, "decision": "INVENTORY_INCOMPLETE",
        "source_only": True, "historical_pnl_computed": False,
        "economic_clearance": False, "source_substitution_authorized": False,
        "validation_2025_read": False, "holdout_accessed": False,
        "external_benchmarks_used": False, "months": {},
    }
    work = [(a, m) for a in ASSETS for m in MONTHS]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(inspect_month, a, m): (a,m) for a,m in work}
        for future in as_completed(futures):
            a,m = futures[future]
            try:
                receipt["months"][a+"/"+m] = future.result()
            except Exception as exc:
                receipt["months"][a+"/"+m] = {"error": type(exc).__name__ + ": " + str(exc)[:220]}
    failures = sorted(k for k,v in receipt["months"].items() if v.get("unchanged_phase797_parser") != "PASS")
    errors = sorted(k for k,v in receipt["months"].items() if "error" in v)
    receipt.update(
        checked=len(receipt["months"]), failed_months=failures,
        download_or_checksum_errors=errors,
        decision="SOURCE_DEFECTS_FOUND_NO_ECONOMICS" if len(receipt["months"])==100 and not errors else "INVENTORY_INCOMPLETE",
    )
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "phase": 999, "decision": receipt["decision"],
        "checked": receipt["checked"],
        "failed_months": failures,
        "errors": errors,
    }, sort_keys=True))
    return 0 if len(receipt["months"]) == 100 and not errors else 2


if __name__ == "__main__":
    raise SystemExit(run())
