"""C130 independent, TRAIN-only modeled fill/mark accounting (NO economic ROI).

A price different from the hourly mark is an explicit economic event, not a
silent fee. This independent oracle is intentionally not wired to any order API.
Perp accounting assumes immediate mark-to-market cash recognition; it is NOT
an assertion about OKX's actual settlement convention or authentic fills.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

START = datetime(2021, 12, 9, tzinfo=timezone.utc)
END = datetime(2023, 10, 1, tzinfo=timezone.utc)


def dec(value, *, nonnegative=False, positive=False):
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError('C130_CANONICAL_DECIMAL_REQUIRED')
    try:
        d = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('C130_BAD_DECIMAL') from exc
    if not d.is_finite() or (positive and d <= 0) or (nonnegative and d < 0):
        raise ValueError('C130_INVALID_AMOUNT')
    return d


def reconcile_marked_fill(*, timestamp, leg, side, fee_currency, quantity,
                          execution_price, mark_price, native_fee_quote,
                          stress_fee_quote, base_fee_units,
                          before, after):
    """Fail-closed independent proof for one fill at a declared mark.

    States have cash_quote, spot_base, perp_base as canonical decimal strings.
    QUOTE spot fees and all perp fees debit cash. BASE spot fees debit base.
    A perp fill's execution/mark spread is credited/debited to modeled cash
    immediately, so the resulting account NAV cannot silently omit slippage.
    """
    if (type(timestamp) is not datetime or timestamp.tzinfo is not timezone.utc
            or not START <= timestamp < END):
        raise ValueError('C130_SEALED_OR_NONUTC_TIMESTAMP')
    if leg not in ('spot', 'perp') or side not in ('buy', 'sell'):
        raise ValueError('C130_LEG_OR_SIDE_INVALID')
    if fee_currency not in ('BASE', 'QUOTE'):
        raise ValueError('C130_FEE_CURRENCY_INVALID')
    if leg == 'perp' and fee_currency != 'QUOTE':
        raise ValueError('C130_PERP_BASE_FEE_UNSUPPORTED')
    q = dec(quantity, positive=True)
    px = dec(execution_price, positive=True)
    mark = dec(mark_price, positive=True)
    native = dec(native_fee_quote, nonnegative=True)
    stress = dec(stress_fee_quote, nonnegative=True)
    base_fee = dec(base_fee_units, nonnegative=True)
    if leg == 'perp' or fee_currency == 'QUOTE':
        if base_fee:
            raise ValueError('C130_UNEXPECTED_BASE_FEE')
    elif base_fee * px != native:
        raise ValueError('C130_BASE_FEE_EXECUTION_CONVERSION_MISMATCH')
    if type(before) is not dict or type(after) is not dict or set(before) != {
            'cash_quote', 'spot_base', 'perp_base'} or set(after) != set(before):
        raise ValueError('C130_ACCOUNT_SCHEMA')
    b = {k: dec(v) for k, v in before.items()}
    a = {k: dec(v) for k, v in after.items()}
    if min(b['cash_quote'], a['cash_quote'], b['spot_base'], a['spot_base']) < 0:
        raise ValueError('C130_NEGATIVE_SPOT_OR_CASH')
    direction = Decimal('1') if side == 'buy' else Decimal('-1')
    signed_slippage_pnl = direction * q * (mark - px)
    if leg == 'spot':
        quote_fee = native if fee_currency == 'QUOTE' else Decimal('0')
        expected_cash = b['cash_quote'] - direction * q * px - quote_fee - stress
        expected_spot = b['spot_base'] + direction * q - base_fee
        expected_perp = b['perp_base']
        fee_at_mark = quote_fee + stress + base_fee * mark
    else:
        expected_cash = b['cash_quote'] + signed_slippage_pnl - native - stress
        expected_spot = b['spot_base']
        expected_perp = b['perp_base'] + direction * q
        fee_at_mark = native + stress
    if (a['cash_quote'], a['spot_base'], a['perp_base']) != (
            expected_cash, expected_spot, expected_perp):
        raise ValueError('C130_FILL_INVENTORY_CASH_OR_SLIPPAGE_MISMATCH')
    before_nav = b['cash_quote'] + b['spot_base'] * mark
    after_nav = a['cash_quote'] + a['spot_base'] * mark
    delta = after_nav - before_nav
    if delta != signed_slippage_pnl - fee_at_mark:
        raise ValueError('C130_MARK_NAV_CONSERVATION_MISMATCH')
    return {'status': 'C130_STRUCTURAL_MARK_FILL_ONLY_NO_ECONOMICS',
            'slippage_pnl_quote': str(signed_slippage_pnl),
            'fees_at_mark_quote': str(fee_at_mark),
            'nav_delta_quote': str(delta),
            'actual_okx_fills_authenticated': False,
            'actual_funding_authenticated': False,
            'historical_roi_authorized': False,
            'validation_opened': False, 'holdout_opened': False,
            'promotion_authorized': False, 'orders_enabled': False}
