"""Independent cross-scenario ORIGINAL market-path oracle (source uncertified).

No production event replay/selector imports. Equal scenario inputs are only
necessary for honest cost comparisons, not proof of exchange provenance.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

NUMERIC = ("strike_usd", "bid_coin", "ask_coin", "bid_native_lots",
           "ask_native_lots", "index_usd")
FIELDS = ("asset", "symbol", "expiry_ms", "strike_usd", "bid_coin",
          "ask_coin", "bid_native_lots", "ask_native_lots",
          "venue_ms", "arrival_ms", "index_usd")
KINDS = ("OPEN", "MARK", "SETTLE_BATCH")


def decimal(value):
    if isinstance(value, bool):
        raise AssertionError("ORACLE_BOOLEAN_MARKET_NUMBER")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise AssertionError("ORACLE_BAD_MARKET_NUMBER") from exc
    if not result.is_finite():
        raise AssertionError("ORACLE_NONFINITE_MARKET_NUMBER")
    return result


def book(raw):
    if not isinstance(raw, dict) or any(key not in raw for key in FIELDS):
        raise AssertionError("ORACLE_INCOMPLETE_MARKET_BOOK")
    return tuple(decimal(raw[key]) if key in NUMERIC else raw[key]
                 for key in FIELDS)


def verify(journal):
    if journal.get("fixture") is not False:
        raise AssertionError("ORACLE_NONFIXTURE_JOURNAL_REQUIRED")
    scenarios = journal.get("scenarios")
    if not isinstance(scenarios, dict) or set(scenarios) != {"severe", "supersevere"}:
        raise AssertionError("ORACLE_TWO_SCENARIOS_REQUIRED")
    all_events = {}
    for scenario in ("severe", "supersevere"):
        by_kind = {k: {} for k in KINDS}
        for day in scenarios[scenario]:
            for event in day["events"]:
                kind = event["kind"]
                if kind not in by_kind:
                    continue
                at, asset = event["at_ms"], event["asset"]
                if kind == "OPEN":
                    inventory = event["quotes"]
                    if not isinstance(inventory, list):
                        raise AssertionError("ORACLE_INVALID_OPEN_INVENTORY")
                    observation = tuple(sorted((book(q) for q in inventory),
                                               key=lambda item: item[1]))
                    key = (at, asset)
                elif kind == "MARK":
                    short, long = book(event["short"]), book(event["long"])
                    key = (at, asset, short[1], long[1])
                    observation = (short, long)
                else:
                    key = (at, asset)
                    observation = decimal(event["delivery_index_usd"])
                previous = by_kind[kind].get(key)
                if previous is not None and previous != observation:
                    raise AssertionError("ORACLE_INTRA_SCENARIO_MARKET_DIVERGENCE")
                by_kind[kind][key] = observation
        all_events[scenario] = by_kind
    a, b = (all_events[s] for s in ("severe", "supersevere"))
    counts = {}
    for kind in KINDS:
        keys = a[kind].keys() & b[kind].keys()
        for key in keys:
            if a[kind][key] != b[kind][key]:
                raise AssertionError("ORACLE_CROSS_SCENARIO_" + kind + "_MISMATCH")
        counts[kind] = len(keys)
    return {
        "independent_common_open_inventories": counts["OPEN"],
        "independent_common_mark_books": counts["MARK"],
        "independent_common_delivery_indices": counts["SETTLE_BATCH"],
        "scenario_exposure_divergence_allowed": True,
        "original_source_certified": False,
        "economic_train_certified": False,
        "promotion_authorized": False,
    }
