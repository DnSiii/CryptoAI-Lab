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
FIXED_SCHEMA = "V99_I1_FIXED_28_35D_661_DAY_TRAIN_LIFECYCLE_TAPE_V1"


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
    fixed_tenor = manifest.get("schema") == FIXED_SCHEMA
    if (manifest.get("schema") not in (SCHEMA, FIXED_SCHEMA)
            or manifest.get("venue") != "deribit"
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
    # Exact-contract continuity is only a necessary pre-expiry quote screen.
    # A changing option every day must NEVER count as a held option lifecycle.
    entry_mondays = []
    monday = FIRST + timedelta(days=(7 - FIRST.weekday()) % 7)
    while monday + timedelta(days=28) < LAST_EXCLUSIVE:
        entry_mondays.append(monday)
        monday += timedelta(days=7)
    if len(entry_mondays) != 90:
        raise ValueError("PREREG_FIXED_ENTRY_SCHEDULE_CHANGED")
    eligible_expiries = {}
    for monday in entry_mondays:
        for tenor in range(28, 36):
            expiry = monday + timedelta(days=tenor)
            if expiry < LAST_EXCLUSIVE:
                eligible_expiries.setdefault(expiry, []).append(monday)
    # Sunday pre-decision quotes are the ONLY causal source for Monday 00:00.
    # Daily Monday-after-open quotes cannot certify an entry at midnight.
    sunday_to_entry = {m - timedelta(days=1): m for m in entry_mondays}
    latest_entry_quote = {}
    contract_day_masks = {}
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
                if not (0 <= event <= arrival and lower <= arrival < upper):
                    raise ValueError("FUTURE_OR_OUTSIDE_DAY_QUOTE")
                if last_arrival is not None and arrival < last_arrival:
                    raise ValueError("OUT_OF_ORDER_CAPTURE")
                last_arrival = arrival
                # Vendor files are partitioned by LOCAL arrival date, not event date.
                # Older venue events remain original rows but cannot certify a fresh mark.
                asset = _valid_put(row, day) if arrival - event <= 300_000_000 else None
                if asset is not None:
                    seen.add(asset)
                    # Capture the LAST valid as-of Sunday quote for each exact
                    # contract. Strictly earlier than Monday 00:00, <=300s old.
                    entry = sunday_to_entry.get(day)
                    if entry is not None:
                        decision = int(datetime(entry.year, entry.month, entry.day,
                                                tzinfo=timezone.utc).timestamp() * 1_000_000)
                        entry_expiry = datetime.strptime(
                            row["symbol"].split("-")[1].upper(), "%d%b%y").date()
                        if (decision - 300_000_000 <= event <= arrival < decision
                                and 28 <= (entry_expiry - entry).days <= 35
                                and entry_expiry < LAST_EXCLUSIVE):
                            key = (entry.isoformat(), asset, entry_expiry.isoformat(),
                                   row["symbol"])
                            latest_entry_quote[key] = (event, arrival)
                    expiry = datetime.strptime(row["symbol"].split("-")[1].upper(),
                                               "%d%b%y").date()
                    for entry in eligible_expiries.get(expiry, ()):
                        if entry <= day < expiry:
                            key = (entry.isoformat(), asset, expiry.isoformat(), row["symbol"])
                            contract_day_masks[key] = (contract_day_masks.get(key, 0)
                                                       | (1 << (day - entry).days))
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
    minimum_tenor = 28 if fixed_tenor else 21
    while d + timedelta(days=minimum_tenor) < LAST_EXCLUSIVE:
        mondays.append(d)
        d += timedelta(days=7)
    if len(mondays) != (90 if fixed_tenor else 91):
        raise ValueError("PREREG_MATURITY_SCHEDULE_CHANGED")
    # Two distinct put strikes, SAME expiry and SAME original contract
    # continuously observed on every day until expiry (exclusive).
    # No delivery index or actual exit is inferred from this necessary check.
    full_contracts = {}
    full_contract_symbols = {}
    for (entry, asset, expiry, symbol), mask in contract_day_masks.items():
        required_mask = (1 << (date.fromisoformat(expiry) -
                               date.fromisoformat(entry)).days) - 1
        if mask == required_mask:
            key = (entry, asset, expiry)
            full_contracts[key] = full_contracts.get(key, 0) + 1
            full_contract_symbols.setdefault(key, []).append(symbol)
    causal_pairs = set()
    for (entry, asset, expiry), symbols in full_contract_symbols.items():
        for i, a in enumerate(symbols):
            qa = latest_entry_quote.get((entry, asset, expiry, a))
            if qa is None:
                continue
            for b in symbols[i + 1:]:
                qb = latest_entry_quote.get((entry, asset, expiry, b))
                if (qb is not None and abs(qa[0] - qb[0]) <= 1_000_000
                        and abs(qa[1] - qb[1]) <= 1_000_000):
                    causal_pairs.add((entry, asset))
                    break
            if (entry, asset) in causal_pairs:
                break
    continuous_pairs = {
        (entry, asset) for (entry, asset, expiry), n in full_contracts.items()
        if n >= 2
    }
    weekly = []
    for monday in mondays:
        # This is a WEAK market-presence screen, not a contract-specific mark.
        # Never require a sealed date, even for the longest permitted tenor.
        final_day = (min(monday + timedelta(days=35),
                         LAST_EXCLUSIVE - timedelta(days=1))
                     if fixed_tenor else monday + timedelta(days=21))
        required = (final_day - monday).days + 1
        for asset in ASSETS:
            missing = [(monday + timedelta(days=j)).isoformat()
                       for j in range(required)
                       if not presence[asset][(monday + timedelta(days=j)).isoformat()]]
            weekly.append({"decision_utc": monday.isoformat(), "asset": asset,
                           "required_daily_marks": required,
                           "missing_daily_marks": len(missing),
                           "first_missing_day": missing[0] if missing else None,
                           "necessary_daily_presence": not missing,
                           "same_contract_pair_preexpiry_presence":
                           (monday.isoformat(), asset) in continuous_pairs
                           if fixed_tenor else False,
                           "causal_entry_and_same_contract_pair_presence":
                           (monday.isoformat(), asset) in causal_pairs
                           if fixed_tenor else False})
    complete = sum(w["necessary_daily_presence"] for w in weekly)
    return {"schema": "V99_I1_661_DAY_LIFECYCLE_DAILY_PRESENCE_REPORT_V1",
            "source_scope": "FIXED_28_35D" if fixed_tenor else "LEGACY_21_45D",
            "daily_market_presence_only_not_same_contract_marks": True,
            "status": ("SYNTHETIC_FIXTURE_NOT_ECONOMICS" if manifest["fixture"]
                       else "SOURCE_DAILY_PRESENCE_ONLY_NOT_EXECUTION_CERTIFIED"),
            "fixture": manifest["fixture"], "days": DAYS, "original_rows": total,
            "asset_weeks": 2*len(mondays),
            "required_days_per_asset_week": 36 if fixed_tenor else 22,
            "asset_weeks_with_necessary_daily_presence": complete,
            "asset_weeks_with_same_contract_pair_preexpiry_presence":
            sum(w["same_contract_pair_preexpiry_presence"] for w in weekly),
            "asset_weeks_with_causal_entry_and_same_contract_pair_presence":
            sum(w["causal_entry_and_same_contract_pair_presence"] for w in weekly),
            "same_contract_pair_still_not_executable_or_settlement_certified": True,
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
                      "same_contract_pair_preexpiry_asset_weeks":
                      report["asset_weeks_with_same_contract_pair_preexpiry_presence"],
                      "causal_entry_and_same_contract_asset_weeks":
                      report["asset_weeks_with_causal_entry_and_same_contract_pair_presence"],
                      "certified_complete_option_lifecycles": 0,
                      "economic_train_executed": False, "promotion_authorized": False},
                     sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_lifecycle_daily_tape ROOT OUT_JSON")
    main(sys.argv[1], sys.argv[2])
