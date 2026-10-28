"""Bounded REAL public Tardis first-of-month full-day source smoke, no economics.

Pre-registered in V99_R106_I1_PUBLIC_FULL_DAY_SOURCE_SMOKE_PREREG_20261028.md.
Never uses credentials, publishes source bytes, accesses sealed periods or trades.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from research.tools.v99_r106_i1_local_tape_import import scan_day

DAY = date(2022, 6, 1)
URL = "https://datasets.tardis.dev/v1/deribit/quotes/2022/06/01/OPTIONS.csv.gz"
MAX_BYTES = 512 * 1024 * 1024
MAX_SECONDS = 180


def probe(opener=None, *, max_bytes=MAX_BYTES, clock=None):
    """Only an entire verified public day counts as a real full-day smoke pass.

    Injected opener is exclusively an OFFLINE fixture and can never be reported
    as verified live original source, regardless of its returned bytes.
    """
    if type(max_bytes) is not int or not 10 <= max_bytes <= MAX_BYTES:
        raise ValueError("INVALID_BOUNDED_PUBLIC_DAY_PROBE")
    fixture = opener is not None
    opener = opener or urllib.request.urlopen
    clock = clock or time.monotonic
    result = {
        "schema": "V99_I1_PUBLIC_FULL_DAY_SOURCE_SMOKE_V1",
        "day": DAY.isoformat(), "venue": "deribit", "symbol_group": "OPTIONS",
        "fixture": fixture, "source_only": True,
        "complete_661_day_train_certified": False,
        "native_terms_or_fills_certified": False,
        "economic_train_executed": False, "roi_calculated": False,
        "validation_opened": False, "holdout_opened": False,
        "promotion_authorized": False, "orders_enabled": False,
        "real_full_day_original_quote_scan_passed": False,
        "downloaded_bytes": 0,
    }
    request = urllib.request.Request(URL, headers={
        "User-Agent": "V99-I1-bounded-public-full-day-source-smoke/1.0"})
    started = clock()
    try:
        with opener(request, timeout=MAX_SECONDS) as response:
            result["http_status"] = int(response.status)
            if result["http_status"] != 200:
                result["status"] = "PUBLIC_DAY_HTTP_NOT_200"
                return result
            content_type = response.headers.get("Content-Type", "").lower()
            if "html" in content_type or "json" in content_type:
                result["status"] = "PUBLIC_DAY_NOT_GZIP"
                return result
            declared = response.headers.get("Content-Length")
            if declared is not None and (not declared.isdigit() or int(declared) > max_bytes):
                result["status"] = "BOUNDED_REAL_SOURCE_INCOMPLETE"
                result["declared_bytes"] = declared if declared.isdigit() else "INVALID"
                return result
            with tempfile.TemporaryDirectory(prefix="v99-public-day-") as tmp:
                path = Path(tmp) / (DAY.isoformat() + ".csv.gz")
                with path.open("wb") as out:
                    prefix = b""
                    while True:
                        if clock() - started > MAX_SECONDS:
                            result["status"] = "PUBLIC_DAY_TIME_CAP_EXCEEDED"
                            return result
                        block = response.read(min(1024 * 1024, max_bytes - result["downloaded_bytes"] + 1))
                        if not block:
                            break
                        result["downloaded_bytes"] += len(block)
                        if result["downloaded_bytes"] > max_bytes:
                            result["status"] = "BOUNDED_REAL_SOURCE_INCOMPLETE"
                            return result
                        prefix = (prefix + block)[:2]
                        out.write(block)
                if (prefix != b"\\x1f\\x8b" or result["downloaded_bytes"] < 10):
                    result["status"] = "PUBLIC_DAY_NOT_GZIP"
                    return result
                if declared is not None and int(declared) != result["downloaded_bytes"]:
                    result["status"] = "PUBLIC_DAY_TRUNCATED"
                    return result
                try:
                    scanned = scan_day(path, DAY)
                except (ValueError, OSError) as exc:
                    # Never expose remote response or raw source rows.
                    result["status"] = "PUBLIC_DAY_ORIGINAL_SCAN_FAILED"
                    result["scan_error_type"] = type(exc).__name__
                    return result
                result["rows"] = scanned["rows"]
                result["sha256"] = scanned["sha256"]
                result["qualifying_put_rows_by_asset"] = scanned[
                    "qualifying_original_put_quote_rows_by_asset"]
                result["status"] = ("OFFLINE_FIXTURE_FULL_DAY_PASS_NOT_MARKET_EVIDENCE"
                                    if fixture else "PUBLIC_REAL_FULL_DAY_SOURCE_SMOKE_PASS")
                result["real_full_day_original_quote_scan_passed"] = not fixture
                return result
    except urllib.error.HTTPError as exc:
        result["http_status"] = int(exc.code)
        result["status"] = "PUBLIC_DAY_HTTP_UNAVAILABLE"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        result["status"] = "PUBLIC_DAY_NETWORK_OR_SOURCE_UNAVAILABLE"
    return result


def main():
    result = probe()
    print(json.dumps(result, sort_keys=True))
    assert not result["promotion_authorized"]
    assert not result["economic_train_executed"]


if __name__ == "__main__":
    main()
