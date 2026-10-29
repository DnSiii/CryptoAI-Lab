"""Compile ORIGINAL 661d held-option as-of OPEN/MARK and expiry-due source spine.

NO index, lot, native fees, margin, liquidation, delivery, fills, NAV or ROI.
Requires licensed complete original tape; no synthetic fallback.
Prereg: V99_R106_I1_SOURCE_TO_MARK_EVENT_SPINE_PREREG_20261028.md.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.tools.v99_r106_i1_native_coin_account_replay import D
from research.tools.v99_r106_i1_original_event_quote_identity import (
    _original_manifest, _last_original_quotes,
)
from research.tools.v99_r106_i1_source_driven_entry_book import _contract
from research.tools.v99_r106_i1_train_numeric_gate import DAYS, _expected_clock
from research.tools.v99_r106_d1_real_train_source_join import FOLD_EDGES
from research.verification.independent_v99_r106_i1_source_entry_book_oracle import verify

SCHEMA = "V99_I1_SOURCE_DRIVEN_661D_MARK_EVENT_SPINE_V1"
FRESH_US = 300_000_000
# Immutable four intraday TRAIN fold boundaries, NOT daily NAV approximations.
EXACT_FOLD_EDGES = tuple(FOLD_EDGES[1:-1])


def _held_mark_clocks(decision_ms, expiry_ms):
    """Original source requests for daily NAV and active-position exact folds."""
    daily = (_expected_clock(i) for i in range(DAYS))
    return tuple(sorted({clock for clock in (*daily, *EXACT_FOLD_EDGES)
                         if decision_ms <= clock < expiry_ms}))


def _receipt(source, clock, symbol):
    if source is None:
        raise ValueError("MISSING_ORIGINAL_HELD_CONTRACT_DAILY_MARK:" + symbol)
    arrival, _, ordinal, venue, row = source
    if (row["symbol"] != symbol or row["exchange"] != "deribit"
            or not 0 <= venue <= arrival < clock * 1000
            or clock * 1000 - arrival > FRESH_US
            or clock * 1000 - venue > FRESH_US):
        raise ValueError("STALE_FUTURE_OR_WRONG_ORIGINAL_HELD_MARK:" + symbol)
    try:
        bid, ask, bs, a_s = [D(row[key]) for key in
                            ("bid_price", "ask_price", "bid_amount", "ask_amount")]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("INVALID_LAST_HELD_MARK:" + symbol) from exc
    if not (0 < bid < ask and bs > 0 and a_s > 0):
        raise ValueError("LAST_INVALID_HELD_MARK_REVOKES_EARLIER:" + symbol)
    return {
        "symbol": symbol, "bid_coin": str(bid), "ask_coin": str(ask),
        "bid_size_source_units": str(bs), "ask_size_source_units": str(a_s),
        "venue_us": venue, "arrival_us": arrival,
        "original_source_row_ordinal": ordinal,
    }


def compile_spine(root, entry_report, positions):
    """Original BBO/size/clock events, not a native wallet journal.

    Positions are an explicit *unverified* research plan. No strike selection
    or risk veto is certified without independent underlying-index receipts.
    """
    files, manifest_sha = _original_manifest(root)
    checked = verify(root, entry_report)
    if (checked["independently_verified_asset_weeks"] != 180
            or entry_report["source_manifest_sha256"] != manifest_sha):
        raise ValueError("UNBOUND_ORIGINAL_ENTRY_SOURCE")
    if not isinstance(positions, list) or not positions:
        raise ValueError("NONEMPTY_FIXED_POSITION_PLAN_REQUIRED")
    entry_rows = {(r["decision_ms"], r["asset"]): r for r in entry_report["rows"]}
    fixed = set()
    names = set()
    plan = []
    for item in positions:
        if not isinstance(item, dict) or set(item) != {
                "position_id", "decision_ms", "asset", "short_symbol", "long_symbol"}:
            raise ValueError("INVALID_FIXED_POSITION_PLAN_ROW")
        name, clock, asset = item["position_id"], item["decision_ms"], item["asset"]
        key = (clock, asset)
        if (not isinstance(name, str) or not name or name in names
                or key in fixed or key not in entry_rows
                or entry_rows[key]["signal"] != "POSITIVE_EX_ANTE_PREMIUM"):
            raise ValueError("DUPLICATE_UNSCHEDULED_OR_NONPOSITIVE_OPEN")
        short_id = _contract(item["short_symbol"])
        long_id = _contract(item["long_symbol"])
        if (short_id is None or long_id is None
                or short_id[0] != asset or long_id[0] != asset
                or short_id[1] != long_id[1]
                or D(short_id[2]) <= D(long_id[2])):
            raise ValueError("WRONG_ASSET_EXPIRY_OR_VERTICAL_IDENTITY")
        books = {q["symbol"]: q for q in entry_rows[key]["original_books"]}
        if (item["short_symbol"] not in books
                or item["long_symbol"] not in books):
            raise ValueError("POSITION_NOT_IN_FULL_ORIGINAL_OPEN_BOOK")
        short = books[item["short_symbol"]]
        long = books[item["long_symbol"]]
        if (abs(short["arrival_us"] - long["arrival_us"]) > 1_000_000
                or abs(short["venue_us"] - long["venue_us"]) > 1_000_000
                or D(short["bid_coin"]) <= D(long["ask_coin"])):
            raise ValueError("UNSYNCHRONIZED_OR_NONCREDIT_ORIGINAL_OPEN")
        names.add(name)
        fixed.add(key)
        plan.append({**item, "expiry_ms": short_id[1],
                     "open_full_original_books": entry_rows[key]["original_books"]})
    plan.sort(key=lambda p: (p["decision_ms"], p["asset"]))

    # Original daily MARK requests must be same literal contracts as OPEN.
    # Expiry at 08:00 UTC: no mark at 23:59:59 on expiry day.
    requests = {}
    for p in plan:
        for clock in _held_mark_clocks(p["decision_ms"], p["expiry_ms"]):
            for symbol in (p["short_symbol"], p["long_symbol"]):
                requests[(clock, p["asset"], symbol)] = None
    originals = _last_original_quotes(files, requests)
    marks = {}
    for (clock, asset, symbol), _ in requests.items():
        marks[(clock, asset, symbol)] = _receipt(
            originals.get((clock, asset, symbol)), clock, symbol)

    days = []
    mark_count = 0
    intraday_fold_mark_count = 0
    for i in range(DAYS):
        clock = _expected_clock(i)
        day_start = clock - 86_399_000
        events = []
        for p in plan:
            if day_start <= p["decision_ms"] <= clock:
                events.append({
                    "kind": "OPEN_SOURCE_ONLY", "at_ms": p["decision_ms"],
                    "asset": p["asset"], "position_id": p["position_id"],
                    "signal_source": "ORIGINAL_FIXED_180_GRID",
                    "candidate_inventory": p["open_full_original_books"],
                    "short_symbol_unverified_selection": p["short_symbol"],
                    "long_symbol_unverified_selection": p["long_symbol"],
                })
            if p["decision_ms"] <= clock < p["expiry_ms"]:
                events.append({
                    "kind": "MARK_SOURCE_ONLY", "at_ms": clock,
                    "asset": p["asset"], "position_id": p["position_id"],
                    "short": marks[(clock, p["asset"], p["short_symbol"])],
                    "long": marks[(clock, p["asset"], p["long_symbol"])],
                })
                mark_count += 1
            # Every active held option must have its own literal pre-edge
            # two-sided original quote at the four exact intraday TRAIN folds.
            # Missing/stale quotes fail in _receipt above; never interpolate.
            for edge in EXACT_FOLD_EDGES:
                if (day_start <= edge <= clock
                        and p["decision_ms"] <= edge < p["expiry_ms"]):
                    events.append({
                        "kind": "MARK_SOURCE_ONLY", "at_ms": edge,
                        "asset": p["asset"], "position_id": p["position_id"],
                        "short": marks[(edge, p["asset"], p["short_symbol"])],
                        "long": marks[(edge, p["asset"], p["long_symbol"])],
                    })
                    intraday_fold_mark_count += 1
            if day_start <= p["expiry_ms"] <= clock:
                events.append({
                    "kind": "SETTLEMENT_DUE_SOURCE_ONLY", "at_ms": p["expiry_ms"],
                    "asset": p["asset"], "position_id": p["position_id"],
                    "delivery_index_missing": True,
                })
        events.sort(key=lambda e: (e["at_ms"], e["kind"], e["position_id"]))
        days.append({"ts_ms": clock, "market_events": events})
    return {
        "schema": SCHEMA, "status": "ORIGINAL_MARKET_SPINE_ONLY_NOT_ECONOMIC_JOURNAL",
        "original_manifest_sha256": manifest_sha,
        "original_fixed_entry_asset_weeks_verified": 180,
        "unverified_position_plan_count": len(plan),
        "same_contract_daily_marks": mark_count,
        "same_contract_exact_intraday_fold_marks": intraday_fold_mark_count,
        "same_contract_all_marks": mark_count + intraday_fold_mark_count,
        "expiry_due_count": len(plan), "days": days,
        "original_underlying_index_authenticated": False,
        "original_native_lot_conversion_authenticated": False,
        "historical_native_fees_margin_liquidation_authenticated": False,
        "original_delivery_index_authenticated": False,
        "source_plan_selection_authenticated": False,
        "original_execution_fills_authenticated": False,
        "native_economic_train_executed": False,
        "original_complete_option_lifecycles_certified": 0,
        "validation_opened": False, "holdout_opened": False,
        "freeze_authorized": False, "promotion_authorized": False,
        "orders_enabled": False, "paper_publication_authorized": False,
    }


def main(root, entry_json, positions_json, output_json):
    entry = json.loads(Path(entry_json).read_text(encoding="utf-8"))
    plan = json.loads(Path(positions_json).read_text(encoding="utf-8"))
    result = compile_spine(root, entry, plan)
    Path(output_json).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "original_mark_events": result["same_contract_daily_marks"],
                      "certified_lifecycles": 0, "promotion_authorized": False}))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_source_to_mark_event_spine ORIGINAL_ROOT ENTRY_BOOK_JSON FIXED_PLAN_JSON OUT_JSON")
    main(*sys.argv[1:])
