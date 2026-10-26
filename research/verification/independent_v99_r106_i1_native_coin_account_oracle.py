"""Independent Decimal reference for I1 native coin wallet traces.

Never imports production ledger; validates arithmetic only, not source license,
historical fee/margin authenticity, fill probability or economic profitability.
"""
from decimal import Decimal, InvalidOperation


def d(x):
    if isinstance(x, bool):
        raise AssertionError("BOOLEAN_REFERENCE_INPUT")
    try:
        y = Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise AssertionError("INVALID_REFERENCE_INPUT") from exc
    if not y.is_finite():
        raise AssertionError("NONFINITE_REFERENCE_INPUT")
    return y


def audit(trace, observed):
    if trace.get("asset") not in ("BTC", "ETH") or trace.get("scenario") not in (
            "severe", "supersevere"):
        raise AssertionError("INVALID_TRACE_ASSET_OR_SCENARIO")
    cash = d(trace["initial_coin"])
    if cash <= 0:
        raise AssertionError("INVALID_INITIAL_COIN")
    initial = cash
    reserve = Decimal(0)
    positions = {}
    marks = {}
    settled = []
    last_clock = 0
    snapshots = []
    for event in trace["events"]:
        typ = event["kind"]
        t = int(event["at_ms"])
        if t < last_clock:
            raise AssertionError("NONCHRONOLOGICAL_REFERENCE")
        last_clock = t
        name = event.get("name")
        if typ == "open":
            if positions:
                if set(marks) != set(positions) or any(
                        mark_t != t for _, mark_t, _ in marks.values()):
                    raise AssertionError("PRETRADE_REFERENCE_MARK_REQUIRED")
                nav = cash-sum((m[0] for m in marks.values()), Decimal(0))
                maintenance = sum((p[4] for p in positions.values()), Decimal(0))
                if nav < maintenance:
                    raise AssertionError("PRETRADE_REFERENCE_MAINTENANCE_BREACH")
            if name in positions or name in settled:
                raise AssertionError("DUPLICATE_REFERENCE_POSITION")
            qty, high, low = d(event["qty"]), d(event["high"]), d(event["low"])
            margin = d(event["margin_coin"])
            maintenance = d(event["maintenance_coin"])
            if not (qty > 0 and high > low > 0 and margin >= maintenance > 0):
                raise AssertionError("BAD_REFERENCE_CONTRACT")
            credit = qty*(d(event["short_bid_coin"])-d(event["long_ask_coin"]))
            credit -= d(event["entry_fees_coin"])+d(event["entry_slippage_coin"])
            if credit <= 0:
                raise AssertionError("NONPOSITIVE_REFERENCE_PREMIUM")
            cash += credit
            reserve += margin
            if cash < reserve:
                raise AssertionError("REUSED_REFERENCE_COIN")
            positions[name] = (qty, high, low, margin, maintenance, int(event["expiry_ms"]))
            marks.pop(name, None)
        elif typ == "mark":
            if name not in positions:
                raise AssertionError("MISSING_REFERENCE_MARK")
            qty = positions[name][0]
            liability = max(Decimal(0), qty*(d(event["short_ask_coin"])-
                                            d(event["long_bid_coin"])))
            liability += d(event["exit_fees_coin"])+d(event["exit_slippage_coin"])
            marks[name] = (liability, t, d(event["index_usd"]))
        elif typ == "nav":
            if set(marks) != set(positions) or any(
                    mark_t != t for _, mark_t, _ in marks.values()):
                raise AssertionError("MISSING_OR_STALE_REFERENCE_MARK")
            indices = {idx for _, _, idx in marks.values()}
            if len(indices) != 1:
                raise AssertionError("INCONSISTENT_REFERENCE_INDEX")
            nav = cash-sum((m[0] for m in marks.values()), Decimal(0))
            maintenance = sum((p[4] for p in positions.values()), Decimal(0))
            if nav < maintenance:
                raise AssertionError("REFERENCE_MAINTENANCE_BREACH")
            snapshots.append({"nav_coin": str(nav),
                              "nav_usd_equivalent_at_source_index": str(
                                  nav*next(iter(indices)))})
        elif typ == "settle":
            if name not in positions:
                raise AssertionError("MISSING_REFERENCE_SETTLEMENT")
            qty, high, low, margin, _, expiry = positions[name]
            if t != expiry:
                raise AssertionError("NONCONTRACTUAL_REFERENCE_SETTLEMENT")
            idx = d(event["delivery_index_usd"])
            if idx <= 0:
                raise AssertionError("INVALID_REFERENCE_INDEX")
            due = qty*(max(high-idx, Decimal(0))-max(low-idx, Decimal(0)))/idx
            cash -= due+d(event["delivery_fee_coin"])
            reserve -= margin
            del positions[name]
            marks.pop(name, None)
            settled.append(name)
            if cash < reserve:
                raise AssertionError("INSOLVENT_REFERENCE_SETTLEMENT")
        else:
            raise AssertionError("UNKNOWN_REFERENCE_EVENT")
    if (str(cash) != str(d(observed["cash_coin"]))
            or str(reserve) != str(d(observed["reserved_coin"]))
            or set(positions) != set(observed["open_position_ids"])
            or settled != observed["settled_ids"]
            or len(snapshots) != len(observed["snapshots"])):
        raise AssertionError("INDEPENDENT_COIN_JOURNAL_MISMATCH")
    for ref, got in zip(snapshots, observed["snapshots"]):
        if (d(ref["nav_coin"]) != d(got["nav_coin"])
                or d(ref["nav_usd_equivalent_at_source_index"]) != d(
                    got["nav_usd_equivalent_at_source_index"])):
            raise AssertionError("INDEPENDENT_COIN_NAV_MISMATCH")
    if observed.get("historical_economic_train") is not False or observed.get(
            "promotion_authorized") is not False:
        raise AssertionError("FALSE_ECONOMIC_CERTIFICATION")
    return {"independent_coin_account_replay": "MATCH",
            "events": len(trace["events"]),
            "snapshots": len(snapshots),
            "historical_economic_train": False,
            "promotion_authorized": False}
