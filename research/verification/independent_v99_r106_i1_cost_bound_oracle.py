"""Independent Decimal arithmetic for I1 modeled two-leg scenario-cost binding.

No imports from primary cost adapter or wallet; no original fee certification.
"""
from decimal import Decimal, InvalidOperation

FIXED = {"severe": ("0.0012", "0.0012"),
         "supersevere": ("0.0024", "0.0024")}


def decimal(x):
    if isinstance(x, bool):
        raise AssertionError("BOOLEAN_COST_OR_QUANTITY")
    try:
        v = Decimal(str(x))
    except (ValueError, TypeError, InvalidOperation) as e:
        raise AssertionError("INVALID_REFERENCE_DECIMAL") from e
    if not v.is_finite():
        raise AssertionError("NONFINITE_REFERENCE_DECIMAL")
    return v


def audit_open(journal: dict, cash_coin):
    if journal.get("fixture") is not True or journal.get("historical_economic_train") is not False:
        raise AssertionError("UNTRUSTED_REFERENCE_FIXTURE")
    scenario = journal.get("scenario")
    if scenario not in FIXED:
        raise AssertionError("UNKNOWN_REFERENCE_SCENARIO")
    q = decimal(journal["qty"])
    if q <= 0:
        raise AssertionError("NONPOSITIVE_REFERENCE_QUANTITY")
    fee, slip = decimal(journal["entry_fee_coin"]), decimal(journal["entry_slippage_coin"])
    fr, sr = map(decimal, FIXED[scenario])
    if fee < 2 * q * fr or slip < 2 * q * sr:
        raise AssertionError("REFERENCE_SCENARIO_FRICTION_UNDERPAYMENT")
    short_bid = decimal(journal["short_bid_coin"])
    long_ask = decimal(journal["long_ask_coin"])
    if short_bid <= long_ask:
        raise AssertionError("NONPOSITIVE_REFERENCE_GROSS_CREDIT")
    expected = decimal(journal["initial_coin"]) + q * (short_bid-long_ask) - fee-slip
    if expected != decimal(cash_coin):
        raise AssertionError("REFERENCE_COIN_CASH_MISMATCH")
    return {"independent_cost_binding": "MATCH", "scenario": scenario,
            "fee_floor_coin": str(2*q*fr), "slippage_floor_coin": str(2*q*sr),
            "historical_economic_train": False, "promotion_authorized": False}


def audit_postentry(journal: dict):
    """Independent post-entry maintenance check including scenario exit costs.

    Requires a synthetic journal; not exchange-certified original accounting.
    No imports from primary wallet or adapter.
    """
    if journal.get("fixture") is not True or journal.get("historical_economic_train") is not False:
        raise AssertionError("UNTRUSTED_POSTENTRY_JOURNAL")
    scenario = journal.get("scenario")
    if scenario not in FIXED:
        raise AssertionError("UNKNOWN_REFERENCE_SCENARIO")
    q = decimal(journal["qty"])
    if q <= 0:
        raise AssertionError("NONPOSITIVE_REFERENCE_QUANTITY")
    cash = decimal(journal["cash_after_open_coin"])
    short_ask = decimal(journal["short_ask_coin"])
    long_bid = decimal(journal["long_bid_coin"])
    previous_liabilities = decimal(journal["existing_exit_liabilities_coin"])
    maintenance = decimal(journal["total_maintenance_coin"])
    if cash < 0 or previous_liabilities < 0 or maintenance <= 0:
        raise AssertionError("INVALID_REFERENCE_COLLATERAL")
    fee_per_leg, slip_per_leg = map(decimal, FIXED[scenario])
    minimum_exit = max(decimal("0"), q * (short_ask - long_bid))
    minimum_exit += 2*q*fee_per_leg + 2*q*slip_per_leg
    conservative_nav = cash - previous_liabilities - minimum_exit
    if conservative_nav < maintenance:
        raise AssertionError("POSTENTRY_SCENARIO_COST_MAINTENANCE_VETO")
    return {"independent_postentry_solvency": "PASS",
            "conservative_nav_coin": str(conservative_nav),
            "maintenance_coin": str(maintenance),
            "historical_economic_train": False,
            "promotion_authorized": False}


def audit_delivery_batch(journal: dict, observed_cash_coin, observed_reserved_coin,
                         observed_settled_names):
    """Independent native inverse-payoff + scenario fee-floor reconciliation.

    Input is a *fixture* journal only; no imports from primary wallet or
    cost adapter, no historical source attestation, no claimed option PnL.
    """
    if journal.get("fixture") is not True or journal.get("historical_economic_train") is not False:
        raise AssertionError("UNTRUSTED_DELIVERY_JOURNAL")
    scenario = journal.get("scenario")
    if scenario not in FIXED:
        raise AssertionError("UNKNOWN_REFERENCE_SCENARIO")
    fee_rate = decimal(FIXED[scenario][0])
    index = decimal(journal["delivery_index_usd"])
    if index <= 0:
        raise AssertionError("INVALID_REFERENCE_DELIVERY_INDEX")
    positions = journal.get("due_positions")
    if not isinstance(positions, list) or not positions:
        raise AssertionError("MISSING_REFERENCE_DUE_COHORT")
    names = [p["name"] for p in positions]
    if len(names) != len(set(names)) or any(not isinstance(n, str) or not n for n in names):
        raise AssertionError("INVALID_REFERENCE_DUE_IDS")
    if set(names) != set(journal["due_names"]) or set(names) != set(observed_settled_names):
        raise AssertionError("INCOMPLETE_REFERENCE_ATOMIC_SETTLEMENT")
    debits = decimal("0")
    released = decimal("0")
    for p in positions:
        q, high, low = (decimal(p[k]) for k in ("qty", "short_strike_usd", "long_strike_usd"))
        fee, margin = (decimal(p[k]) for k in ("delivery_fee_coin", "initial_margin_coin"))
        if q <= 0 or high <= low or low <= 0 or margin < 0:
            raise AssertionError("INVALID_REFERENCE_NATIVE_POSITION")
        if fee < 2 * q * fee_rate:
            raise AssertionError("REFERENCE_SCENARIO_DELIVERY_FEE_UNDERPAYMENT")
        obligation = q * (max(high-index, decimal("0")) - max(low-index, decimal("0"))) / index
        debits += obligation + fee
        released += margin
    expected_cash = decimal(journal["cash_before_coin"]) - debits
    expected_reserved = decimal(journal["reserve_before_coin"]) - released
    if expected_cash < 0 or expected_reserved < 0 or expected_cash < expected_reserved:
        raise AssertionError("INSOLVENT_REFERENCE_DELIVERY")
    if expected_cash != decimal(observed_cash_coin) or expected_reserved != decimal(observed_reserved_coin):
        raise AssertionError("REFERENCE_DELIVERY_CASH_OR_RESERVE_MISMATCH")
    return {"independent_scenario_delivery": "MATCH", "scenario": scenario,
            "delivery_debit_coin": str(debits), "released_margin_coin": str(released),
            "historical_economic_train": False, "promotion_authorized": False}
