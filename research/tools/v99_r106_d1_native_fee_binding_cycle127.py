"""C127 independent native-fee/stress reconciliation for D1; never grants economics.

Historical native fees and fixed severe/supersevere *additional* stress are
separate obligations. This audit does not authenticate exchange receipts or
repair the old ledger; it rejects undercharging in a supplied trade journal.
Spot BASE-denominated fees require a separate inventory-units reconciliation.
No network, sealed data, orders, strategy retuning, or ROI calculation.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone

from research.tools.v99_r106_d1_basis_carry_preregistered import COST_SHOCKS, TRAIN_END
from research.tools.v99_r106_d1_full_train_guard import START

ASSETS = frozenset(('BTC', 'ETH'))
LEGS = frozenset(('spot', 'perp'))


def decimal_string(value, *, positive=False):
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError('C127_CANONICAL_DECIMAL_STRING_REQUIRED')
    try:
        v = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('C127_BAD_DECIMAL') from exc
    if not v.is_finite() or v < 0 or (positive and v == 0):
        raise ValueError('C127_NEGATIVE_OR_NONFINITE')
    return v


def audit_native_plus_stress(*, scenario, trade_rows, native_fee_schedule):
    """Check exact quote-equivalent native+shock costs for *each* fill.

    `native_fee_schedule`: per asset list of dictionaries with `start`, `end`,
    `spot_taker`, `perp_taker`, `spot_fee_currency`, `account_tier`.  Entries
    must be chronological and gap-free over observed trade times; actual
    historical tier provenance remains a separate independent requirement.

    `trade_rows`: trade_id, time (datetime UTC), asset, leg, quote_notional,
    native_fee_quote, stress_fee_quote, booked_total_fee_quote, and for spot
    BASE fees also base_fee_units, execution_price_quote_per_base.  Fees in
    base MUST be reflected in the actual inventory ledger before economics.
    """
    if scenario not in COST_SHOCKS:
        raise ValueError('C127_UNPREREGISTERED_SCENARIO')
    if not isinstance(trade_rows, (list, tuple)) or not trade_rows:
        raise ValueError('C127_NO_NATIVE_TRADE_JOURNAL')
    if not isinstance(native_fee_schedule, dict) or set(native_fee_schedule) != ASSETS:
        raise ValueError('C127_MISSING_NATIVE_FEE_SCHEDULE')
    stress = Decimal(str(COST_SHOCKS[scenario]))
    prepared = {}
    for asset in ASSETS:
        intervals = native_fee_schedule[asset]
        if not isinstance(intervals, (list, tuple)) or not intervals:
            raise ValueError('C127_FEE_TIER_COVERAGE_MISSING')
        previous = None
        prepared[asset] = []
        for r in intervals:
            if set(r) != {'start', 'end', 'spot_taker', 'perp_taker', 'spot_fee_currency', 'account_tier'}:
                raise ValueError('C127_NATIVE_TIER_SCHEMA')
            start, end = r['start'], r['end']
            if (not isinstance(start, datetime) or not isinstance(end, datetime) or
                start.tzinfo is None or end.tzinfo is None or
                start.utcoffset().total_seconds() != 0 or end.utcoffset().total_seconds() != 0 or
                start >= end or end > TRAIN_END or (previous is not None and start != previous)):
                raise ValueError('C127_FEE_TIER_GAP_OVERLAP_OR_SEALED')
            previous = end
            if r['spot_fee_currency'] not in ('BASE', 'QUOTE') or not isinstance(r['account_tier'], str) or not r['account_tier'].strip():
                raise ValueError('C127_FEE_CURRENCY_OR_TIER_UNVERIFIED')
            for k in ('spot_taker', 'perp_taker'):
                fee = decimal_string(r[k])
                if fee > Decimal('.01'):
                    raise ValueError('C127_NATIVE_TIER_RATE_UNREASONABLE')
            prepared[asset].append(r)
    ids = set()
    native_sum = stress_sum = total_sum = Decimal('0')
    base_fee_fills = 0
    for trade in trade_rows:
        required = {'trade_id', 'time', 'asset', 'leg', 'quote_notional',
                    'native_fee_quote', 'stress_fee_quote', 'booked_total_fee_quote'}
        if not isinstance(trade, dict) or not required <= set(trade):
            raise ValueError('C127_TRADE_JOURNAL_SCHEMA')
        trade_id = trade['trade_id']
        if not isinstance(trade_id, str) or not trade_id or trade_id in ids:
            raise ValueError('C127_DUPLICATE_OR_EMPTY_TRADE_ID')
        ids.add(trade_id)
        t = trade['time']
        if (not isinstance(t, datetime) or t.tzinfo is None or
            t.utcoffset().total_seconds() != 0 or not START <= t < TRAIN_END):
            raise ValueError('C127_TRADE_OUTSIDE_TRAIN_OR_NONUTC')
        asset, leg = trade['asset'], trade['leg']
        if asset not in ASSETS or leg not in LEGS:
            raise ValueError('C127_UNKNOWN_ASSET_OR_LEG')
        tier = next((r for r in prepared[asset] if r['start'] <= t < r['end']), None)
        if tier is None:
            raise ValueError('C127_NATIVE_FEE_TIER_NOT_VALID_AT_FILL')
        notional = decimal_string(trade['quote_notional'], positive=True)
        native = notional * decimal_string(tier['spot_taker' if leg == 'spot' else 'perp_taker'])
        shock = notional * stress
        booked_native = decimal_string(trade['native_fee_quote'])
        booked_stress = decimal_string(trade['stress_fee_quote'])
        booked_total = decimal_string(trade['booked_total_fee_quote'])
        if booked_native != native or booked_stress != shock or booked_total != native + shock:
            raise ValueError('C127_NATIVE_PLUS_STRESS_FEE_UNDER_OR_OVER_BOOKED')
        if leg == 'spot' and tier['spot_fee_currency'] == 'BASE':
            if not {'base_fee_units', 'execution_price_quote_per_base', 'inventory_base_fee_debit_units'} <= set(trade):
                raise ValueError('C127_SPOT_BASE_FEE_INVENTORY_DEBIT_MISSING')
            units = decimal_string(trade['base_fee_units'])
            price = decimal_string(trade['execution_price_quote_per_base'], positive=True)
            debited = decimal_string(trade['inventory_base_fee_debit_units'])
            if units * price != native or debited != units:
                raise ValueError('C127_SPOT_BASE_FEE_INVENTORY_MISMATCH')
            base_fee_fills += 1
        native_sum += native
        stress_sum += shock
        total_sum += booked_total
    return {'status': 'C127_STRUCTURAL_NATIVE_FEE_BINDING_ONLY_NO_ECONOMICS',
            'scenario': scenario, 'trades_checked': len(ids),
            'spot_base_fee_inventory_debits_checked': base_fee_fills,
            'native_fee_quote': str(native_sum),
            'incremental_stress_fee_quote': str(stress_sum),
            'total_modeled_fee_quote': str(total_sum),
            'native_fee_source_authenticated': False,
            'actual_exchange_fills_authenticated': False,
            'historical_roi_calculated': False, 'historical_economics_authorized': False,
            'validation_opened': False, 'holdout_opened': False,
            'promotion_authorized': False, 'orders_enabled': False}
