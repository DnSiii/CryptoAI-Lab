"""Source-to-engine ORIGINAL I1 entry book export. No strategy, economics or orders.

Exports every causally eligible last-known Deribit quote (not a selected trade)
from the verified 91-Sunday legacy or 90-Sunday fixed-tenor TRAIN archive. An executable portfolio must still
provide native fees, full holding-period books, settlement, and margin evidence.
"""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
import math
import sys
from datetime import timedelta
from pathlib import Path

from research.tools.v99_r106_i1_full_archive_intake import (
    END, REQUIRED, eligible, evaluate, file_digest, instrument, safe_path, native_contracts, historical_price_grid_ok, synchronized_strikes,
)

def export_books(root):
    root = Path(root)
    gate = evaluate(root)  # checksum, complete schedule, original five folds
    native = None if gate["fixture"] else native_contracts(root)
    native_sources = (None if native is None else json.loads(
        (root / "native_instrument_registry.json").read_text(encoding="utf-8"))["sources"])
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    fixed = manifest["schema"] == "I1_FIXED_TENOR_TRAIN_SUNDAY_ARCHIVE_V1"
    books = []
    for week, (decision, item) in enumerate(zip(eligible(fixed), manifest["days"])):
        cutoff = int(decision.timestamp() * 1_000_000) - 300_000_000
        end = int(decision.timestamp() * 1_000_000)
        path = safe_path(root, item["file"])
        if file_digest(path) != item["sha256"]:
            raise ValueError("SOURCE_CHANGED_AFTER_INTAKE")
        opener = gzip.open if path.name.endswith(".gz") else open
        latest = {}
        previous_arrival = None
        with opener(path, "rt", newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            if not set(REQUIRED).issubset(reader.fieldnames or ()):
                raise ValueError("MISSING_ORIGINAL_QUOTE_FIELDS")
            for row in reader:
                arrival, exchange = int(row["local_timestamp"]), int(row["timestamp"])
                if not (int((decision-timedelta(days=1)).timestamp()*1_000_000)
                        <= arrival < end and exchange <= arrival):
                    raise ValueError("OUTSIDE_FROZEN_TRAIN_SOURCE")
                if previous_arrival is not None and arrival < previous_arrival:
                    raise ValueError("OUT_OF_ORDER_ORIGINAL_CAPTURE")
                previous_arrival = arrival
                if arrival < cutoff:
                    continue
                # Preserve last physical capture row, including invalid updates.
                latest[row["symbol"]] = ((arrival, exchange), row)
        for symbol, ((arrival, exchange), row) in sorted(latest.items()):
            parsed = instrument(symbol)
            if parsed is None:
                continue
            asset, expiry, strike = parsed
            if not (exchange >= cutoff and
                    timedelta(days=(28 if fixed else 21)) <= expiry-decision
                    <= timedelta(days=(35 if fixed else 45))
                    and expiry < END):
                continue
            try:
                bid, ask, bid_size, ask_size = (float(row[k]) for k in
                    ("bid_price", "ask_price", "bid_amount", "ask_amount"))
            except (ValueError, TypeError):
                continue
            if not (all(map(math.isfinite, (bid, ask, bid_size, ask_size)))
                    and 0 < bid < ask and bid_size > 0 and ask_size > 0):
                continue
            meta = None
            if native is not None:
                meta = native[asset].get(symbol)
                if (meta is None
                    or meta["creation_timestamp"] > int(decision.timestamp()*1000)
                    or meta["expiration_timestamp"] != int(expiry.timestamp()*1000)
                    or float(meta["strike"]) != strike
                    or meta["settlement_currency"] != asset
                    or any(meta[k] is None or float(meta[k]) <= 0 for k in
                           ("contract_size","min_trade_amount","tick_size"))
                    or not historical_price_grid_ok(meta, decision, bid, ask)):
                    continue
            books.append({
                "decision_utc": decision.isoformat(),
                "fold": gate["weekly"][week]["fold"],
                "asset": asset, "symbol": symbol, "strike_usd": strike,
                "expiry_utc": expiry.isoformat(),
                "bid_coin": bid, "ask_coin": ask,
                "bid_size_source_units": bid_size,
                "ask_size_source_units": ask_size,
                "exchange_us": exchange, "arrival_us": arrival,
                "source_file": item["file"], "source_sha256": item["sha256"],
                # Raw original Deribit registry fields, never inferred from BBO
                # size units. An archived registry is NOT as-of fee/margin proof.
                "native_contract_terms": (None if meta is None else {
                    k: meta[k] for k in ("contract_size", "min_trade_amount",
                                         "tick_size", "settlement_currency",
                                         "creation_timestamp", "expiration_timestamp",
                                         "tick_size_steps")}),
                "native_registry_source_sha256": (None if native_sources is None
                    else native_sources[asset]["original_raw_sha256"]),
            })
    grouped = {}
    for quote in books:
        key = (quote["decision_utc"], quote["asset"], quote["expiry_utc"])
        grouped.setdefault(key, set()).add(quote["strike_usd"])
    pairs = sum(any(d == week["decision_utc"] and a == asset and len(strikes) >= 2
                    for (d, a, _), strikes in grouped.items())
                for week in gate["weekly"] for asset in ("BTC", "ETH"))
    if pairs != gate["two_strike_asset_weeks"]:
        raise ValueError("SOURCE_TO_ENGINE_PAIR_RECONCILIATION_FAILED")
    grouped_times = {}
    for quote in books:
        key = (quote["decision_utc"], quote["asset"], quote["expiry_utc"])
        grouped_times.setdefault(key, []).append(quote)
    # Use the already independently fuzzed exact two-clock bucket matcher.
    # Quadratic all-pairs scans are not viable for dense original 661-day tapes.
    synchronized = {
        (d, a) for (d, a, _), quotes in grouped_times.items()
        if synchronized_strikes([
            (q["strike_usd"], q["arrival_us"], q["exchange_us"])
            for q in quotes
        ])
    }
    if len(synchronized) != gate["synchronized_two_strike_asset_weeks"]:
        raise ValueError("SOURCE_TO_ENGINE_SYNCHRONIZED_PAIR_RECONCILIATION_FAILED")
    return {
        "schema": "I1_ORIGINAL_ENTRY_BOOK_EXPORT_V1",
        "status": "SYNTHETIC_NOT_ECONOMIC" if gate["fixture"] else
                  "ORIGINAL_BOOKS_NOT_CERTIFIED_EXECUTION",
        "fixture": gate["fixture"],
        "native_registry_verified": native is not None,
        "native_terms_bound_to_original_bytes": native is not None,
        "historical_dated_price_grid_checked": native is not None,
        "historical_native_lot_asof_certified": False,
        "historical_fee_asof_certified": False,
        "quote_size_to_native_lot_conversion_certified": False,
        "historical_fee_margin_certified": False,
        "source_pairs": pairs, "synchronized_source_pairs": len(synchronized),
        "synchronized_max_skew_us": 1_000_000,
        "source_scope": gate["source_scope"],
        "required_pairs": gate["required_asset_weeks"],
        "quotes": books,
        "missing": ["historical full quote entitlement", "full holding-period quotes",
                    "historical contract multipliers and lot sizes",
                    "authenticated account fee tier", "coin margin/liquidation rules",
                    "size-aware fill model", "independent complete economic TRAIN"],
        "economic_train_executed": False, "validation_opened": False,
        "holdout_opened": False, "promotion_authorized": False,
        "orders_enabled": False,
    }

def main(root, out):
    result = export_books(root)
    dest = Path(out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "original_quotes": len(result["quotes"]),
                      "source_pairs": result["source_pairs"],
                      "synchronized_source_pairs": result["synchronized_source_pairs"],
                      "economic_train_executed": False,
                      "promotion_authorized": False}))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_entry_book_export ROOT OUT")
    main(sys.argv[1], sys.argv[2])
