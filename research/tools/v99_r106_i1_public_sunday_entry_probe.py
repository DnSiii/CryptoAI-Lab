"""One real original Sunday -> fixed Monday I1 entry-book feasibility, NO ECONOMICS.

Pre-registered in V99_R106_I1_REAL_SUNDAY_FULLDAY_ENTRY_PREREG_20261028.md.
Does not fetch sealed dates, claim fills, certify source completeness or trade.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_local_tape_import import (
    scan_day, require_hourly_original_coverage,
)
from research.tools.v99_r106_i1_original_intent_binding import bind
from research.tools.v99_r106_i1_source_driven_entry_book import _one_sunday
from research.verification.independent_v99_r106_i1_source_entry_book_oracle import _replay_day

SUNDAY = date(2022, 5, 1)
MONDAY = date(2022, 5, 2)
URL = "https://datasets.tardis.dev/v1/deribit/quotes/2022/05/01/OPTIONS.csv.gz"
MAX_BYTES = 512 * 1024 * 1024
MAX_TRANSFER_SECONDS = 240
DECISION_MS = int(datetime(2022, 5, 2, tzinfo=timezone.utc).timestamp() * 1000)


def analyze_file(path: Path, intents: list[dict]) -> dict:
    """Source-only original-shaped inspection; NEVER certifies a caller's file."""
    expected = [r for r in intents if r.get("decision_ms") == DECISION_MS]
    if (len(intents) != 180 or len(expected) != 2
            or [r.get("asset") for r in expected] != ["BTC", "ETH"]
            or any(r.get("signal") not in (
                "POSITIVE_EX_ANTE_PREMIUM", "NO_PREMIUM", "NO_30D_HISTORY")
                for r in expected)):
        raise ValueError("UNBOUND_OR_MISSING_FIXED_ORIGINAL_MONDAY_INTENTS")
    scanned = scan_day(path, SUNDAY)
    require_hourly_original_coverage(scanned)
    actual, invalid, stale, seen = _one_sunday(
        path, scanned["rows"], SUNDAY, DECISION_MS)
    independently, independently_invalid, independently_stale, other_seen = (
        _replay_day(path, SUNDAY, DECISION_MS))
    if (seen != other_seen or seen != scanned["rows"]
            or actual != independently or invalid != independently_invalid
            or stale != independently_stale):
        raise ValueError("INDEPENDENT_ORIGINAL_SUNDAY_ENTRY_BOOK_DISAGREEMENT")
    # Independent byte re-read. A self-declared source manifest is not a
    # vendor gap certificate and this one day is not a 661-day source.
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != scanned["sha256"]:
        raise ValueError("ORIGINAL_SUNDAY_BYTE_HASH_DIVERGENCE")
    # A missing fresh book is an actual source-based CASH veto, not a
    # software exception or a reason to relax the fixed 300s freshness gate.
    both_books = all(actual[asset] for asset in ("BTC", "ETH"))
    return {
        "schema": "V99_I1_REAL_SUNDAY_FIXED_MONDAY_ENTRY_FEASIBILITY_V1",
        "status": ("ORIGINAL_SHAPED_ENTRY_BOOK_REPLAY_ONLY_NOT_CERTIFIED"
                   if both_books else "ORIGINAL_SHAPED_NO_FRESH_ENTRY_BOOK_VETO"),
        "source_day": SUNDAY.isoformat(),
        "decision_day": MONDAY.isoformat(),
        "compressed_sha256": scanned["sha256"],
        "source_rows": seen,
        "hourly_qualifying_put_coverage": scanned[
            "qualifying_original_put_arrival_hours_by_asset"],
        "original_books_by_asset": {a: len(actual[a]) for a in ("BTC", "ETH")},
        "both_assets_have_fresh_fixed_tenor_books": both_books,
        "invalid_last_books_by_asset": invalid,
        "stale_last_books_by_asset": stale,
        "fixed_original_signal_by_asset": {
            r["asset"]: r["signal"] for r in expected},
        "independent_original_byte_entry_replay": True,
        "source_fixture": True,  # A caller-provided path is never certified.
        "real_original_day_verified": False,
        "original_complete_option_lifecycles_certified": 0,
        "economic_train_executed": False,
        "native_terms_authenticated": False,
        "roi_calculated": False,
        "validation_opened": False,
        "holdout_opened": False,
        "orders_enabled": False,
        "promotion_authorized": False,
    }


