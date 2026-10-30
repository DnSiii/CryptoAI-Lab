"""Preregistered TRAIN-only first-party Binance funding API/archive clock comparison.

No trading, economics, private settlement, validation, or promotion.
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from research.tools import v99_r106_binance_funding_original_train_source as original

START, END, STEP = original.START, original.END, original.STEP
SYMBOLS = original.SYMBOLS
API = "https://fapi.binance.com/fapi/v1/fundingRate"
WINDOW = 90 * 24 * 3600 * 1000
FOLD_EDGES = [START + h * 3600000 for h in (0, 3172, 6345, 9518, 12691, 15864)]
SCHEMA = "V99_R106_BINANCE_FUNDING_API_ARCHIVE_CLOCK_CORROBORATION_V1"


def query(url: str) -> tuple[bytes | None, str | None]:
    error = "NO_RESPONSE"
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={
                "User-Agent": "CryptoAI-Lab-Research-SourceOnly/1.0",
                "Accept": "application/json"}), timeout=25) as resp:
                if resp.status != 200:
                    raise ValueError("HTTP_NON_200")
                data = resp.read(2_000_001)
                if len(data) > 2_000_000:
                    raise ValueError("API_RESPONSE_OVERSIZE")
                return data, None
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            error = type(exc).__name__ + ":" + str(exc)[:100]
            if attempt < 2:
                time.sleep(1 + attempt)
    return None, error


def api_records(symbol: str, raw_dir: Path):
    records = []
    errors = []
    windows = 0
    for start in range(START, END, WINDOW):
        end = min(start + WINDOW, END) - 1
        params = urlencode(dict(symbol=symbol, startTime=start, endTime=end, limit=1000))
        payload, err = query(API + "?" + params)
        windows += 1
        if payload is None:
            errors.append(f"{symbol}:WINDOW_{windows}:{err}")
            continue
        try:
            data = json.loads(payload)
            if not isinstance(data, list) or len(data) > 1000:
                raise ValueError("API_NOT_BOUNDED_LIST")
            parsed = []
            for item in data:
                if not isinstance(item, dict) or item.get("symbol") != symbol:
                    raise ValueError("API_SYMBOL_MISMATCH")
                ts = int(item["fundingTime"])
                rate = float(item["fundingRate"])
                if not (start <= ts <= end and math.isfinite(rate)):
                    raise ValueError("API_WINDOW_OR_RATE_INVALID")
                parsed.append((ts, rate))
            if any(a[0] >= b[0] for a, b in zip(parsed, parsed[1:])):
                raise ValueError("API_NONMONOTONE_OR_DUPLICATE")
            # Save exactly the first-party JSON response; never upload it.
            (raw_dir / f"{symbol}-window-{windows:02d}.json").write_bytes(payload)
            records.extend(parsed)
        except (KeyError, ValueError, TypeError, OverflowError) as exc:
            errors.append(f"{symbol}:WINDOW_{windows}:{type(exc).__name__}:{str(exc)[:70]}")
    return records, errors, windows


def compare(symbol: str, root: Path, api_rows: list[tuple[int, float]]):
    archive_rows = []
    for month in original.MONTHS:
        name = f"{symbol}-fundingRate-{month}.zip"
        archive = root / "raw_ephemeral" / name
        if not archive.exists():
            return dict(error="ORIGINAL_ARCHIVE_MISSING", archive_rows=0)
        archive_rows.extend(original.parse_csv(archive.read_bytes(), month))
    archive_rows = [(ts, rate) for ts, interval, rate in archive_rows
                    if START <= ts < END and interval == 8]
    archive_by_slot = {}
    offset_hist = Counter()
    invalid_offsets = 0
    for ts, rate in archive_rows:
        offset = (ts - START) % STEP
        if offset > 31:
            invalid_offsets += 1
            continue
        slot = ts - offset
        archive_by_slot.setdefault(slot, []).append((ts, rate))
        offset_hist[offset] += 1
    api_by_slot = {}
    for ts, rate in api_rows:
        api_by_slot.setdefault(ts, []).append(rate)
    expected = set(range(START, END, STEP))
    archive_slots = {k for k, v in archive_by_slot.items() if len(v) == 1}
    api_slots = {k for k, v in api_by_slot.items() if len(v) == 1}
    matched = [slot for slot in sorted(expected & archive_slots & api_slots)
               if abs(archive_by_slot[slot][0][1] - api_by_slot[slot][0]) <= 1e-10]
    folds = []
    for a, b in zip(FOLD_EDGES, FOLD_EDGES[1:]):
        folds.append(dict(expected=sum(a <= s < b for s in expected),
                          archive_unique=sum(a <= s < b for s in archive_slots & expected),
                          api_unique=sum(a <= s < b for s in api_slots & expected),
                          rates_matched=sum(a <= s < b for s in matched)))
    return dict(archive_rows=len(archive_rows), api_rows=len(api_rows),
                archive_unique_slots=len(archive_slots & expected),
                api_unique_slots=len(api_slots & expected),
                rate_matched_slots=len(matched),
                missing_archive_slots=len(expected - archive_slots),
                missing_api_slots=len(expected - api_slots),
                invalid_archive_offsets=invalid_offsets,
                duplicate_archive_slots=sum(len(v)-1 for v in archive_by_slot.values()),
                duplicate_api_slots=sum(len(v)-1 for v in api_by_slot.values()),
                offgrid_api_events=sum(ts not in expected for ts, _ in api_rows),
                offset_histogram_ms={str(k): v for k, v in sorted(offset_hist.items())},
                five_folds=folds)


def run(root: Path):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    # Existing publisher-SHA256 original-byte source gate remains unchanged.
    publisher = original.run(root)
    raw = root / "api_raw_ephemeral"
    raw.mkdir(exist_ok=True)
    summary = {}
    errors = []
    for symbol in SYMBOLS:
        rows, api_errors, windows = api_records(symbol, raw)
        errors.extend(api_errors)
        detail = compare(symbol, root, rows)
        detail["api_windows_requested"] = windows
        detail["api_windows_saved"] = len(list(raw.glob(f"{symbol}-window-*.json")))
        summary[symbol] = detail
        print("BINANCE_API_ARCHIVE", symbol, json.dumps(detail, sort_keys=True), flush=True)
    complete = (len(errors) == 0
                and all(f.get("publisher_checksum_verified") for f in publisher["files"])
                and all(summary[s].get("archive_rows") == 1983
                        and summary[s].get("api_rows") == 1983
                        and summary[s].get("rate_matched_slots") == 1983
                        and summary[s].get("missing_archive_slots") == 0
                        and summary[s].get("missing_api_slots") == 0
                        and summary[s].get("invalid_archive_offsets") == 0
                        and summary[s].get("duplicate_archive_slots") == 0
                        and summary[s].get("duplicate_api_slots") == 0
                        and summary[s].get("offgrid_api_events") == 0
                        for s in SYMBOLS))
    report = dict(schema=SCHEMA, status=("PUBLIC_ARCHIVE_API_EVENT_CLOCK_CORROBORATED"
                                        if complete else "SOURCE_HOLD"),
                  scope="[2021-12-09,2023-10-01)_TRAIN_ONLY",
                  source="BINANCE_FIRST_PARTY_PUBLIC_ARCHIVE_AND_USDM_FUNDINGRATE_API",
                  original_strict_exact_clock_gate_unchanged=True,
                  original_strict_exact_clock_observed_per_asset=821,
                  errors=errors, assets=summary,
                  no_private_account_settlement=True,
                  no_economics=True, no_promotion=True,
                  no_validation=True, no_holdout=True,
                  no_paper=True, no_orders=True)
    (root / "binance_funding_api_clock_source_only.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(status=report["status"], errors=errors,
                          matched={s: summary[s].get("rate_matched_slots", 0)
                                   for s in SYMBOLS}, promotion=False), sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_binance_funding_api_clock_binding OUT")
    run(Path(sys.argv[1]))
