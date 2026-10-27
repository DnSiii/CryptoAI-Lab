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
            # Independently reject impossible BBO sides before cash accounting.
            # A self-consistent forged wallet is not evidence of a real quote.
            short_bid = d(event["short_bid_coin"])
            short_ask = d(event["short_ask_coin"])
            long_bid = d(event["long_bid_coin"])
            long_ask = d(event["long_ask_coin"])
            if not (Decimal(0) < short_bid < short_ask
                    and Decimal(0) < long_bid < long_ask):
                raise AssertionError("REFERENCE_INVALID_OPEN_BBO")
            opening_fee = d(event["entry_fees_coin"])
            opening_slippage = d(event["entry_slippage_coin"])
            if opening_fee < 0 or opening_slippage < 0:
                raise AssertionError("REFERENCE_NEGATIVE_OPENING_COST")
            credit = qty*(d(event["short_bid_coin"])-d(event["long_ask_coin"]))
            credit -= opening_fee+opening_slippage
            if credit <= 0:
                raise AssertionError("NONPOSITIVE_REFERENCE_PREMIUM")
            cash += credit
            reserve += margin
            if cash < reserve:
                raise AssertionError("REUSED_REFERENCE_COIN")
            entry_index = d(event["index_usd"])
            if entry_index <= 0:
                raise AssertionError("INVALID_REFERENCE_ENTRY_INDEX")
            if positions and any(old_idx != entry_index for _, _, old_idx in marks.values()):
                raise AssertionError("POSTENTRY_REFERENCE_UNBOUND_INDEX")
            # Independent lower-bound reconstruction: immediate two-sided
            # closing cost from the ORIGINAL entry book, with zero assumed
            # exit fees. This is a necessary, never sufficient, solvency gate.
            immediate_due = max(
                Decimal(0), qty*(d(event["short_ask_coin"])-d(event["long_bid_coin"])))
            outstanding_due = sum((m[0] for m in marks.values()), Decimal(0))
            prior_maintenance = sum((p[4] for p in positions.values()), Decimal(0))
            if cash-outstanding_due-immediate_due < prior_maintenance+maintenance:
                raise AssertionError("POSTENTRY_REFERENCE_MAINTENANCE_BREACH")
            positions[name] = (qty, high, low, margin, maintenance, int(event["expiry_ms"]))
            marks.pop(name, None)
        elif typ == "mark":
            if name not in positions:
                raise AssertionError("MISSING_REFERENCE_MARK")
            qty = positions[name][0]
            fees = d(event["exit_fees_coin"])
            slippage = d(event["exit_slippage_coin"])
            index = d(event["index_usd"])
            if fees < 0 or slippage < 0 or index <= 0:
                raise AssertionError("INVALID_REFERENCE_MARK_PROVENANCE")
            short_ask = d(event["short_ask_coin"])
            long_bid = d(event["long_bid_coin"])
            if short_ask <= 0 or long_bid <= 0:
                raise AssertionError("REFERENCE_INVALID_MARK_BBO")
            liability = max(Decimal(0), qty*(short_ask-long_bid))
            liability += fees+slippage
            if liability < 0:
                raise AssertionError("NEGATIVE_REFERENCE_MARK_LIABILITY")
            marks[name] = (liability, t, index)
        elif typ == "nav":
            if not positions:
                if marks or reserve != 0:
                    raise AssertionError("REFERENCE_INVALID_FLAT_WALLET")
                if "flat_index_usd" not in event:
                    raise AssertionError("REFERENCE_FLAT_NAV_MISSING_SOURCE_INDEX")
                index = d(event["flat_index_usd"])
                if index <= 0:
                    raise AssertionError("REFERENCE_INVALID_FLAT_SOURCE_INDEX")
                nav = cash
            else:
                if "flat_index_usd" in event:
                    raise AssertionError("REFERENCE_FLAT_INDEX_OVERRIDE_OPEN_MARKS")
                if set(marks) != set(positions) or any(
                        mark_t != t for _, mark_t, _ in marks.values()):
                    raise AssertionError("MISSING_OR_STALE_REFERENCE_MARK")
                indices = {idx for _, _, idx in marks.values()}
                if len(indices) != 1:
                    raise AssertionError("INCONSISTENT_REFERENCE_INDEX")
                index = next(iter(indices))
                nav = cash-sum((m[0] for m in marks.values()), Decimal(0))
                maintenance = sum((p[4] for p in positions.values()), Decimal(0))
                if nav < maintenance:
                    raise AssertionError("REFERENCE_MAINTENANCE_BREACH")
            snapshots.append({"nav_coin": str(nav),
                              "nav_usd_equivalent_at_source_index": str(nav*index)})
        elif typ == "settle_batch":
            cohort = event.get("names")
            fee_map = event.get("delivery_fees_coin")
            if (not isinstance(cohort, list) or not cohort
                    or not all(isinstance(k, str) for k in cohort)
                    or len(cohort) != len(set(cohort))
                    or not isinstance(fee_map, dict)):
                raise AssertionError("REFERENCE_INVALID_ATOMIC_BATCH")
            index = d(event["delivery_index_usd"])
            if index <= 0:
                raise AssertionError("REFERENCE_INVALID_DELIVERY_INDEX")
            due = {k for k, v in positions.items() if v[5] == t}
            if set(cohort) != due or not due:
                raise AssertionError("REFERENCE_INCOMPLETE_EXPIRY_BATCH")
            if set(fee_map) != due:
                raise AssertionError("REFERENCE_MISSING_DELIVERY_FEES")
            if any(v[5] < t for v in positions.values()):
                raise AssertionError("REFERENCE_EARLIER_EXPIRY_UNSETTLED")
            later = {k for k, v in positions.items() if v[5] > t}
            if later and any(k not in marks or marks[k][1] != t
                             or marks[k][2] != index for k in later):
                raise AssertionError("REFERENCE_BATCH_SURVIVOR_MARK_REQUIRED")
            fees = {k: d(fee_map[k]) for k in cohort}
            if any(v < 0 for v in fees.values()):
                raise AssertionError("REFERENCE_NEGATIVE_DELIVERY_FEE")
            # Recompute the complete cohort from contract payoffs in coin;
            # no use of production wallet arithmetic or intermediate credit.
            total_payoff = Decimal(0)
            total_margin = Decimal(0)
            for k in cohort:
                qty, high, low, margin, _, _ = positions[k]
                intrinsic = max(high-index, Decimal(0))-max(low-index, Decimal(0))
                total_payoff += qty*intrinsic/index
                total_margin += margin
            cash -= total_payoff + sum(fees.values(), Decimal(0))
            reserve -= total_margin
            for k in cohort:
                del positions[k]
                marks.pop(k, None)
                settled.append(k)
            if cash < 0 or cash < reserve:
                raise AssertionError("REFERENCE_INSOLVENT_ATOMIC_BATCH")
            if later:
                remaining_nav = cash-sum((marks[k][0] for k in later), Decimal(0))
                required_maintenance = sum((positions[k][4] for k in later), Decimal(0))
                if remaining_nav < required_maintenance:
                    raise AssertionError("REFERENCE_POSTBATCH_MAINTENANCE_BREACH")
        elif typ == "settle":
            if name not in positions:
                raise AssertionError("MISSING_REFERENCE_SETTLEMENT")
            qty, high, low, margin, _, expiry = positions[name]
            if t != expiry:
                raise AssertionError("NONCONTRACTUAL_REFERENCE_SETTLEMENT")
            idx = d(event["delivery_index_usd"])
            if idx <= 0:
                raise AssertionError("INVALID_REFERENCE_INDEX")
            later = [key for key, pos in positions.items()
                     if key != name and pos[5] > t]
            siblings = [key for key, pos in positions.items()
                        if key != name and pos[5] == t]
            if siblings:
                raise AssertionError("REFERENCE_SAME_EXPIRY_ATOMIC_BATCH_REQUIRED")
            if later:
                if any(key not in marks or marks[key][1] != t
                       or marks[key][2] != idx for key in later):
                    raise AssertionError("REFERENCE_SETTLEMENT_SURVIVOR_ASOF_MARK_REQUIRED")
            due = qty*(max(high-idx, Decimal(0))-max(low-idx, Decimal(0)))/idx
            delivery_fee = d(event["delivery_fee_coin"])
            if delivery_fee < 0:
                raise AssertionError("REFERENCE_NEGATIVE_SINGLE_DELIVERY_FEE")
            cash -= due+delivery_fee
            reserve -= margin
            del positions[name]
            marks.pop(name, None)
            settled.append(name)
            if cash < reserve:
                raise AssertionError("INSOLVENT_REFERENCE_SETTLEMENT")
            if later:
                liabilities = sum((marks[key][0] for key in later), Decimal(0))
                maintenance_due = sum((positions[key][4] for key in later), Decimal(0))
                if cash-liabilities < maintenance_due:
                    raise AssertionError("REFERENCE_POSTSETTLEMENT_MAINTENANCE_BREACH")
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
