"""Independent V99 I1 dated-fee arithmetic oracle; no production imports.

Only checks mathematical lower-bound parity on caller-provided schedule rows.
It does not authenticate the underlying venue, account, contract or fills.
"""
from decimal import Decimal


def _d(value):
    if isinstance(value, bool):
        raise AssertionError("ORACLE_INVALID_DECIMAL")
    number = Decimal(str(value))
    if not number.is_finite() or number < 0:
        raise AssertionError("ORACLE_INVALID_DECIMAL")
    return number


def independently_recompute(schedule, *, event_type, asset, at_ms, native_lots,
                            premiums_coin=None, strikes_usd=None,
                            delivery_index_usd=None):
    eligible = [row for row in schedule["rows"]
                if row["asset"] == asset and
                row["effective_from_ms"] <= at_ms < row["effective_to_ms"]]
    if len(eligible) != 1:
        raise AssertionError("ORACLE_MISSING_OR_AMBIGUOUS_TERMS")
    row = eligible[0]
    quantity = _d(native_lots)
    if quantity <= 0 or quantity % _d(row["native_lot_quantity"]) != 0:
        raise AssertionError("ORACLE_LOT_MISMATCH")
    if event_type == "OPEN":
        values = [_d(p) for p in premiums_coin]
        rate = _d(row["entry_per_lot_coin"])
    elif event_type == "SETTLE_BATCH":
        index = _d(delivery_index_usd)
        values = [max(_d(k)-index, Decimal(0))/index for k in strikes_usd]
        rate = _d(row["delivery_per_lot_coin"])
    else:
        raise AssertionError("ORACLE_EVENT_TYPE")
    if len(values) != 2:
        raise AssertionError("ORACLE_NOT_TWO_LEGS")
    cap = _d(row["cap_fraction"])
    return sum((quantity * min(rate, cap * p) for p in values), Decimal(0))


def verify(schedule, production_result, **inputs):
    expected = independently_recompute(schedule, **inputs)
    if (_d(production_result["native_fee_minimum_coin"]) != expected
            or production_result["historical_native_fee_certified"] is not False
            or production_result["original_options_economic_train_certified"] is not False
            or production_result["promotion_authorized"] is not False):
        raise AssertionError("INDEPENDENT_NATIVE_FEE_PARITY_OR_CERTIFICATION_MISMATCH")
    return {"independent_native_fee_arithmetic_verified": True,
            "historical_native_fee_certified": False,
            "promotion_authorized": False}
