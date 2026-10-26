"""I1 661-day ORIGINAL TRAIN option lifecycle-tape daily presence gate.

A necessary original-byte ingestion check, NEVER an execution, NAV, or ROI.
Precommitted in research/V99_R106_I1_FULL_LIFECYCLE_DAILY_TAPE_PREREG_20261026.md.
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

FIRST = date(2021, 12, 9)
LAST_EXCLUSIVE = date(2023, 10, 1)
DAYS = (LAST_EXCLUSIVE - FIRST).days
ASSETS = ("BTC", "ETH")
REQUIRED = {"exchange", "symbol", "timestamp", "local_timestamp",
            "bid_price", "ask_price", "bid_amount", "ask_amount"}
SCHEMA = "V99_I1_ORIGINAL_661_DAY_TRAIN_LIFECYCLE_TAPE_V1"


def _source_path(root: Path, filename: str) -> Path:
    if (not isinstance(filename, str) or Path(filename).name != filename
            or not (filename.endswith(".csv") or filename.endswith(".csv.gz"))):
        raise ValueError("UNSAFE_OR_NONCSV_SOURCE_PATH")
    p = root / filename
    if not p.is_file() or p.is_symlink():
        raise ValueError("MISSING_OR_SYMLINKED_ORIGINAL_DAY")
    return p


def _valid_put(row: dict, day: date) -> str | None:
    parts = row["symbol"].split("-")
    if len(parts) != 4 or parts[0] not in ASSETS or parts[3] != "P":
        return None
    try:
        expiry = datetime.strptime(parts[1].upper(), "%d%b%y").date()
        strike = float(parts[2])
        bid, ask, bid_size, ask_size = (
            float(row[k]) for k in ("bid_price", "ask_price", "bid_amount", "ask_amount"))
    except (ValueError, TypeError, OverflowError):
        return None
    if (not day < expiry <= day + timedelta(days=45)
            or not all(math.isfinite(x) and x > 0
                       for x in (strike, bid, ask, bid_size, ask_size))
            or bid >= ask):
        return None
    return parts[0]


def audit(root: Path) -> dict:
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("schema") != SCHEMA or manifest.get("venue") != "deribit"
            or type(manifest.get("fixture")) is not bool
            or manifest.get("train_start") != FIRST.isoformat()
            or manifest.get("train_end_exclusive") != LAST_EXCLUSIVE.isoformat()):
        raise ValueError("WRONG_OR_SEALED_TRAIN_MANIFEST")
    days = manifest.get("days")
    if not isinstance(days, list) or len(days) != DAYS:
        raise ValueError("INCOMPLETE_661_DAY_LIFECYCLE_ARCHIVE")
    expected = [(FIRST + timedelta(days=i)).isoformat() for i in range(DAYS)]
    if [d.get("date") for d in days] != expected:
        raise ValueError("MISSING_DUPLICATED_OR_REORDERED_TRAIN_DAY")
    if len({d.get("file") for d in days}) != DAYS:
        raise ValueError("REUSED_ORIGINAL_SOURCE_FILE")
    presence = {a: {} for a in ASSETS}
    daily = []
    total = 0
    for day_text, item in zip(expected, days):
        day = date.fromisoformat(day_text)
        if item.get("complete_capture") is not True:
            raise ValueError("SOURCE_DAY_NOT_DECLARED_COMPLETE")
        p = _source_path(root, item.get("file"))
        digest = hashlib.sha256()
        with p.open("rb") as raw:
            for chunk in iter(lambda: raw.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != item.get("sha256"):
            raise ValueError("ORIGINAL_DAILY_SOURCE_SHA256_MISMATCH")
        lower = int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp() * 1_000_000)
        upper = lower + 86_400_000_000
        seen = set()
        count = 0
        last_arrival = None
        opener = gzip.open if p.name.endswith(".gz") else open
        with opener(p, "rt", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not REQUIRED.issubset(reader.fieldnames or []):
                raise ValueError("ORIGINAL_DAILY_BOOK_COLUMNS_MISSING")
            for row in reader:
                count += 1
                if row["exchange"] != "deribit":
                    raise ValueError("WRONG_ORIGINAL_EXCHANGE")
                try:
                    event = int(row["timestamp"])
                    arrival = int(row["local_timestamp"])
                except (ValueError, TypeError) as exc:
                    raise ValueError("INVALID_ORIGINAL_SOURCE_CLOCK") from exc
                if not lower <= event <= arrival < upper:
                    raise ValueError("FUTURE_OR_OUTSIDE_DAY_QUOTE")
                if last_arrival is not None and arrival < last_arrival:
                    raise ValueError("OUT_OF_ORDER_CAPTURE")
                last_arrival = arrival
                asset = _valid_put(row, day)
                if asset is not None:
                    seen.add(asset)
        if count != item.get("rows"):
            raise ValueError("ORIGINAL_DAILY_ROW_COUNT_MISMATCH")
        total += count
        for asset in ASSETS:
            presence[asset][day_text] = asset in seen
        daily.append({"date": day_text, "BTC": "BTC" in seen,
                      "ETH": "ETH" in seen, "rows": count,
                      "sha256": digest.hexdigest()})
    mondays = []
    d = FIRST + timedelta(days=(7 - FIRST.weekday()) % 7)
    while d + timedelta(days=21) < LAST_EXCLUSIVE:
        mondays.append(d)
        d += timedelta(days=7)
    if len(mondays) != 91:
        raise ValueError("PREREG_MATURITY_SCHEDULE_CHANGED")
    weekly = []
    for monday in mondays:
        for asset in ASSETS:
            missing = [(monday + timedelta(days=j)).isoformat()
                       for j in range(22)
                       if not presence[asset][(monday + timedelta(days=j)).isoformat()]]
            weekly.append({"decision_utc": monday.isoformat(), "asset": asset,
                           "required_daily_marks": 22,
                           "missing_daily_marks": len(missing),
                           "first_missing_day": missing[0] if missing else None,
                           "necessary_daily_presence": not missing})
    complete = sum(w["necessary_daily_presence"] for w in weekly)
    return {"schema": "V99_I1_661_DAY_LIFECYCLE_DAILY_PRESENCE_REPORT_V1",
            "status": ("SYNTHETIC_FIXTURE_NOT_ECONOMICS" if manifest["fixture"]
                       else "SOURCE_DAILY_PRESENCE_ONLY_NOT_EXECUTION_CERTIFIED"),
            "fixture": manifest["fixture"], "days": DAYS, "original_rows": total,
            "asset_weeks": 182, "required_days_per_asset_week": 22,
            "asset_weeks_with_necessary_daily_presence": complete,
            "certified_complete_option_lifecycles": 0,
            "source_manifest_self_declared_not_vendor_certified": True,
            "native_fees_authenticated": False, "native_margin_authenticated": False,
            "size_aware_fills_authenticated": False, "economic_train_executed": False,
            "validation_opened": False, "holdout_opened": False,
            "orders_enabled": False, "promotion_authorized": False,
            "daily": daily, "weekly": weekly}


def main(root: str, output: str):
    report = audit(Path(root))
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "days": report["days"],
                      "asset_weeks": report["asset_weeks"],
                      "daily_presence_asset_weeks": report["asset_weeks_with_necessary_daily_presence"],
                      "certified_complete_option_lifecycles": 0,
                      "economic_train_executed": False, "promotion_authorized": False},
                     sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_lifecycle_daily_tape ROOT OUT_JSON")
    main(sys.argv[1], sys.argv[2])
