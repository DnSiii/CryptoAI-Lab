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
    if (manifest.get("schema") not in (
            "V99_I1_ORIGINAL_661_DAY_TRAIN_LIFECYCLE_TAPE_V1",
            "V99_I1_FIXED_28_35D_661_DAY_TRAIN_LIFECYCLE_TAPE_V1")
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
    # Recompute exact-contract continuity from independent original CSV reads.
    entries_monday = []
    m = START + timedelta(days=(7 - START.weekday()) % 7)
    while m + timedelta(days=28) < STOP:
        entries_monday.append(m)
        m += timedelta(days=7)
    assert len(entries_monday) == 90
    expiry_to_entries = {}
    for m in entries_monday:
        for tenor in range(28, 36):
            expiry = m + timedelta(days=tenor)
            if expiry < STOP:
                expiry_to_entries.setdefault(expiry, []).append(m)
    masks = {}
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
                if (row["exchange"] != "deribit" or not (0 <= venue <= arrival and low <= arrival < high)
                        or arrival < previous):
                    raise AssertionError("OUT_OF_ORDER_OR_FUTURE_ORIGINAL_RECEIPT")
                previous = arrival
                # Independent original-byte replay of five-minute event freshness.
                if arrival - venue > 300_000_000:
                    continue
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
                    for m in expiry_to_entries.get(expiry, ()):
                        if m <= d < expiry:
                            key = (m.isoformat(), parts[0], expiry.isoformat(), row["symbol"])
                            masks[key] = masks.get(key, 0) | (1 << (d - m).days)
        if n != entry.get("rows"):
            raise AssertionError("ORIGINAL_ROW_COUNT_FORGED")
        out.append({"date": stamp, **good, "rows": n, "sha256": sha})
    full = {}
    for (m, asset, expiry, symbol), bits in masks.items():
        days = (date.fromisoformat(expiry) - date.fromisoformat(m)).days
        if bits == (1 << days) - 1:
            key = (m, asset, expiry)
            full[key] = full.get(key, 0) + 1
    pairs = {(m, asset) for (m, asset, expiry), count in full.items() if count >= 2}
    return manifest, out, pairs


def verify(root: Path, report: dict):
    if (report.get("schema") != "V99_I1_661_DAY_LIFECYCLE_DAILY_PRESENCE_REPORT_V1"
            or report.get("days") != 661
            or report.get("certified_complete_option_lifecycles") != 0
            or report.get("daily_market_presence_only_not_same_contract_marks") is not True
            or report.get("same_contract_pair_still_not_executable_or_settlement_certified") is not True):
        raise AssertionError("FORGED_LIFECYCLE_COVERAGE_HEADER")
    for k in ("native_fees_authenticated", "native_margin_authenticated",
              "size_aware_fills_authenticated", "economic_train_executed",
              "validation_opened", "holdout_opened", "orders_enabled",
              "promotion_authorized"):
        if report.get(k) is not False:
            raise AssertionError("FORGED_ECONOMIC_CERTIFICATION")
    if report.get("source_manifest_self_declared_not_vendor_certified") is not True:
        raise AssertionError("FORGED_VENDOR_ATTESTATION")
    manifest, daily, continuous_pairs = _independent_days(Path(root))
    fixed = manifest["schema"] == "V99_I1_FIXED_28_35D_661_DAY_TRAIN_LIFECYCLE_TAPE_V1"
    if (report.get("source_scope") != ("FIXED_28_35D" if fixed else "LEGACY_21_45D")
            or report.get("asset_weeks") != (180 if fixed else 182)
            or report.get("required_days_per_asset_week") != (36 if fixed else 22)):
        raise AssertionError("FORGED_LIFECYCLE_COVERAGE_HEADER")
    expected_status = ("SYNTHETIC_FIXTURE_NOT_ECONOMICS" if manifest["fixture"]
                       else "SOURCE_DAILY_PRESENCE_ONLY_NOT_EXECUTION_CERTIFIED")
    if (report.get("status") != expected_status or report.get("fixture") != manifest["fixture"]
            or report.get("daily") != daily
            or report.get("original_rows") != sum(x["rows"] for x in daily)):
        raise AssertionError("FORGED_ORIGINAL_DAILY_PRESENCE")
    calendar = {x["date"]: x for x in daily}
    weekly = []
    day = START + timedelta(days=(7 - START.weekday()) % 7)
    while day + timedelta(days=28 if fixed else 21) < STOP:
        if fixed:
            last = min(day + timedelta(days=35), STOP - timedelta(days=1))
            count_days = (last - day).days + 1
        else:
            count_days = 22
        for asset in ("BTC", "ETH"):
            absent = [(day + timedelta(days=i)).isoformat()
                      for i in range(count_days)
                      if calendar[(day + timedelta(days=i)).isoformat()][asset] is False]
            weekly.append({"decision_utc": day.isoformat(), "asset": asset,
                           "required_daily_marks": count_days,
                           "missing_daily_marks": len(absent),
                           "first_missing_day": absent[0] if absent else None,
                           "necessary_daily_presence": len(absent) == 0,
                           "same_contract_pair_preexpiry_presence":
                           (day.isoformat(), asset) in continuous_pairs if fixed else False})
        day += timedelta(days=7)
    if len(weekly) != (180 if fixed else 182) or report.get("weekly") != weekly:
        raise AssertionError("FORGED_ORIGINAL_WEEKLY_COVERAGE")
    count = sum(x["necessary_daily_presence"] for x in weekly)
    if report.get("asset_weeks_with_necessary_daily_presence") != count:
        raise AssertionError("FORGED_ASSET_WEEK_COUNT")
    continuous = sum(x["same_contract_pair_preexpiry_presence"] for x in weekly)
    if report.get("asset_weeks_with_same_contract_pair_preexpiry_presence") != continuous:
        raise AssertionError("FORGED_SAME_CONTRACT_PAIR_CONTINUITY")
    return {"status": "INDEPENDENT_ORIGINAL_661_DAY_DAILY_PRESENCE_MATCH",
            "days": len(daily), "original_rows": sum(x["rows"] for x in daily),
            "necessary_daily_presence_asset_weeks": count,
            "same_contract_pair_preexpiry_asset_weeks": continuous,
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
