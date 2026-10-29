"""Bidirectional original-source lifecycle parity BEFORE provisional I1 NAV.

This checks only original BBO identity and event completeness. It cannot
authenticate underlying index, native lot units, historical fees, margin,
delivery index, fills, profitability, or any promotion. Preregistered in
V99_R106_I1_ORIGINAL_SPINE_TO_NATIVE_JOURNAL_PARITY_PREREG_20261029.md.
"""
from __future__ import annotations

from research.tools.v99_r106_i1_fixed_vertical_bridge import select_fixed_vertical
from research.tools.v99_r106_i1_native_event_equity import _quote
from research.tools.v99_r106_i1_native_coin_account_replay import D
from research.tools.v99_r106_i1_source_to_mark_event_spine import compile_spine

SCHEMA = "V99_I1_ORIGINAL_SPINE_NATIVE_JOURNAL_PARITY_V1"


def _market_equal(native, source):
    """Compare literal original BBO/size/arrival/venue, never caller index."""
    if not isinstance(native, dict) or not isinstance(source, dict):
        return False
    try:
        return (
            native["symbol"] == source["symbol"]
            and D(native["bid_coin"]) == D(source["bid_coin"])
            and D(native["ask_coin"]) == D(source["ask_coin"])
            and D(native["bid_native_lots"]) == D(source["bid_size_source_units"])
            and D(native["ask_native_lots"]) == D(source["ask_size_source_units"])
            and native["venue_ms"] == source["venue_us"] // 1000
            and native["arrival_ms"] == source["arrival_us"] // 1000
        )
    except (KeyError, TypeError, ValueError):
        return False


def _key(kind, at, asset, name):
    if type(at) is not int or asset not in ("BTC", "ETH") or not isinstance(name, str):
        raise ValueError("INVALID_ORIGINAL_SPINE_EVENT_IDENTITY")
    return kind, at, asset, name


def verify_source_spine(root, original_entry_report, journal):
    """Reject missing/extra or altered original held-contract events before NAV.

    Scenario-specific OPEN plans are derived from the frozen selector applied
    to the COMPLETE original OPEN inventory, never from caller-provided pair
    choices. Both cost scenarios are checked separately, including no-trade.
    """
    if (not isinstance(journal, dict) or journal.get("fixture") is not False
            or set(journal.get("scenarios", {})) != {"severe", "supersevere"}):
        raise ValueError("NONFIXTURE_TWO_SCENARIO_SPINE_REQUIRED")
    result = {}
    for scenario in ("severe", "supersevere"):
        plan = []
        actual = {}
        for day in journal["scenarios"][scenario]:
            for event in day["events"]:
                kind, at, asset = event["kind"], event["at_ms"], event["asset"]
                if kind == "OPEN":
                    quotes = [_quote(q) for q in event["quotes"]]
                    chosen = select_fixed_vertical(event["signal"], quotes)
                    if chosen is None:
                        raise ValueError("ORIGINAL_SPINE_FIXED_SELECTOR_NO_POSITION")
                    short, long = chosen
                    name = event["position_id"]
                    plan.append({
                        "position_id": name, "decision_ms": at, "asset": asset,
                        "short_symbol": short.symbol, "long_symbol": long.symbol,
                    })
                    key = _key("OPEN", at, asset, name)
                    value = event
                    if key in actual:
                        raise ValueError("DUPLICATE_NATIVE_SPINE_EVENT")
                    actual[key] = value
                elif kind == "MARK":
                    key = _key("MARK", at, asset, event["position_id"])
                    if key in actual:
                        raise ValueError("DUPLICATE_NATIVE_SPINE_EVENT")
                    actual[key] = event
                elif kind == "SETTLE_BATCH":
                    for name in event["position_ids"]:
                        key = _key("SETTLEMENT_DUE", at, asset, name)
                        if key in actual:
                            raise ValueError("DUPLICATE_NATIVE_SPINE_EVENT")
                        actual[key] = event
                else:
                    raise ValueError("UNREGISTERED_NATIVE_SPINE_EVENT")
        expected = {}
        if plan:
            spine = compile_spine(root, original_entry_report, plan)
            for day in spine["days"]:
                for event in day["market_events"]:
                    kind = event["kind"]
                    if kind == "OPEN_SOURCE_ONLY":
                        category = "OPEN"
                    elif kind == "MARK_SOURCE_ONLY":
                        category = "MARK"
                    elif kind == "SETTLEMENT_DUE_SOURCE_ONLY":
                        category = "SETTLEMENT_DUE"
                    else:
                        raise ValueError("UNKNOWN_ORIGINAL_SPINE_KIND")
                    key = _key(category, event["at_ms"], event["asset"], event["position_id"])
                    if key in expected:
                        raise ValueError("DUPLICATE_ORIGINAL_SPINE_EVENT")
                    expected[key] = event
        if set(actual) != set(expected):
            missing = len(set(expected) - set(actual))
            extra = len(set(actual) - set(expected))
            raise ValueError(
                f"ORIGINAL_SPINE_NATIVE_EVENT_SCHEDULE_MISMATCH:missing={missing}:extra={extra}"
            )
        marks = 0
        for key, source in expected.items():
            event = actual[key]
            if key[0] == "MARK":
                marks += 1
                if (not _market_equal(event["short"], source["short"])
                        or not _market_equal(event["long"], source["long"])):
                    raise ValueError("ORIGINAL_SPINE_HELD_MARK_BBO_MISMATCH")
            elif key[0] == "OPEN":
                books = source["candidate_inventory"]
                native = event["quotes"]
                original_by_symbol = {q["symbol"]: q for q in books}
                if (len(original_by_symbol) != len(books)
                        or len(native) != len(books)
                        or {q["symbol"] for q in native} != set(original_by_symbol)
                        or any(not _market_equal(q, original_by_symbol[q["symbol"]])
                               for q in native)):
                    raise ValueError("ORIGINAL_SPINE_FULL_OPEN_BBO_MISMATCH")
            else:
                if not source["delivery_index_missing"]:
                    raise ValueError("FORGED_ORIGINAL_DELIVERY_INDEX_CERTIFICATION")
        result[scenario] = {
            "positions": len(plan), "source_mark_events": marks,
            "source_expiry_due_events": len(plan),
            "native_event_schedule_matched": True,
        }
    return {
        "schema": SCHEMA, "status": "ORIGINAL_BBO_EVENT_SCHEDULE_ONLY",
        "scenarios": result,
        "historical_native_economics_certified": False,
        "independent_original_fills_verified": False,
        "promotion_authorized": False,
        "validation_opened": False, "holdout_opened": False,
        "orders_enabled": False,
    }
