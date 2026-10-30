"""One-shot first-party Binance USD-M bookTicker TRAIN quote feasibility; NO economics."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DAY = "2022-01-23"
START = int(datetime(2022, 1, 23, tzinfo=timezone.utc).timestamp() * 1000)
END = START + 86_400_000
HOUR = 3_600_000
AGE = 300_000
SYMBOLS = ("BTCUSDT", "ETHUSDT")
BASE = "https://data.binance.vision/data/futures/um/daily/bookTicker"
HEADER = ("update_id", "best_bid_price", "best_bid_qty", "best_ask_price",
          "best_ask_qty", "transaction_time", "event_time")
MAX_ZIP = 200 * 1024 * 1024
MAX_CSV = 1_200 * 1024 * 1024
MAX_ROWS = 12_000_000
SCHEMA = "V99_R106_BINANCE_BOOKTICKER_ORIGINAL_SAMPLE_SOURCE_ONLY_V1"


def download(url: str, cap: int) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": "CryptoAI-Lab-V99-SourceOnly/1.0"}), timeout=90) as resp:
        if resp.status != 200:
            raise ValueError("HTTP_NOT_200")
        data = resp.read(cap + 1)
    if not data or len(data) > cap:
        raise ValueError("EMPTY_OR_OVERSIZE_SOURCE")
    return data


def records(archive: bytes):
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        entries = [m for m in z.infolist() if not m.is_dir()]
        if len(entries) != 1 or not entries[0].filename.endswith(".csv"):
            raise ValueError("ZIP_NOT_SINGLE_CSV")
        if not 0 < entries[0].file_size <= MAX_CSV:
            raise ValueError("UNSAFE_DECOMPRESSED_CSV_SIZE")
        with z.open(entries[0]) as source:
            text = io.TextIOWrapper(source, encoding="utf-8-sig", newline="")
            reader = csv.reader(text)
            first = next(reader, None)
            if first is None:
                raise ValueError("EMPTY_CSV")
            if tuple(x.strip().lower() for x in first) == HEADER:
                pass
            elif len(first) == 7 and first[0].strip().isdigit():
                yield first
            else:
                raise ValueError("UNKNOWN_BOOKTICKER_COLUMNS:" + ",".join(first[:9])[:120])
            yield from reader


def parse(row):
    if len(row) != 7:
        raise ValueError("BAD_COLUMN_COUNT")
    try:
        update_id = int(row[0])
        bid, bid_qty, ask, ask_qty = (float(x) for x in row[1:5])
        transaction_ms, event_ms = int(row[5]), int(row[6])
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("MALFORMED_NATIVE_QUOTE_ROW") from exc
    if update_id < 0 or not all(math.isfinite(x) and x > 0 for x in
                                 (bid, bid_qty, ask, ask_qty)):
        raise ValueError("INVALID_NATIVE_BID_ASK_OR_SIZE")
    if not (ask > bid and START <= transaction_ms <= event_ms < END):
        raise ValueError("CROSSED_QUOTE_OR_INVALID_NATIVE_TIME")
    return (event_ms, bid, bid_qty, ask, ask_qty, update_id)


def summarize(archive: bytes) -> dict:
    best = [None] * 23
    total = 0
    previous = None
    min_time = max_time = None
    for row in records(archive):
        quote = parse(row)
        ts = quote[0]
        if previous is not None and ts < previous:
            raise ValueError("NONCHRONOLOGICAL_NATIVE_EVENT_TIME")
        previous = ts
        min_time = ts if min_time is None else min_time
        max_time = ts
        total += 1
        if total > MAX_ROWS:
            raise ValueError("EXCESSIVE_SOURCE_ROWS")
        hour = (ts - START) // HOUR + 1
        if 1 <= hour <= 23 and (START + hour * HOUR - ts) <= AGE:
            best[hour - 1] = quote
    if not total:
        raise ValueError("EMPTY_NATIVE_QUOTES")
    digest = hashlib.sha256()
    coverage = 0
    for hour, quote in enumerate(best, 1):
        decision = START + hour * HOUR
        if quote is None:
            digest.update(f"{decision},NONE\n".encode())
            continue
        if not 0 < decision - quote[0] <= AGE:
            raise ValueError("FUTURE_OR_STALE_BOOK")
        coverage += 1
        digest.update((f"{decision},{quote[0]},{quote[1]:.17g},{quote[2]:.17g},"
                       f"{quote[3]:.17g},{quote[4]:.17g},{quote[5]}\n").encode())
    return dict(original_quote_rows=total, first_event_ms=min_time,
                last_event_ms=max_time, strict_hourly_asof_covered=coverage,
                strict_hourly_asof_required=23, hourly_asof_sha256=digest.hexdigest())


def run(root: Path) -> dict:
    root = Path(root)
    raw = root / "raw_ephemeral"
    raw.mkdir(parents=True, exist_ok=True)
    report = dict(schema=SCHEMA, day=DAY, venue="BINANCE_USDM_FUTURES",
                  classification="SOURCE_HOLD", assets={},
                  economics_executed=False, historical_fills_certified=False,
                  account_funding_settlement_certified=False,
                  native_account_fee_tier_certified=False,
                  okx_source=False, i1_deribit_source=False,
                  validation_opened=False, final_holdout_opened=False,
                  paper_changed=False, frozen_changed=False,
                  orders_enabled=False, promotion=False)
    for symbol in SYMBOLS:
        name = f"{symbol}-bookTicker-{DAY}.zip"
        url = f"{BASE}/{symbol}/{name}"
        item = dict(status="SOURCE_HOLD", publisher_sha256_verified=False)
        try:
            body = download(url, MAX_ZIP)
            checksum = download(url + ".CHECKSUM", 4096)
            match = re.search(rb"\b([0-9a-fA-F]{64})\b", checksum)
            if match is None:
                raise ValueError("NO_PUBLISHER_CHECKSUM")
            digest = hashlib.sha256(body).hexdigest()
            if digest != match.group(1).decode().lower():
                raise ValueError("PUBLISHER_CHECKSUM_MISMATCH")
            (raw / name).write_bytes(body)
            (raw / (name + ".CHECKSUM")).write_bytes(checksum)
            item.update(summarize(body))
            item.update(status="ORIGINAL_PUBLISHER_VERIFIED",
                        publisher_sha256_verified=True, original_zip_sha256=digest)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError,
                zipfile.BadZipFile, UnicodeError) as exc:
            item["blocker"] = type(exc).__name__ + ":" + str(exc)[:160]
        report["assets"][symbol] = item
        print("BOOKTICKER_SOURCE", symbol, item["status"],
              item.get("strict_hourly_asof_covered", 0), item.get("blocker", ""),
              flush=True)
    if all(report["assets"][s].get("publisher_sha256_verified") and
           report["assets"][s].get("strict_hourly_asof_covered") == 23 for s in SYMBOLS):
        report["classification"] = "FIRST_PARTY_BEST_BID_ASK_SAMPLE_FEASIBLE_NOT_EXECUTION"
    (root / "binance_bookticker_source_only.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(dict(classification=report["classification"],
                          coverage={s: report["assets"][s].get("strict_hourly_asof_covered", 0)
                                    for s in SYMBOLS}, promotion=False), sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_binance_bookticker_native_quote_probe OUT")
    run(Path(sys.argv[1]))
