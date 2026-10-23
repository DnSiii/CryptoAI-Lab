"""C153 read-only exact paired spot/swap quantity lattice; NOT exchange proof."""
from fractions import Fraction
from math import gcd, lcm
import re

def rational_decimal(s, *, allow_zero=False):
    if type(s) is not str or not s or s.strip() != s or not re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?', s):
        raise ValueError('C153_CANONICAL_DECIMAL_REQUIRED')
    try:
        f = Fraction(s)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError('C153_BAD_DECIMAL') from exc
    if f < 0 or (f == 0 and not allow_zero):
        raise ValueError('C153_NONPOSITIVE_VALUE')
    return f

def common_step(a, b):
    if a <= 0 or b <= 0:
        raise ValueError('C153_BAD_STEP')
    return Fraction(lcm(a.numerator, b.numerator), gcd(a.denominator, b.denominator))

def pair_lattice(*, spot_lot_base, swap_contract_base, swap_lot_contracts,
                 spot_fee_rate, spot_fee_currency, spot_side,
                 spot_min_base, swap_min_contracts, max_pair_base):
    """Structural proof only. No rounding, order submission, or economic claims."""
    if spot_fee_currency not in ('BASE', 'QUOTE') or spot_side not in ('buy', 'sell'):
        raise ValueError('C153_INVALID_FEE_OR_SIDE')
    sl = rational_decimal(spot_lot_base)
    cv = rational_decimal(swap_contract_base)
    cl = rational_decimal(swap_lot_contracts)
    fee = rational_decimal(spot_fee_rate, allow_zero=True)
    spot_min = rational_decimal(spot_min_base)
    swap_min = rational_decimal(swap_min_contracts)
    cap = rational_decimal(max_pair_base)
    if fee >= 1:
        raise ValueError('C153_INVALID_FEE')
    multiplier = (1-fee if spot_side == 'buy' else 1+fee) if spot_fee_currency == 'BASE' else Fraction(1)
    net_spot_step = sl * multiplier
    perp_step = cv * cl
    min_net = max(spot_min * multiplier, cv * swap_min)
    hedge_step = common_step(net_spot_step, perp_step)
    min_units = (min_net.numerator * hedge_step.denominator + min_net.denominator * hedge_step.numerator - 1) // (min_net.denominator * hedge_step.numerator)
    first = hedge_step * max(1, min_units)
    return {
        'status': 'C153_DECLARED_SPECS_ONLY_NO_ECONOMIC_AUTHORIZATION',
        'net_spot_step_base': str(net_spot_step),
        'swap_step_base': str(perp_step),
        'first_exact_hedge_base': str(first),
        'fits_declared_pair_cap': first <= cap,
        'requires_new_preregistered_execution_policy_if_infeasible': first > cap,
        'exchange_authenticated': False, 'historical_roi_authorized': False,
        'validation_opened': False, 'holdout_opened': False,
        'promotion_authorized': False, 'orders_enabled': False,
    }
