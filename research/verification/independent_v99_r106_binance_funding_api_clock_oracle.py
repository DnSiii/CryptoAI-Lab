"""Independent replay of original Binance publisher ZIP and saved first-party API JSON.

No imports from primary clock-binding implementation; no economics.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from research.verification.independent_v99_r106_binance_funding_original_train_oracle import verify as verify_publisher

START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
STEP = 8 * 3600 * 1000
WINDOW = 90 * 24 * 3600 * 1000
EDGES = [START + h * 3600000 for h in (0, 3172, 6345, 9518, 12691, 15864)]
SLOTS = set(range(START, END, STEP))
SYMBOLS = ("BTCUSDT", "ETHUSDT")
MONTHS = [f"{y}-{m:02d}" for y in (2021, 2022, 2023) for m in range(1, 13)
          if (y, m) >= (2021, 12) and (y, m) <= (2023, 9)]
SCHEMA = "V99_R106_BINANCE_FUNDING_API_ARCHIVE_CLOCK_CORROBORATION_V1"


def replay(root: Path):
    root = Path(root)
    # Separate existing original-byte oracle verifies all 44 original publisher checksums.
    verify_publisher(root)
    report = json.loads((root / "binance_funding_api_clock_source_only.json").read_bytes())
    if report.get("schema") != SCHEMA or report.get("scope") != "[2021-12-09,2023-10-01)_TRAIN_ONLY":
        raise ValueError("ORACLE_SCOPE_OR_SCHEMA")
    if (report.get("original_strict_exact_clock_gate_unchanged") is not True
            or report.get("original_strict_exact_clock_observed_per_asset") != 821):
        raise ValueError("ORACLE_FALSE_ORIGINAL_EXACT_CLOCK")
    for k in ("no_private_account_settlement", "no_economics", "no_promotion",
              "no_validation", "no_holdout", "no_paper", "no_orders"):
        if report.get(k) is not True:
            raise ValueError("ORACLE_FALSE_PERMISSION_" + k)
    if set(report.get("assets", {})) != set(SYMBOLS):
        raise ValueError("ORACLE_ASSET_SET")
    expected_api_files = set()
    for symbol in SYMBOLS:
        rows = []
        for month in MONTHS:
            name = f"{symbol}-fundingRate-{month}.zip"
            path = root / "raw_ephemeral" / name
            if not path.exists():
                # Primary explicitly reports missing original data, no false success.
                if "error" not in report["assets"][symbol]:
                    raise ValueError("ORACLE_UNREPORTED_ORIGINAL_MISSING")
                rows = None
                break
            with zipfile.ZipFile(path) as z:
                members = [m for m in z.infolist() if not m.is_dir()]
                if len(members) != 1 or not members[0].filename.endswith(".csv"):
                    raise ValueError("ORACLE_ARCHIVE_FORMAT")
                raw = z.read(members[0])
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            if not {"calc_time", "funding_interval_hours", "last_funding_rate"}.issubset(reader.fieldnames or []):
                raise ValueError("ORACLE_ARCHIVE_SCHEMA")
            for item in reader:
                ts = int(item["calc_time"])
                iv = float(item["funding_interval_hours"])
                rate = float(item["last_funding_rate"])
                if START <= ts < END and iv == 8:
                    rows.append((ts, rate))
        api_rows = []
        saved = 0
        expected_windows = 0
        for start in range(START, END, WINDOW):
            expected_windows += 1
            end = min(start + WINDOW, END) - 1
            name = f"{symbol}-window-{expected_windows:02d}.json"
            path = root / "api_raw_ephemeral" / name
            if not path.exists():
                continue
            expected_api_files.add(name)
            saved += 1
            data = json.loads(path.read_bytes())
            if not isinstance(data, list) or len(data) > 1000:
                raise ValueError("ORACLE_API_SHAPE")
            previous = -1
            for item in data:
                if not isinstance(item, dict) or item.get("symbol") != symbol:
                    raise ValueError("ORACLE_API_SYMBOL")
                ts = int(item["fundingTime"])
                rate = float(item["fundingRate"])
                if not (start <= ts <= end and ts > previous and math.isfinite(rate)):
                    raise ValueError("ORACLE_API_WINDOW_OR_ORDER")
                previous = ts
                api_rows.append((ts, rate))
        detail = report["assets"][symbol]
        if detail.get("api_windows_requested") != expected_windows or detail.get("api_windows_saved") != saved:
            raise ValueError("ORACLE_API_WINDOW_COUNTS")
        if rows is None:
            continue
        grouped = {}
        offsets = Counter()
        invalid = 0
        for ts, rate in rows:
            offset = (ts - START) % STEP
            if offset > 31:
                invalid += 1
                continue
            slot = ts - offset
            grouped.setdefault(slot, []).append(rate)
            offsets[offset] += 1
        api_grouped = {}
        for ts, rate in api_rows:
            api_grouped.setdefault(ts, []).append(rate)
        original_unique = {s for s in SLOTS if len(grouped.get(s, [])) == 1}
        api_unique = {s for s in SLOTS if len(api_grouped.get(s, [])) == 1}
        matched = {s for s in original_unique & api_unique
                   if abs(grouped[s][0] - api_grouped[s][0]) <= 1e-10}
        independently_computed = dict(
            archive_rows=len(rows), api_rows=len(api_rows),
            archive_unique_slots=len(original_unique), api_unique_slots=len(api_unique),
            rate_matched_slots=len(matched),
            missing_archive_slots=len(SLOTS - original_unique),
            missing_api_slots=len(SLOTS - api_unique),
            invalid_archive_offsets=invalid,
            duplicate_archive_slots=sum(len(v)-1 for v in grouped.values()),
            duplicate_api_slots=sum(len(v)-1 for v in api_grouped.values()),
            offgrid_api_events=sum(ts not in SLOTS for ts, _ in api_rows),
            offset_histogram_ms={str(k): v for k, v in sorted(offsets.items())},
            five_folds=[dict(expected=sum(a <= t < b for t in SLOTS),
                             archive_unique=sum(a <= t < b for t in original_unique),
                             api_unique=sum(a <= t < b for t in api_unique),
                             rates_matched=sum(a <= t < b for t in matched))
                        for a, b in zip(EDGES, EDGES[1:])],
            api_windows_requested=expected_windows, api_windows_saved=saved)
        if detail != independently_computed:
            raise ValueError("ORACLE_API_ARCHIVE_DISAGREEMENT_" + symbol)
    actual_files = {p.name for p in (root / "api_raw_ephemeral").glob("*") if p.is_file()}
    if actual_files != expected_api_files:
        raise ValueError("ORACLE_UNDECLARED_API_FILE")
    complete = (not report.get("errors")
                and all(report["assets"][s].get("archive_rows") == 1983
                        and report["assets"][s].get("api_rows") == 1983
                        and report["assets"][s].get("rate_matched_slots") == 1983
                        and report["assets"][s].get("missing_archive_slots") == 0
                        and report["assets"][s].get("missing_api_slots") == 0
                        and report["assets"][s].get("invalid_archive_offsets") == 0
                        and report["assets"][s].get("duplicate_archive_slots") == 0
                        and report["assets"][s].get("duplicate_api_slots") == 0
                        and report["assets"][s].get("offgrid_api_events") == 0
                        for s in SYMBOLS))
    target = "PUBLIC_ARCHIVE_API_EVENT_CLOCK_CORROBORATED" if complete else "SOURCE_HOLD"
    if report.get("status") != target:
        raise ValueError("ORACLE_FALSE_SOURCE_PROMOTION")
    print(json.dumps(dict(oracle="INDEPENDENT_FIRST_PARTY_ARCHIVE_API_REPLAY_PASS",
                          source_status=target,
                          rates_matched={s: report["assets"][s].get("rate_matched_slots", 0)
                                         for s in SYMBOLS},
                          private_settlement=False, economics=False, promotion=False),
                     sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_binance_funding_api_clock_oracle OUT")
    replay(Path(sys.argv[1]))
