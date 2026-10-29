"""Final preregistered second public TRAIN Sunday, source-only; no economics."""
from __future__ import annotations

import hashlib
import json
import tempfile
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from research.tools.v99_r106_i1_local_tape_import import scan_day, require_hourly_original_coverage
from research.tools.v99_r106_i1_original_intent_binding import bind
from research.tools.v99_r106_i1_source_driven_entry_book import _one_sunday
from research.verification.independent_v99_r106_i1_source_entry_book_oracle import _replay_day

SUNDAY = date(2023, 1, 1)
MONDAY = date(2023, 1, 2)
DECISION_MS = int(datetime(2023, 1, 2, tzinfo=timezone.utc).timestamp() * 1000)
URL = "https://datasets.tardis.dev/v1/deribit/quotes/2023/01/01/OPTIONS.csv.gz"
MAX_BYTES = 512 * 1024 * 1024
MAX_SECONDS = 240
SCHEMA = "V99_I1_SECOND_ORIGINAL_SUNDAY_FIXED_MONDAY_SOURCE_ONLY_V1"


def analyze(path: Path, intents: list[dict]) -> dict:
    selected = [r for r in intents if r.get("decision_ms") == DECISION_MS]
    if (len(intents) != 180 or len(selected) != 2
            or [r.get("asset") for r in selected] != ["BTC", "ETH"]
            or any(r.get("signal") not in (
                "POSITIVE_EX_ANTE_PREMIUM", "NO_PREMIUM", "NO_30D_HISTORY")
                for r in selected)):
        raise ValueError("SECOND_SUNDAY_ORIGINAL_SIGNAL_GRID_INVALID")
    scan = scan_day(path, SUNDAY)
    require_hourly_original_coverage(scan)
    books, invalid, stale, rows = _one_sunday(path, scan["rows"], SUNDAY, DECISION_MS)
    independent, independent_invalid, independent_stale, independent_rows = (
        _replay_day(path, SUNDAY, DECISION_MS))
    if ((books, invalid, stale, rows) !=
            (independent, independent_invalid, independent_stale, independent_rows)):
        raise ValueError("SECOND_SUNDAY_INDEPENDENT_BOOK_DIVERGENCE")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != scan["sha256"]:
        raise ValueError("SECOND_SUNDAY_ORIGINAL_SHA_DIVERGENCE")
    return {
        "schema": SCHEMA, "source_day": SUNDAY.isoformat(),
        "decision_day": MONDAY.isoformat(), "original_quote_rows": rows,
        "original_sha256": scan["sha256"],
        "hourly_qualifying_put_coverage": scan["qualifying_original_put_arrival_hours_by_asset"],
        "original_books_by_asset": {a: len(books[a]) for a in ("BTC", "ETH")},
        "original_signal_by_asset": {r["asset"]: r["signal"] for r in selected},
        "invalid_last_books_by_asset": invalid, "stale_last_books_by_asset": stale,
        "independent_original_byte_reexecution": True,
        "status": "SECOND_SUNDAY_SOURCE_ONLY_REPLAY",
        "real_original_day_verified": False, "fixture": True,
        "historical_option_lifecycles_certified": 0,
        "economic_train_executed": False, "roi_calculated": False,
        "native_terms_authenticated": False, "validation_opened": False,
        "holdout_opened": False, "promotion_authorized": False, "orders_enabled": False,
    }


def live(original_signals: Path) -> dict:
    original = bind(original_signals)
    report = {"schema": SCHEMA, "source_day": SUNDAY.isoformat(),
              "decision_day": MONDAY.isoformat(), "status": "NOT_ATTEMPTED",
              "fixture": False, "real_original_day_verified": False,
              "historical_option_lifecycles_certified": 0,
              "economic_train_executed": False, "roi_calculated": False,
              "native_terms_authenticated": False, "validation_opened": False,
              "holdout_opened": False, "promotion_authorized": False,
              "orders_enabled": False}
    started = time.monotonic()
    request = urllib.request.Request(URL, headers={
        "User-Agent": "V99-final-preregistered-source-only/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=MAX_SECONDS) as response:
            report["http_status"] = response.status
            if response.status != 200:
                report["status"] = "ORIGINAL_HTTP_NOT_200"
                return report
            length = response.headers.get("Content-Length")
            if length is not None and (
                    not length.isdigit() or int(length) > MAX_BYTES):
                report["status"] = "ORIGINAL_OVERSIZED_OR_INVALID_LENGTH"
                return report
            with tempfile.TemporaryDirectory(prefix="v99-second-sunday-") as tmp:
                path = Path(tmp) / "2023-01-01.csv.gz"
                received = 0
                with path.open("wb") as target:
                    while True:
                        if time.monotonic() - started > MAX_SECONDS:
                            report["status"] = "ORIGINAL_TRANSFER_TIMEOUT"
                            return report
                        chunk = response.read(min(1024 * 1024, MAX_BYTES - received + 1))
                        if not chunk:
                            break
                        received += len(chunk)
                        if received > MAX_BYTES:
                            report["status"] = "ORIGINAL_TOO_LARGE"
                            return report
                        target.write(chunk)
                report["compressed_bytes"] = received
                if (received < 10 or path.open("rb").read(2) != b"\\x1f\\x8b"
                        or length is not None and received != int(length)):
                    report["status"] = "ORIGINAL_TRUNCATED_OR_NOT_GZIP"
                    return report
                verified = analyze(path, original["intents"])
                report.update(verified)
                report["fixture"] = False
                report["real_original_day_verified"] = True
                report["status"] = ("SECOND_SUNDAY_REAL_SOURCE_BOOKS_PRESENT"
                    if any(verified["original_books_by_asset"].values())
                    else "SECOND_SUNDAY_REAL_SOURCE_NO_FIXED_BOOKS")
                return report
    except urllib.error.HTTPError as exc:
        report["http_status"] = exc.code
        report["status"] = "ORIGINAL_HTTP_UNAVAILABLE"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        report["status"] = "ORIGINAL_NETWORK_OR_FILE_UNAVAILABLE"
        report["error_class"] = type(exc).__name__
    except (ValueError, EOFError, UnicodeError) as exc:
        report["status"] = "ORIGINAL_REPLAY_FAILED"
        report["error_class"] = type(exc).__name__
        report["error_code"] = str(exc).split(":", 1)[0][:100]
    return report


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_second_sunday_probe ORIGINAL_SIGNAL_JSON")
    print(json.dumps(live(Path(sys.argv[1])), sort_keys=True))
