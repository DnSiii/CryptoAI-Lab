"""CoinAPI ORIGINAL per-contract Sunday -> complete 180-intent OPEN inventories.

Source/derived cross-parser parity only; never certified native economics.
Prereg: V99_R106_I1_COINAPI_FULL_ENTRY_BOOK_PARITY_PREREG_20261102.md
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_coinapi_661d_original_byte_chain import verify as verify_chain
from research.tools.v99_r106_i1_coinapi_derived_day_bridge import (
    SCHEMA as DAY_SCHEMA, _source, digest,
)
from research.tools.v99_r106_i1_coinapi_quote_intake import (
    COLUMNS, SITE_UUID, _original_rows, nonnegative, ticks100ns,
)
from research.tools.v99_r106_i1_source_driven_entry_book import (
    _contract, _one_sunday, MIN_TENOR_MS, MAX_TENOR_MS,
)
from research.tools.v99_r106_i1_full_archive_intake import eligible
from research.tools.v99_r106_i1_original_intent_binding import bind
from research.verification.independent_v99_r106_i1_original_intent_oracle import (
    verify as independent_intents,
)
from research.tools.v99_r106_i1_train_numeric_gate import _fold
from research.tools.v99_r106_i1_local_tape_import import FIRST, END

SCHEMA = "V99_I1_COINAPI_ORIGINAL_180_ENTRY_BOOK_PARITY_V1"
AGE_US = 300_000_000
BOOK_FIELDS = ("symbol", "expiry_ms", "strike_usd", "bid_coin", "ask_coin",
               "bid_size_source_units", "ask_size_source_units",
               "venue_us", "arrival_us")


def _safe(root, path):
    root, path = Path(root), Path(path)
    if (not root.is_dir() or root.is_symlink() or not path.is_file()
            or path.is_symlink() or not path.resolve().is_relative_to(root.resolve())):
        raise ValueError("UNSAFE_COINAPI_ENTRY_SOURCE")
    return path


def verify_sunday(spec_path, original_root, derived_root, decision_ms):
    """Independent original 100ns scan versus separately derived daily parser.

    Fixture-callable helper. Public build() first enforces full licensed 661d
    original-byte chain and independent 180-intent binding.
    """
    spec_path = Path(spec_path)
    original_root, derived_root = Path(original_root), Path(derived_root)
    if type(decision_ms) is not int:
        raise ValueError("INVALID_COINAPI_ENTRY_DECISION_CLOCK")
    decision = datetime.fromtimestamp(decision_ms / 1000, timezone.utc)
    day = decision.date() - timedelta(days=1)
    if (decision.time().isoformat() != "00:00:00"
            or decision.weekday() != 0 or day.weekday() != 6
            or not FIRST <= day < END):
        raise ValueError("NONFIXED_OR_SEALED_COINAPI_ENTRY_DAY")
    _safe(spec_path.parent, spec_path)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if (not isinstance(spec, dict) or set(spec) != {"schema", "day", "sources"}
            or spec["schema"] != DAY_SCHEMA or spec["day"] != day.isoformat()
            or not isinstance(spec["sources"], list)
            or not 2 <= len(spec["sources"]) <= 4096):
        raise ValueError("INVALID_COINAPI_ENTRY_SPEC")
    start = int(datetime(day.year, day.month, day.day,
                         tzinfo=timezone.utc).timestamp()) * 10_000_000
    end = start + 86400 * 10_000_000
    seen_symbols, seen_paths, seen_keys = set(), set(), set()
    books = {"BTC": [], "ETH": []}
    invalid = {"BTC": 0, "ETH": 0}
    stale = {"BTC": 0, "ETH": 0}
    rows = 0
    for source in spec["sources"]:
        path, symbol = _source(source, day)
        _safe(original_root, path)
        if (symbol in seen_symbols or path.resolve() in seen_paths
                or source["source_key"] in seen_keys):
            raise ValueError("DUPLICATED_COINAPI_ENTRY_PARTITION")
        seen_symbols.add(symbol)
        seen_paths.add(path.resolve())
        seen_keys.add(source["source_key"])
        parsed = _contract(symbol)
        if parsed is None:
            raise ValueError("INVALID_COINAPI_ENTRY_CONTRACT")
        asset, expiry, strike = parsed
        prior = -1
        last = None
        local_rows = 0
        for raw, _ in _original_rows(path):
            local_rows += 1
            rows += 1
            if (raw.get(None) is not None
                    or any(raw.get(k) is None for k in COLUMNS)
                    or (raw["id_site_coinapi"]
                        and not SITE_UUID.fullmatch(raw["id_site_coinapi"]))):
                raise ValueError("MALFORMED_COINAPI_ENTRY_ROW")
            venue = ticks100ns(raw["time_exchange"])
            arrival = ticks100ns(raw["time_coinapi"])
            if (not start <= arrival < end or not 0 <= venue <= arrival
                    or arrival < prior):
                raise ValueError("NONCAUSAL_COINAPI_ENTRY_RECEIPT")
            prior = arrival
            bid, ask, bs, ass = (nonnegative(raw[k]) for k in
                                ("bid_px", "ask_px", "bid_sx", "ask_sx"))
            last = (venue // 10, (arrival + 9) // 10, local_rows,
                    bid, ask, bs, ass)
        if local_rows == 0:
            raise ValueError("EMPTY_COINAPI_ENTRY_PARTITION")
        # Protect against mutation between initial SHA check and stream EOF.
        _source(source, day)
        if not (MIN_TENOR_MS <= expiry - decision_ms <= MAX_TENOR_MS
                and datetime.fromtimestamp(expiry / 1000, timezone.utc).date() < END):
            continue
        venue_us, arrival_us, ordinal, bid, ask, bs, ass = last
        cutoff = decision_ms * 1000
        if not (0 <= cutoff - arrival_us <= AGE_US
                and 0 <= cutoff - venue_us <= AGE_US):
            stale[asset] += 1
            continue
        if not (0 < bid < ask and bs > 0 and ass > 0):
            invalid[asset] += 1
            continue
        books[asset].append({
            "symbol": symbol, "expiry_ms": expiry, "strike_usd": strike,
            "bid_coin": str(bid), "ask_coin": str(ask),
            "bid_size_source_units": str(bs),
            "ask_size_source_units": str(ass),
            "venue_us": venue_us, "arrival_us": arrival_us,
            "original_source_row_ordinal": ordinal,
        })
    if {s.split("-", 1)[0] for s in seen_symbols} != {"BTC", "ETH"}:
        raise ValueError("MISSING_COINAPI_ENTRY_BTC_ETH_PARTITION")
    for asset in ("BTC", "ETH"):
        books[asset].sort(key=lambda item: item["symbol"])

    derived = _safe(derived_root, derived_root / (day.isoformat() + ".csv.gz"))
    sidecar_path = _safe(derived_root, derived_root /
                         (day.isoformat() + ".coinapi-derived.json"))
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    if (sidecar.get("schema") != DAY_SCHEMA
            or sidecar.get("day") != day.isoformat()
            or sidecar.get("derived_gzip_sha256") != digest(derived)
            or type(sidecar.get("derived_rows")) is not int
            or sidecar["derived_rows"] != rows
            or {item["symbol"]: item["original_gzip_sha256"]
                for item in sidecar.get("original_sources", [])}
            != {item["symbol"]: item["sha256"] for item in spec["sources"]}):
        raise ValueError("UNBOUND_COINAPI_DERIVED_SUNDAY")
    derived_books, derived_invalid, derived_stale, count = _one_sunday(
        derived, rows, day, decision_ms)
    if count != rows or invalid != derived_invalid or stale != derived_stale:
        raise ValueError("COINAPI_ORIGINAL_DERIVED_ENTRY_COUNTS_DIVERGE")
    for asset in ("BTC", "ETH"):
        left = [{k: q[k] for k in BOOK_FIELDS} for q in books[asset]]
        right = [{k: q[k] for k in BOOK_FIELDS} for q in derived_books[asset]]
        # The merged derived CSV has a different row ordinal from each
        # original per-symbol partition. Compare the actual market fields.
        if left != right:
            raise ValueError("COINAPI_ORIGINAL_DERIVED_FULL_ENTRY_BOOK_DIVERGES")
    return {
        "day": day.isoformat(),
        "original_partition_count": len(spec["sources"]),
        "original_rows_scanned": rows,
        "original_spec_sha256_not_vendor_day": digest(spec_path),
        "derived_day_sha256_not_original": digest(derived),
        "books": books, "invalid": invalid, "stale": stale,
        "original_vendor_day_manifest_created": False,
        "economic_train_executed": False, "promotion_authorized": False,
    }



def bind_original_open_inventories(report, journal):
    """Bind BOTH scenario OPEN inventories to original CoinAPI prices and clocks.

    SOURCE-ONLY: original bid_sx/ask_sx are NOT native lots. Deliberately do
    not compare these unverified source sizes to journal bid_native_lots.
    Numeric wallet/fills must remain blocked pending independently authenticated
    lot conversion, fee/margin/index and execution evidence.
    """
    from decimal import Decimal, InvalidOperation
    from research.tools.v99_r106_i1_native_event_equity import SCHEMA as JOURNAL_SCHEMA
    if (not isinstance(report, dict) or report.get("schema") != SCHEMA
            or report.get("original_intents_checked") != 180
            or report.get("promotion_authorized") is not False
            or not isinstance(report.get("rows"), list)
            or len(report["rows"]) != 180):
        raise ValueError("UNTRUSTED_COINAPI_ORIGINAL_OPEN_GRID")
    if (not isinstance(journal, dict) or journal.get("schema") != JOURNAL_SCHEMA
            or set(journal.get("scenarios", {})) != {"severe", "supersevere"}):
        raise ValueError("INVALID_COINAPI_NATIVE_JOURNAL")
    books = {}
    for row in report["rows"]:
        key = (row.get("decision_ms"), row.get("asset"))
        if (key in books or type(key[0]) is not int
                or key[1] not in ("BTC", "ETH")
                or not isinstance(row.get("original_books"), list)):
            raise ValueError("DUPLICATE_OR_INVALID_COINAPI_ORIGINAL_GRID")
        books[key] = row["original_books"]
    expected_grid = {(int(d.timestamp() * 1000), asset)
                     for d in eligible(True) for asset in ("BTC", "ETH")}
    if len(books) != 180 or set(books) != expected_grid:
        raise ValueError("INCOMPLETE_COINAPI_ORIGINAL_OPEN_GRID")
    checked = {}
    for scenario in ("severe", "supersevere"):
        seen = set()
        count = 0
        for day in journal["scenarios"][scenario]:
            if not isinstance(day, dict) or not isinstance(day.get("events"), list):
                raise ValueError("INVALID_COINAPI_NATIVE_EVENT_DAY")
            for event in day["events"]:
                if not isinstance(event, dict):
                    raise ValueError("INVALID_COINAPI_NATIVE_EVENT")
                if event.get("kind") != "OPEN":
                    continue
                key = (event.get("at_ms"), event.get("asset"))
                if key in seen or key not in books or not books[key]:
                    raise ValueError("UNSCHEDULED_OR_DUPLICATE_COINAPI_OPEN")
                seen.add(key)
                expected = {q["symbol"]: q for q in books[key]}
                received = event.get("quotes")
                if (not isinstance(received, list)
                        or len(received) != len(expected)
                        or len(expected) != len(books[key])):
                    raise ValueError("COINAPI_OPEN_ORIGINAL_INVENTORY_MISMATCH")
                symbols = set()
                for quote in received:
                    if not isinstance(quote, dict):
                        raise ValueError("COINAPI_OPEN_INVALID_QUOTE")
                    symbol = quote.get("symbol")
                    if symbol in symbols or symbol not in expected:
                        raise ValueError("COINAPI_OPEN_ORIGINAL_INVENTORY_MISMATCH")
                    symbols.add(symbol)
                    source = expected[symbol]
                    try:
                        same = (quote.get("asset") == key[1]
                            and quote.get("expiry_ms") == source["expiry_ms"]
                            and all(Decimal(str(quote.get(dst))) ==
                                    Decimal(str(source[src])) for dst, src in (
                                        ("strike_usd", "strike_usd"),
                                        ("bid_coin", "bid_coin"),
                                        ("ask_coin", "ask_coin")))
                            and quote.get("venue_ms") == source["venue_us"] // 1000
                            and quote.get("arrival_ms") == source["arrival_us"] // 1000)
                    except (InvalidOperation, TypeError, ValueError):
                        same = False
                    if not same:
                        raise ValueError("COINAPI_OPEN_ORIGINAL_PRICE_CLOCK_MISMATCH")
                if symbols != set(expected):
                    raise ValueError("COINAPI_OPEN_ORIGINAL_INVENTORY_MISMATCH")
                count += 1
        checked[scenario] = count
    return {
        "status": "ORIGINAL_OPEN_PRICE_CLOCK_PARITY_ONLY_NO_NATIVE_LOT_CERTIFICATION",
        "scenario_opens_original_book_bound": checked,
        "source_quote_size_units_native_lots_certified": False,
        "original_index_fees_margin_delivery_certified": False,
        "economic_train_executed": False,
        "promotion_authorized": False,
        "validation_opened": False,
        "holdout_opened": False,
        "orders_enabled": False,
    }


def build(spec_root, original_root, derived_root, original_signal_path,
          *, license_document=None):
    """Nonfixture complete 180-book bridge; source parity, never native economics."""
    chain = verify_chain(spec_root, original_root, derived_root,
                         fixture=False, license_document=license_document)
    if chain["fixture"] is not False or chain["promotion_authorized"] is not False:
        raise ValueError("UNTRUSTED_COINAPI_ORIGINAL_CHAIN")
    original = bind(Path(original_signal_path))
    with tempfile.TemporaryDirectory(prefix="v99-coinapi-intents-") as tmp:
        path = Path(tmp) / "intents.json"
        path.write_text(json.dumps(original, sort_keys=True), encoding="utf-8")
        checked = independent_intents(original_signal_path, path)
    if (checked["original_intents_verified"] != 180
            or checked["positive_fixed_intents"] != original["positive_fixed_intents"]):
        raise ValueError("UNBOUND_COINAPI_FIXED_ORIGINAL_INTENTS")
    grid = [(int(d.timestamp() * 1000), asset)
            for d in eligible(True) for asset in ("BTC", "ETH")]
    if len(grid) != 180 or len(original["intents"]) != 180:
        raise ValueError("INVALID_COINAPI_180_TRAIN_GRID")
    result = []
    originals_scanned = 0
    for i in range(0, 180, 2):
        clock = grid[i][0]
        sunday = datetime.fromtimestamp(clock / 1000, timezone.utc).date()-timedelta(days=1)
        item = verify_sunday(Path(spec_root) / (sunday.isoformat()+".json"),
                             original_root, derived_root, clock)
        originals_scanned += item["original_rows_scanned"]
        for offset, asset in enumerate(("BTC", "ETH")):
            intent = original["intents"][i + offset]
            if (intent["decision_ms"], intent["asset"], intent["fold"]) != (
                    clock, asset, _fold(clock)):
                raise ValueError("UNBOUND_COINAPI_INTENT_FOLD")
            result.append({
                "decision_ms": clock, "asset": asset,
                "fold": intent["fold"], "signal": intent["signal"],
                "source_day": sunday.isoformat(),
                "original_spec_sha256_not_vendor_day":
                    item["original_spec_sha256_not_vendor_day"],
                "derived_day_sha256_not_original":
                    item["derived_day_sha256_not_original"],
                "source_rows_scanned": item["original_rows_scanned"],
                "last_eligible_invalid_books": item["invalid"][asset],
                "last_eligible_stale_books": item["stale"][asset],
                "original_books": item["books"][asset],
            })
    return {
        "schema": SCHEMA,
        "status": "COINAPI_ORIGINAL_FULL_OPEN_INVENTORY_PARITY_NO_NATIVE_ECONOMICS",
        "original_intents_checked": len(result),
        "original_sundays_independently_replayed": 90,
        "original_sunday_rows_scanned": originals_scanned,
        "original_vendor_files_byte_replayed": chain["original_vendor_files_byte_replayed"],
        "source_quote_units_native_lots_certified": False,
        "original_vendor_day_manifest_created": False,
        "derived_day_claimed_original": False,
        "historical_native_fee_margin_delivery_certified": False,
        "economic_train_executed": False,
        "original_complete_option_lifecycles_certified": 0,
        "freeze_authorized": False, "promotion_authorized": False,
        "validation_opened": False, "holdout_opened": False,
        "paper_publication_authorized": False, "orders_enabled": False,
        "rows": result,
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("spec_root")
    p.add_argument("original_root")
    p.add_argument("derived_root")
    p.add_argument("original_signal_json")
    p.add_argument("--license-document", required=True)
    args = p.parse_args()
    print(json.dumps(build(args.spec_root, args.original_root, args.derived_root,
                           args.original_signal_json,
                           license_document=args.license_document), sort_keys=True))
