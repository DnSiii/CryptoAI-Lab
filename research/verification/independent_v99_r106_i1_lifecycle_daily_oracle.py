"""Independent original-byte 661-day I1 lifecycle presence oracle.

No import from primary lifecycle module. No economic replay or fill inference.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

START = date(2021, 12, 9)
STOP = date(2023, 10, 1)
FIELDS = ("exchange", "symbol", "timestamp", "local_timestamp",
          "bid_price", "ask_price", "bid_amount", "ask_amount")


def _independent_days(root: Path):
    manifest = json.loads((root / "manifest.json").read_bytes())
    if (manifest.get("schema") != "V99_I1_ORIGINAL_661_DAY_TRAIN_LIFECYCLE_TAPE_V1"
            or manifest.get("venue") != "deribit"
            or type(manifest.get("fixture")) is not bool
            or manifest.get("train_start") != START.isoformat()
            or manifest.get("train_end_exclusive") != STOP.isoformat()):
        raise AssertionError("FORGED_OR_OUTSIDE_TRAIN_SOURCE")
    required = [(START + timedelta(days=i)).isoformat() for i in range((STOP - START).days)]
    entries = manifest.get("days")
    if not isinstance(entries, list) or len(entries) != len(required):
        raise AssertionError("MISSING_661_DAY_ARCHIVE")
    if [entry.get("date") for entry in entries] != required:
        raise AssertionError("REORDERED_OR_MISSING_ORIGINAL_DAY")
    filenames = [e.get("file") for e in entries]
    if len(set(filenames)) != len(required):
        raise AssertionError("REUSED_SOURCE_DAY")
    out = []
    for stamp, entry in zip(required, entries):
        filename = entry.get("file")
        if (not isinstance(filename, str) or Path(filename).name != filename
                or not filename.endswith((".csv", ".csv.gz"))
                or entry.get("complete_capture") is not True):
            raise AssertionError("UNSAFE_OR_UNATTESTED_ORIGINAL_DAY")
        p = root / filename
        if not p.is_file() or p.is_symlink():
            raise AssertionError("MISSING_OR_SYMLINKED_SOURCE")
        digest = hashlib.sha256()
        with p.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        sha = digest.hexdigest()
        if sha != entry.get("sha256"):
            raise AssertionError("ORIGINAL_SOURCE_MUTATION")
        d = date.fromisoformat(stamp)
        low = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1_000_000)
        high = low + 86_400_000_000
        good = {"BTC": False, "ETH": False}
        previous = -1
        n = 0
        reader = gzip.open if filename.endswith(".gz") else open
        with reader(p, "rt", newline="", encoding="utf-8") as stream:
            rows = csv.DictReader(stream)
            if not set(FIELDS).issubset(rows.fieldnames or []):
                raise AssertionError("ORIGINAL_COLUMNS_MISSING")
            for row in rows:
                n += 1
                try:
                    arrival, venue = int(row["local_timestamp"]), int(row["timestamp"])
                except (ValueError, TypeError) as exc:
                    raise AssertionError("INVALID_CLOCK") from exc
                if (row["exchange"] != "deribit" or not low <= venue <= arrival < high
                        or arrival < previous):
                    raise AssertionError("OUT_OF_ORDER_OR_FUTURE_ORIGINAL_RECEIPT")
                previous = arrival
                parts = row["symbol"].split("-")
                if len(parts) != 4 or parts[0] not in good or parts[3] != "P":
                    continue
                try:
                    expiry = datetime.strptime(parts[1].upper(), "%d%b%y").date()
                    nums = [float(parts[2])] + [float(row[k]) for k in
                        ("bid_price", "ask_price", "bid_amount", "ask_amount")]
                except (ValueError, TypeError, OverflowError):
                    continue
                if (d < expiry <= d + timedelta(days=45)
                        and all(math.isfinite(x) and x > 0 for x in nums)
                        and nums[1] < nums[2]):
                    good[parts[0]] = True
        if n != entry.get("rows"):
            raise AssertionError("ORIGINAL_ROW_COUNT_FORGED")
        out.append({"date": stamp, **good, "rows": n, "sha256": sha})
    return manifest, out


def verify(root: Path, report: dict):
    if (report.get("schema") != "V99_I1_661_DAY_LIFECYCLE_DAILY_PRESENCE_REPORT_V1"
            or report.get("days") != 661 or report.get("asset_weeks") != 182
            or report.get("required_days_per_asset_week") != 22
            or report.get("certified_complete_option_lifecycles") != 0):
        raise AssertionError("FORGED_LIFECYCLE_COVERAGE_HEADER")
    for k in ("native_fees_authenticated", "native_margin_authenticated",
              "size_aware_fills_authenticated", "economic_train_executed",
              "validation_opened", "holdout_opened", "orders_enabled",
              "promotion_authorized"):
        if report.get(k) is not False:
            raise AssertionError("FORGED_ECONOMIC_CERTIFICATION")
    if report.get("source_manifest_self_declared_not_vendor_certified") is not True:
        raise AssertionError("FORGED_VENDOR_ATTESTATION")
    manifest, daily = _independent_days(Path(root))
    expected_status = ("SYNTHETIC_FIXTURE_NOT_ECONOMICS" if manifest["fixture"]
                       else "SOURCE_DAILY_PRESENCE_ONLY_NOT_EXECUTION_CERTIFIED")
    if (report.get("status") != expected_status or report.get("fixture") != manifest["fixture"]
            or report.get("daily") != daily
            or report.get("original_rows") != sum(x["rows"] for x in daily)):
        raise AssertionError("FORGED_ORIGINAL_DAILY_PRESENCE")
    calendar = {x["date"]: x for x in daily}
    weekly = []
    day = START + timedelta(days=(7 - START.weekday()) % 7)
    while day + timedelta(days=21) < STOP:
        for asset in ("BTC", "ETH"):
            absent = [(day + timedelta(days=i)).isoformat()
                      for i in range(22)
                      if calendar[(day + timedelta(days=i)).isoformat()][asset] is False]
            weekly.append({"decision_utc": day.isoformat(), "asset": asset,
                           "required_daily_marks": 22, "missing_daily_marks": len(absent),
                           "first_missing_day": absent[0] if absent else None,
                           "necessary_daily_presence": len(absent) == 0})
        day += timedelta(days=7)
    if len(weekly) != 182 or report.get("weekly") != weekly:
        raise AssertionError("FORGED_ORIGINAL_WEEKLY_COVERAGE")
    count = sum(x["necessary_daily_presence"] for x in weekly)
    if report.get("asset_weeks_with_necessary_daily_presence") != count:
        raise AssertionError("FORGED_ASSET_WEEK_COUNT")
    return {"status": "INDEPENDENT_ORIGINAL_661_DAY_DAILY_PRESENCE_MATCH",
            "days": len(daily), "original_rows": sum(x["rows"] for x in daily),
            "necessary_daily_presence_asset_weeks": count,
            "certified_complete_option_lifecycles": 0,
            "economic_train_executed": False, "promotion_authorized": False}


def main(root, report_path):
    result = verify(Path(root), json.loads(Path(report_path).read_text(encoding="utf-8")))
    out = Path(report_path).parent / "i1_lifecycle_daily_independent_oracle.json"
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_lifecycle_daily_oracle ROOT REPORT_JSON")
    main(*sys.argv[1:])