def probe_live(original_signal_path: Path) -> dict:
    """No injectable downloader: live flag only after full HTTP 200 + replay."""
    original = bind(original_signal_path)
    result = {
        "schema": "V99_I1_REAL_SUNDAY_FIXED_MONDAY_ENTRY_FEASIBILITY_V1",
        "source_day": SUNDAY.isoformat(), "decision_day": MONDAY.isoformat(),
        "status": "NOT_ATTEMPTED", "source_fixture": False,
        "real_original_day_verified": False,
        "original_complete_option_lifecycles_certified": 0,
        "economic_train_executed": False, "native_terms_authenticated": False,
        "roi_calculated": False, "validation_opened": False,
        "holdout_opened": False, "orders_enabled": False,
        "promotion_authorized": False,
    }
    request = urllib.request.Request(
        URL, headers={"User-Agent": "V99-I1-original-Sunday-entry-replay/1.0"})
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=MAX_TRANSFER_SECONDS) as response:
            result["http_status"] = response.status
            if response.status != 200:
                result["status"] = "REAL_SUNDAY_HTTP_NOT_200"
                return result
            length = response.headers.get("Content-Length")
            if length is not None and (
                    not length.isdigit() or int(length) > MAX_BYTES):
                result["status"] = "REAL_SUNDAY_OVERSIZED_OR_INVALID_LENGTH"
                return result
            with tempfile.TemporaryDirectory(prefix="v99-real-sunday-") as tmp:
                path = Path(tmp) / (SUNDAY.isoformat() + ".csv.gz")
                received = 0
                with path.open("wb") as output:
                    while True:
                        if time.monotonic() - started > MAX_TRANSFER_SECONDS:
                            result["status"] = "REAL_SUNDAY_TRANSFER_TIMEOUT"
                            return result
                        chunk = response.read(min(1024 * 1024, MAX_BYTES - received + 1))
                        if not chunk:
                            break
                        received += len(chunk)
                        if received > MAX_BYTES:
                            result["status"] = "REAL_SUNDAY_TOO_LARGE"
                            return result
                        output.write(chunk)
                result["compressed_bytes"] = received
                if (received < 10 or path.open("rb").read(2) != b"\x1f\x8b"
                        or length is not None and received != int(length)):
                    result["status"] = "REAL_SUNDAY_TRUNCATED_OR_NOT_GZIP"
                    return result
                summary = analyze_file(path, original["intents"])
                result.update(summary)
                result["status"] = (
                    "REAL_ORIGINAL_SUNDAY_ENTRY_BOOK_REPLAY_PASS_SOURCE_ONLY"
                    if summary["both_assets_have_fresh_fixed_tenor_books"]
                    else "REAL_ORIGINAL_SUNDAY_NO_FRESH_ENTRY_BOOK_VETO_SOURCE_ONLY")
                result["source_fixture"] = False
                result["real_original_day_verified"] = True
                return result
    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code
        result["status"] = "REAL_SUNDAY_HTTP_UNAVAILABLE"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result["status"] = "REAL_SUNDAY_NETWORK_OR_FILE_UNAVAILABLE"
        result["error_class"] = type(exc).__name__
    except (ValueError, EOFError, UnicodeError) as exc:
        result["status"] = "REAL_SUNDAY_ORIGINAL_REPLAY_FAILED"
        result["error_class"] = type(exc).__name__
        # Only fixed internal error identifiers; never vendor quotes or rows.
        known = (
            "MISSING_QUALIFYING_ORIGINAL_PUT_QUOTES",
            "ORIGINAL_DAY_BTC_ETH_HOURLY_CAPTURE_GAP",
            "NONCAUSAL_OR_OUT_OF_ORDER_CLOCK",
            "WRONG_ORIGINAL_EXCHANGE",
            "CORRUPT_ORIGINAL_GZIP",
            "MISSING_ORIGINAL_QUOTE_COLUMNS",
            "ORIGINAL_BOOK_COLUMNS_MISSING",
            "ORIGINAL_CAPTURE_ORDER_OR_CLOCK_INVALID",
            "ORIGINAL_ENTRY_DAY_ROW_COUNT_MISMATCH",
            "INDEPENDENT_ORIGINAL_SUNDAY_ENTRY_BOOK_DISAGREEMENT",
            "ORIGINAL_SUNDAY_BYTE_HASH_DIVERGENCE",
            "NO_CAUSAL_FIXED_TENOR_ENTRY_BOOK_FOR_BOTH_ASSETS",
        )
        result["error_code"] = next(
            (code for code in known if str(exc).startswith(code)),
            "OTHER_SOURCE_REPLAY_ERROR")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_public_sunday_entry_probe ORIGINAL_CAUSAL_SIGNAL_JSON")
    print(json.dumps(probe_live(Path(sys.argv[1])), sort_keys=True))
