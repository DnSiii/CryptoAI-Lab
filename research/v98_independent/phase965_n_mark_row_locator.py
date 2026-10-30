#!/usr/bin/env python3
"""V98 Phase965: checksum-bound, source-only mark-candle discrepancy diagnosis.

Fixed BTCUSDT 2023-02, Binance USD-M monthly markPriceKlines. No PnL,
no gate bypass, no 2025+, no benchmark, no replacement of original rows.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from phase797_official_mark_archive_attestor import BASE, calendar_ms, download, parse_zip
from phase206_acquire_funding_archive import checksum_expected

ASSET = "BTCUSDT"
MONTH = "2023-02"
NAME = f"{ASSET}-1h-{MONTH}.zip"
OUT = Path(__file__).resolve().parent / "phase965_n_mark_row_locator_result.json"


def examine(raw):
    """Return all strict schema/geometry anomalies and nearby raw rows."""
    expected = calendar_ms(MONTH)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.namelist() != [NAME[:-4] + ".csv"]:
            return {"problem": "ZIP_MEMBERS", "members": archive.namelist()}
        with archive.open(NAME[:-4] + ".csv") as stream:
            rows = list(csv.reader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline="")))
    header = bool(rows and rows[0] and rows[0][0].strip().lower() == "open_time")
    data = rows[1:] if header else rows
    issues = []
    for i, row in enumerate(data):
        faults = []
        if len(row) != 12:
            faults.append("ROW_WIDTH")
        else:
            try:
                ts, close_ts = int(row[0]), int(row[6])
                o, h, l, c = (Decimal(x) for x in row[1:5])
                if i >= len(expected) or ts != expected[i]:
                    faults.append("OPEN_TIME")
                if close_ts != ts + 3599999:
                    faults.append("CLOSE_TIME")
                if not all(x.is_finite() for x in (o, h, l, c)):
                    faults.append("NONFINITE")
                if l <= 0:
                    faults.append("LOW_NONPOSITIVE")
                if l > min(o, c):
                    faults.append("LOW_ABOVE_OPEN_CLOSE")
                if h < max(o, c):
                    faults.append("HIGH_BELOW_OPEN_CLOSE")
                if h < l:
                    faults.append("HIGH_BELOW_LOW")
            except (ValueError, InvalidOperation, IndexError):
                faults.append("PARSE")
        if faults:
            issues.append({"index": i, "faults": faults, "row": row[:8],
                           "neighbors": [{"index": j, "row": data[j][:8]}
                                         for j in range(max(0, i-2), min(len(data), i+3))]})
    return {"expected_hours": len(expected), "actual_hours": len(data),
            "header": rows[0] if header else None,
            "issues_count": len(issues), "issues": issues[:20],
            "issues_truncated": len(issues) > 20}


def api_crosscheck(issues):
    """Read-only independent Binance API observation; failure never repairs source."""
    if not issues:
        return {"status": "SKIPPED_NO_ISSUE"}
    row = issues[0]["row"]
    try:
        t = int(row[0])
        if not calendar_ms(MONTH)[0] <= t <= calendar_ms(MONTH)[-1]:
            return {"status": "SKIPPED_OUTSIDE_MONTH"}
        query = urllib.parse.urlencode({"symbol": ASSET, "interval": "1h",
                                        "startTime": t-3600000, "endTime": t+3600000, "limit": 3})
        url = "https://fapi.binance.com/fapi/v1/markPriceKlines?" + query
        request = urllib.request.Request(url, headers={"User-Agent": "V98-Independent-Source-Audit/1.0"})
        with urllib.request.urlopen(request, timeout=12) as response:
            if response.status != 200 or response.geturl() != url:
                return {"status": "UNTRUSTED_REDIRECT_OR_STATUS"}
            payload = response.read(50000)
        parsed = json.loads(payload)
        if not isinstance(parsed, list):
            return {"status": "UNEXPECTED_SCHEMA"}
        return {"status": "API_OBSERVATION_ONLY", "rows": [r[:7] for r in parsed]}
    except Exception as exc:
        return {"status": "API_UNAVAILABLE", "reason": type(exc).__name__ + ": " + str(exc)[:140]}


def run():
    result = {"phase": 965, "asset": ASSET, "month": MONTH,
              "source_only": True, "historical_pnl_computed": False,
              "validation_2025_read": False, "holdout_accessed": False,
              "external_benchmarks_used": False, "gate_relaxed": False,
              "decision": "BLOCKED_UNVERIFIED_MARK_SOURCE"}
    try:
        url = f"{BASE}/{ASSET}/1h/{NAME}"
        expected_sha = checksum_expected(download(url + ".CHECKSUM"), NAME)
        raw = download(url)
        actual_sha = hashlib.sha256(raw).hexdigest()
        result.update(official_url=url, expected_sha256=expected_sha,
                      actual_sha256=actual_sha)
        if expected_sha != actual_sha:
            raise ValueError("OFFICIAL_ARCHIVE_SHA_MISMATCH")
        result["diagnostic"] = examine(raw)
        try:
            parse_zip(raw, NAME, MONTH)
            result["strict_phase797_parser"] = "PASS"
        except Exception as exc:
            result["strict_phase797_parser"] = type(exc).__name__ + ": " + str(exc)
        result["independent_api"] = api_crosscheck(result["diagnostic"].get("issues", []))
        result["decision"] = ("QUARANTINE_CHECKSUM_VALID_MARK_ANOMALY"
                              if result["diagnostic"].get("issues_count", 0)
                              else "NO_ROW_GEOMETRY_ANOMALY")
    except Exception as exc:
        result["reason"] = type(exc).__name__ + ": " + str(exc)[:250]
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] != "BLOCKED_UNVERIFIED_MARK_SOURCE" else 2


if __name__ == "__main__":
    raise SystemExit(run())
