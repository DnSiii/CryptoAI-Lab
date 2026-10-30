"""One-shot Binance original publisher-checksummed funding TRAIN source; NEVER economics."""
from __future__ import annotations
import csv
from collections import Counter
import hashlib
import io
import json
import math
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://data.binance.vision/data/futures/um/monthly/fundingRate"
START = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)
END = int(datetime(2023, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
STEP = 8 * 3600 * 1000
SLOTS = set(range(START, END, STEP))
SYMBOLS = ("BTCUSDT", "ETHUSDT")
MONTHS = tuple(f"{y}-{m:02d}" for y in (2021, 2022, 2023)
               for m in range(1, 13) if (y, m) >= (2021, 12) and (y, m) <= (2023, 9))
MAX_ZIP = 8 * 1024 * 1024
MAX_CSV = 24 * 1024 * 1024
SCHEMA = "V99_R106_BINANCE_ORIGINAL_FUNDING_SOURCE_ONLY_V1"

def get(url, cap):
    last = "UNKNOWN"
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent":"CryptoAI-Lab-Research-SourceOnly/1.0"}), timeout=25) as response:
                if response.status != 200:
                    raise ValueError("HTTP_NOT_200")
                body = response.read(cap + 1)
            if len(body) > cap:
                raise ValueError("SOURCE_OVERSIZE")
            return body, None
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            last = type(exc).__name__ + ":" + str(exc)[:70]
            if attempt < 2:
                time.sleep(1 + attempt)
    return None, last

def parse_csv(blob, month):
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names = [x for x in archive.infolist() if not x.is_dir()]
        if len(names) != 1 or names[0].file_size > MAX_CSV or names[0].file_size <= 0:
            raise ValueError("ZIP_NOT_SINGLE_BOUNDED_CSV")
        if not names[0].filename.endswith(".csv"):
            raise ValueError("ZIP_NOT_CSV")
        with archive.open(names[0]) as stream:
            raw = stream.read(MAX_CSV + 1)
    if len(raw) > MAX_CSV:
        raise ValueError("DECOMPRESSED_OVERSIZE")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    expected = {"calc_time", "funding_interval_hours", "last_funding_rate"}
    if not expected.issubset(reader.fieldnames or []):
        raise ValueError("UNEXPECTED_NATIVE_FUNDING_HEADER")
    events = []
    for row in reader:
        try:
            ts = int(row["calc_time"])
            interval = float(row["funding_interval_hours"])
            rate = float(row["last_funding_rate"])
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("BAD_NATIVE_FUNDING_ROW") from exc
        if not math.isfinite(interval) or interval <= 0 or not math.isfinite(rate):
            raise ValueError("NONFINITE_NATIVE_FUNDING")
        if datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m") != month:
            raise ValueError("OUTSIDE_ARCHIVE_MONTH")
        if events and ts <= events[-1][0]:
            raise ValueError("NONMONOTONE_OR_DUPLICATE_NATIVE_FUNDING")
        events.append((ts, interval, rate))
    if not events:
        raise ValueError("EMPTY_NATIVE_FUNDING_CSV")
    return events

def run(root):
    root = Path(root)
    raw_root = root / "raw_ephemeral"
    raw_root.mkdir(parents=True, exist_ok=True)
    files = []
    events = {symbol: [] for symbol in SYMBOLS}
    for symbol in SYMBOLS:
        for month in MONTHS:
            filename = f"{symbol}-fundingRate-{month}.zip"
            url = f"{BASE}/{symbol}/{filename}"
            archive, error = get(url, MAX_ZIP)
            checksum, checksum_error = get(url + ".CHECKSUM", 4096)
            item = dict(symbol=symbol, month=month, filename=filename, status="SOURCE_MISSING_OR_INVALID",
                        error=error or checksum_error, publisher_checksum_verified=False)
            if archive is not None and checksum is not None:
                try:
                    match = re.search(rb"\b([0-9a-fA-F]{64})\b", checksum)
                    if match is None:
                        raise ValueError("PUBLISHER_SHA256_NOT_FOUND")
                    published = match.group(1).decode().lower()
                    digest = hashlib.sha256(archive).hexdigest()
                    if digest != published:
                        raise ValueError("PUBLISHER_SHA256_MISMATCH")
                    parsed = parse_csv(archive, month)
                    (raw_root / filename).write_bytes(archive)
                    (raw_root / (filename + ".CHECKSUM")).write_bytes(checksum)
                    item.update(status="PUBLISHER_CHECKSUM_AND_ROWS_VERIFIED", error=None,
                                zip_sha256=digest, published_sha256=published,
                                original_rows=len(parsed), first_ms=parsed[0][0],
                                last_ms=parsed[-1][0],
                                off_8h_interval_rows=sum(interval != 8 for _, interval, _ in parsed))
                    events[symbol].extend(parsed)
                    item["publisher_checksum_verified"] = True
                except (ValueError, OSError, UnicodeError, zipfile.BadZipFile, OverflowError) as exc:
                    item["error"] = type(exc).__name__ + ":" + str(exc)[:110]
            files.append(item)
            print("BINANCE_ORIGINAL", symbol, month, item["status"], item["error"], flush=True)
    fold_edges = [START + x * 3600000 for x in (0, 3172, 6345, 9518, 12691, 15864)]
    folds = {}
    for symbol in SYMBOLS:
        stamps = [ts for ts, _, _ in events[symbol] if START <= ts < END]
        counts = {ts: stamps.count(ts) for ts in set(stamps)}
        exact = {ts for ts in stamps if ts in SLOTS and counts[ts] == 1}
        non8 = sum(interval != 8 for ts, interval, _ in events[symbol] if START <= ts < END)
        offsets = Counter((lambda r: r if r <= STEP // 2 else r - STEP)((ts - START) % STEP)
                          for ts in stamps)
        by_month = Counter(datetime.fromtimestamp(ts/1000, timezone.utc).strftime("%Y-%m")
                           for ts in stamps if ts not in SLOTS)
        fold_counts = []
        for a, b in zip(fold_edges, fold_edges[1:]):
            expected = sum(a <= t < b for t in SLOTS)
            observed = sum(a <= t < b for t in exact)
            fold_counts.append(dict(expected=expected, observed=observed, missing=expected-observed))
        folds[symbol] = dict(original_rows_all_months=len(events[symbol]),
                             original_rows_train=len(stamps),
                             exact_train_slots=len(exact), expected_train_slots=len(SLOTS),
                             offgrid_train_rows=sum(ts not in SLOTS for ts in stamps),
                             non8h_interval_train_rows=non8,
                             duplicate_train_timestamps=sum(c-1 for c in counts.values() if c>1),
                             signed_nearest_8h_offset_ms_counts={str(k): v for k,v in sorted(offsets.items())},
                             max_abs_8h_offset_ms=max(map(abs,offsets), default=0),
                             offgrid_rows_by_month=dict(sorted(by_month.items())),
                             five_folds=fold_counts)
    complete = (len(files) == 44 and all(f["publisher_checksum_verified"] for f in files)
                and all(folds[s]["exact_train_slots"] == 1983
                        and folds[s]["non8h_interval_train_rows"] == 0
                        and folds[s]["duplicate_train_timestamps"] == 0 for s in SYMBOLS))
    report = dict(schema=SCHEMA, status=("BINANCE_PUBLISHED_FUNDING_TRAIN_COVERAGE_PASS"
                                        if complete else "SOURCE_HOLD"),
                  original_publisher="data.binance.vision", months=list(MONTHS),
                  files=files, folds=folds,
                  source_is_not_account_settled_cash=True,
                  source_is_not_okx=True, economic_train_executed=False,
                  native_account_fees_certified=False, historical_fills_certified=False,
                  roi_calculated=False, validation_opened=False, final_holdout_opened=False,
                  promotion_authorized=False, paper_publication_authorized=False,
                  orders_enabled=False)
    root.mkdir(parents=True, exist_ok=True)
    (root / "binance_funding_source_only.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(status=report["status"], folds=folds, original_verified_files=sum(
        f["publisher_checksum_verified"] for f in files), promotion=False), sort_keys=True))
    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_binance_funding_original_train_source OUT")
    run(sys.argv[1])
