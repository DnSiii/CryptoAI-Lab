"""C151 independent D1 spot/swap executable-lot feasibility gate.

Additive, read-only and fail-closed. Does NOT modify C139 sizing, execute
orders, authenticate instrument specifications or authorize economic claims.
The model's 1e-12 spot quantity step is NOT an OKX spot/swap lot contract.
Spec rows supplied by a caller are only *assertions* until independently
verified against dated first-party exchange records.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

ASSETS = ('BTC', 'ETH')
SPEC_KEYS = frozenset({
    'venue', 'spot_instrument', 'swap_instrument', 'swap_type',
    'contract_value_currency', 'contract_value_base', 'swap_lot_contracts',
    'swap_min_contracts', 'spot_lot_base', 'spot_min_base',
    'effective_from', 'effective_until', 'published_at',
})


def _positive(s):
    if type(s) is not str or not s or s.strip() != s:
        raise ValueError('C151_NONCANONICAL_SPEC_QUANTITY')
    try:
        v = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError('C151_INVALID_SPEC_QUANTITY') from exc
    if not v.is_finite() or v <= 0:
        raise ValueError('C151_NONPOSITIVE_SPEC_QUANTITY')
    return v


def _utc(t):
    return (type(t) is datetime and t.tzinfo is timezone.utc and
            t.minute == t.second == t.microsecond == 0)


def _validate_specs(specs):
    if type(specs) is not dict or set(specs) != set(ASSETS):
        raise ValueError('C151_FIRST_PARTY_INSTRUMENT_SPECS_REQUIRED')
    validated = {}
    for a in ASSETS:
        s = specs[a]
        if type(s) is not dict or set(s) != SPEC_KEYS:
            raise ValueError('C151_INCOMPLETE_SPEC_SCHEMA')
        if (s['venue'] != 'OKX' or s['spot_instrument'] != a + '-USDT' or
                s['swap_instrument'] != a + '-USDT-SWAP' or
                s['swap_type'] != 'linear' or s['contract_value_currency'] != a):
            raise ValueError('C151_WRONG_INSTRUMENT_OR_CONTRACT_UNIT')
        if not all(_utc(s[k]) for k in ('effective_from','effective_until','published_at')):
            raise ValueError('C151_NONCANONICAL_SPEC_CLOCK')
        if s['effective_from'] >= s['effective_until']:
            raise ValueError('C151_INVALID_SPEC_WINDOW')
        q = {k: _positive(s[k]) for k in (
            'contract_value_base', 'swap_lot_contracts', 'swap_min_contracts',
            'spot_lot_base', 'spot_min_base')}
        validated[a] = (s, q)
    return validated


def lot_feasibility_diagnostics(journal, specs):
    """Count impossible modeled fills without rounding or altering any orders.

    Returns modeled structural evidence only. An apparently feasible declared
    spec is NOT authenticated by this function; separate signed/hashed native
    instrument/fee/fill/funding provenance remains mandatory.
    """
    validated = _validate_specs(specs)
    frames = journal.get('frames') if type(journal) is dict else None
    if type(frames) is not list or not frames:
        raise ValueError('C151_JOURNAL_FRAMES_REQUIRED')
    count = 0
    invalid = []
    for frame_index, frame in enumerate(frames):
        t = frame.get('time')
        if not _utc(t):
            raise ValueError('C151_INVALID_FRAME_TIME')
        fills = frame.get('fills')
        if type(fills) is not list:
            raise ValueError('C151_INVALID_FILLS_SCHEMA')
        for fill_index, fill in enumerate(fills):
            if type(fill) is not dict or fill.get('time') != t:
                raise ValueError('C151_INVALID_FILL_TIME')
            a, leg = fill.get('asset'), fill.get('leg')
            if a not in ASSETS or leg not in ('spot','perp'):
                raise ValueError('C151_UNKNOWN_ASSET_OR_LEG')
            spec, q = validated[a]
            if not (spec['effective_from'] <= t < spec['effective_until'] and
                    spec['published_at'] <= t - timedelta(hours=1)):
                raise ValueError('C151_SPEC_NOT_CAUSALLY_EFFECTIVE')
            qty = _positive(fill.get('base_quantity'))
            if leg == 'spot':
                lot, minimum = q['spot_lot_base'], q['spot_min_base']
                executable = qty >= minimum and qty % lot == 0
            else:
                contracts = qty / q['contract_value_base']
                executable = (contracts >= q['swap_min_contracts'] and
                              contracts % q['swap_lot_contracts'] == 0)
            count += 1
            if not executable:
                invalid.append({'frame_index': frame_index,
                                'fill_index': fill_index,
                                'asset': a, 'leg': leg,
                                'quantity_base': str(qty),
                                'reason': 'UNEXECUTABLE_NATIVE_LOT_OR_MINIMUM'})
    return {
        'status': 'C151_MODEL_ONLY_LOT_FEASIBILITY_DIAGNOSTIC',
        'fills_checked': count,
        'unexecutable_fills': len(invalid),
        'first_five_violations': invalid[:5],
        'all_modeled_fills_executable_under_declared_specs': not invalid,
        'instrument_specs_exchange_authenticated': False,
        'native_fills_exchange_authenticated': False,
        'historical_roi_authorized': False,
        'validation_opened': False,
        'holdout_opened': False,
        'promotion_authorized': False,
        'orders_enabled': False,
    }


def require_lot_feasible(journal, specs):
    proof = lot_feasibility_diagnostics(journal, specs)
    if proof['unexecutable_fills']:
        raise ValueError('C151_NATIVE_EXECUTION_LOT_VIOLATION')
    return proof
