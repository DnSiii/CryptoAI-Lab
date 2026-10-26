"""Bounded authenticated Deribit options FULL-DAY source proof; no trading/economics.

Preregistered at research/V99_R106_I1_LICENSED_FULLDAY_SOURCE_PREREG_20261026.md.
Paid raw bytes are streamed only in memory and never written/uploaded to GitHub.
A full gzip day is NOT a gap-certified historical lifecycle or exchange fill.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DAY = "2022-06-15"
URL = "https://datasets.tardis.dev/v1/deribit/quotes/2022/06/15/OPTIONS.csv.gz"
OUT = Path("research_evidence/v99_i1_full_day_20220615/source_check.json")
MAX_COMPRESSED = 512 * 1024 * 1024
MAX_ROWS = 8_000_000
MAX_SECONDS = 720
FIELDS = {"exchange", "symbol", "timestamp", "local_timestamp",
          "bid_price", "ask_price", "bid_amount", "ask_amount"}
SYMBOL = re.compile(r"^(BTC|ETH)-[0-9]{1,2}[A-Z]{3}[0-9]{2}-[0-9]+(?:\\.[0-9]+)?-([PC])$")
DAY_START = int(datetime(2022, 6, 15, tzinfo=timezone.utc).timestamp() * 1_000_000)
DAY_END = DAY_START + 86_400_000_000


class SourceBlock(ValueError):
    pass


class BoundedCompressedReader:
    """Hash compressed vendor bytes while bounding read, time and memory."""

    def __init__(self, raw, *, max_bytes=MAX_COMPRESSED, max_seconds=MAX_SECONDS):
        self.raw = raw
        self.maximum = max_bytes
        self.deadline = time.monotonic() + max_seconds
        self.bytes = 0
        self.digest = hashlib.sha256()

    def read(self, n=-1):
        if time.monotonic() >= self.deadline:
            raise SourceBlock("SOURCE_STREAM_TIME_LIMIT")
        remaining = self.maximum - self.bytes
        if remaining < 0:
            raise SourceBlock("SOURCE_COMPRESSED_BYTE_LIMIT")
        size = min(n if n >= 0 else 65536, remaining + 1)
        chunk = self.raw.read(size)
        self.bytes += len(chunk)
        if self.bytes > self.maximum:
            raise SourceBlock("SOURCE_COMPRESSED_BYTE_LIMIT")
        self.digest.update(chunk)
        return chunk


def inspect_gzip(raw, *, fixture=False, max_bytes=MAX_COMPRESSED, max_rows=MAX_ROWS):
    """Read entire original gzip, never persist vendor bytes or infer fills."""
    if type(fixture) is not bool:
        raise SourceBlock("INVALID_FIXTURE_FLAG")
    bounded = BoundedCompressedReader(raw, max_bytes=max_bytes)
    counts = {asset: {"option_rows": 0, "valid_put_quotes": 0,
                      "valid_call_quotes": 0} for asset in ("BTC", "ETH")}
    rows = 0
    previous_arrival = None
    try:
        with gzip.GzipFile(fileobj=bounded, mode="rb") as stream:
            with io.TextIOWrapper(stream, encoding="utf-8", newline="") as text_stream:
                reader = csv.DictReader(text_stream)
                if not FIELDS.issubset(reader.fieldnames or []):
                    raise SourceBlock("MISSING_REQUIRED_VENDOR_COLUMNS")
                for row in reader:
                    rows += 1
                    if rows > max_rows:
                        raise SourceBlock("SOURCE_ROW_LIMIT")
                    if row.get("exchange") != "deribit":
                        raise SourceBlock("WRONG_VENDOR_VENUE")
                    try:
                        arrival = int(row["local_timestamp"])
                        event = int(row["timestamp"])
                    except (TypeError, ValueError, OverflowError) as exc:
                        raise SourceBlock("INVALID_VENDOR_CLOCK") from exc
                    if not DAY_START <= event <= arrival < DAY_END:
                        raise SourceBlock("FUTURE_OR_OUTSIDE_TRAIN_DAY")
                    if previous_arrival is not None and arrival < previous_arrival:
                        raise SourceBlock("REORDERED_VENDOR_CAPTURE")
                    previous_arrival = arrival
                    match = SYMBOL.fullmatch(row.get("symbol") or "")
                    if not match:
                        continue
                    asset, kind = match.groups()
                    counts[asset]["option_rows"] += 1
                    try:
                        bid, ask, bid_size, ask_size = (
                            float(row[k]) for k in ("bid_price", "ask_price",
                                                   "bid_amount", "ask_amount"))
                        good = (all(math.isfinite(v) for v in
                                    (bid, ask, bid_size, ask_size))
                                and 0 < bid < ask and bid_size > 0 and ask_size > 0)
                    except (ValueError, TypeError, OverflowError):
                        good = False
                    if good:
                        counts[asset]["valid_put_quotes" if kind == "P"
                               else "valid_call_quotes"] += 1
    except (gzip.BadGzipFile, EOFError, UnicodeError, OSError) as exc:
        raise SourceBlock("INVALID_OR_TRUNCATED_ORIGINAL_GZIP") from exc
    if rows == 0 or any(counts[a]["valid_put_quotes"] == 0
                        for a in ("BTC", "ETH")):
        raise SourceBlock("EMPTY_OR_MISSING_BTC_ETH_PUT_QUOTES")
    return {
        "schema": "V99_I1_BOUNDED_AUTHENTICATED_FULL_DAY_SOURCE_V1",
        "status": ("SYNTHETIC_FIXTURE_ONLY" if fixture
                   else "SOURCE_ONE_DAY_FIELDS_OBSERVED_NOT_LIFECYCLE"),
        "provider": "Tardis Deribit reconstructed WebSocket quotes",
        "source_date_utc": DAY,
        "original_compressed_sha256": bounded.digest.hexdigest(),
        "compressed_bytes_read": bounded.bytes,
        "original_quote_rows": rows,
        "asset_counts": counts,
        "full_gzip_consumed": True,
        "vendor_gap_certified": False,
        "complete_2021_2023_archive": False,
        "historical_native_fee_certified": False,
        "historical_margin_certified": False,
        "original_account_fills_certified": False,
        "economic_train_executed": False,
        "validation_opened": False,
        "holdout_opened": False,
        "orders_enabled": False,
        "promotion_authorized": False,
    }


def main():
    key = os.environ.get("TARDIS_API_KEY", "").strip()
    if not key:
        result = {"schema": "V99_I1_BOUNDED_AUTHENTICATED_FULL_DAY_SOURCE_V1",
                  "status": "BLOCKED_NO_AUTHENTICATED_ENTITLEMENT",
                  "source_date_utc": DAY, "network_requests": 0,
                  "economic_train_executed": False,
                  "validation_opened": False, "holdout_opened": False,
                  "orders_enabled": False, "promotion_authorized": False}
    else:
        request = Request(URL, headers={
            "Authorization": "Bearer " + key,
            "User-Agent": "V99-I1-authorized-TRAIN-full-day-source-only/1.0",
        })
        try:
            with urlopen(request, timeout=90) as response:
                if response.status != 200:
                    raise SourceBlock("NONFULL_VENDOR_RESPONSE")
                result = inspect_gzip(response, fixture=False)
                result["network_requests"] = 1
        except HTTPError as exc:
            result = {"status": "BLOCKED_VENDOR_HTTP_" + str(exc.code)}
        except (URLError, TimeoutError):
            result = {"status": "BLOCKED_VENDOR_TRANSPORT"}
        except SourceBlock as exc:
            result = {"status": "BLOCKED_" + str(exc)}
        for key_name, value in {
            "schema": "V99_I1_BOUNDED_AUTHENTICATED_FULL_DAY_SOURCE_V1",
            "source_date_utc": DAY, "economic_train_executed": False,
            "validation_opened": False, "holdout_opened": False,
            "orders_enabled": False, "promotion_authorized": False,
        }.items():
            result[key_name] = value
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
