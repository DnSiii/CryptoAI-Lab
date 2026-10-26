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
