"""C128 independent per-fill cash/spot/perp replay, pre-economic only.

This does NOT turn declared fills, fee tiers, funding or prices into authentic
OKX receipts. No strategy tuning, no historical ROI, no orders, no holdout.
Use C127 native+stress audit first; C128 independently checks that the same
fees are reflected in actual *modeled* cash and BASE inventory changes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from research.tools.v99_r106_d1_native_fee_binding_cycle127 import (
    audit_native_plus_stress, decimal_string,
)
from research.tools.v99_r106_d1_basis_carry_preregistered import TRAIN_END
from research.tools.v99_r106_d1_full_train_guard import START

ASSETS = frozenset(('BTC', 'ETH'))
SIDES = frozenset(('buy', 'sell'))


def _signed_decimal(value):
    """Canonical signed finite decimal, unlike nonnegative C127 fees."""
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError('C128_CANONICAL_SIGNED_DECIMAL_REQUIRED')
    try:
        v = Decimal(value)
    except Exception as exc:
        raise ValueError('C128_BAD_SIGNED_DECIMAL') from exc
    if not v.is_finite():
        raise ValueError('C128_NONFINITE_BALANCE')
    return v


def _state(row):
    if not isinstance(row, dict) or set(row) != {'cash_quote', 'spot_base', 'perp_base'}:
        raise ValueError('C128_ACCOUNT_SNAPSHOT_SCHEMA')
    if not isinstance(row['spot_base'], dict) or set(row['spot_base']) != ASSETS:
        raise ValueError('C128_COMPLETE_SPOT_BALANCE_REQUIRED')
    if not isinstance(row['perp_base'], dict) or set(row['perp_base']) != ASSETS:
        raise ValueError('C128_COMPLETE_PERP_BALANCE_REQUIRED')
    cash = _signed_decimal(row['cash_quote'])
    spot = {a: _signed_decimal(row['spot_base'][a]) for a in ASSETS}
    perp = {a: _signed_decimal(row['perp_base'][a]) for a in ASSETS}
    if cash < 0 or any(q < 0 for q in spot.values()):
        raise ValueError('C128_NEGATIVE_CASH_OR_SPOT_BALANCE')
    return cash, spot, perp


def _snapshot(cash, spot, perp):
    return {'cash_quote': str(cash),
            'spot_base': {a: str(spot[a]) for a in sorted(ASSETS)},
            'perp_base': {a: str(perp[a]) for a in sorted(ASSETS)}}


def reconcile_cash_inventory(*, scenario, fills, native_fee_schedule):
    """Independently replay strictly TRAIN-only fills, no mark/funding inference.

    Each fill extends C127's schema with `side`, `base_quantity`,
    `execution_price_quote_per_base`, and full `before`/`after` account states.
    Spot BASE native fee is a BASE inventory debit, *not* also a cash fee.
    Spot QUOTE and perp native fees are cash debits. Incremental scenario
    stress is always a cash debit. Perp trade notional does not debit cash.
    Adjacent fills must share exactly the previous post-state and be sorted
    by UTC timestamp, making invented/missing intermediate entries detectable
    relative to the supplied journal (not relative to the real exchange).
    """
    if not isinstance(fills, (list, tuple)) or not fills:
        raise ValueError('C128_EMPTY_FILL_JOURNAL')
    c127 = audit_native_plus_stress(scenario=scenario, trade_rows=fills,
                                    native_fee_schedule=native_fee_schedule)
    previous_after = None
    previous_time = None
    total_fees = Decimal('0')
    base_native_fees = Decimal('0')
    quote_native_fees = Decimal('0')
    total_stress = Decimal('0')
    for fill in fills:
        t = fill['time']
        if (not isinstance(t, datetime) or t.tzinfo != timezone.utc or
            not START <= t < TRAIN_END or
            (previous_time is not None and t < previous_time)):
            raise ValueError('C128_NONCHRONOLOGICAL_OR_SEALED_FILL')
        previous_time = t
        asset, leg = fill['asset'], fill['leg']
        if fill.get('side') not in SIDES:
            raise ValueError('C128_MISSING_OR_UNKNOWN_SIDE')
        direction = Decimal('1') if fill['side'] == 'buy' else Decimal('-1')
        quantity = decimal_string(fill.get('base_quantity'), positive=True)
        price = decimal_string(fill.get('execution_price_quote_per_base'), positive=True)
        notional = decimal_string(fill['quote_notional'], positive=True)
        if notional != quantity * price:
            raise ValueError('C128_FILL_NOTIONAL_QUANTITY_PRICE_MISMATCH')
        native = decimal_string(fill['native_fee_quote'])
        stress = decimal_string(fill['stress_fee_quote'])
        before = _state(fill.get('before'))
        after = _state(fill.get('after'))
        if previous_after is not None and before != previous_after:
            raise ValueError('C128_DISCONTINUOUS_ACCOUNT_JOURNAL')
        old_cash, old_spot, old_perp = before
        new_cash, new_spot, new_perp = after
        if any(new_spot[a] != old_spot[a] or new_perp[a] != old_perp[a]
               for a in ASSETS if a != asset):
            raise ValueError('C128_OTHER_ASSET_BALANCE_CHANGED')
        tier = next((r for r in native_fee_schedule[asset]
                     if r['start'] <= t < r['end']), None)
        if tier is None:  # C127 should have rejected this already.
            raise ValueError('C128_FEE_TIER_MISSING')
        if leg == 'spot':
            if new_perp[asset] != old_perp[asset]:
                raise ValueError('C128_SPOT_FILL_CHANGED_PERP_POSITION')
            base_fee = (decimal_string(fill['base_fee_units'])
                        if tier['spot_fee_currency'] == 'BASE' else Decimal('0'))
            if new_spot[asset] != old_spot[asset] + direction * quantity - base_fee:
                raise ValueError('C128_SPOT_BASE_INVENTORY_MISMATCH')
            quote_fee = native if tier['spot_fee_currency'] == 'QUOTE' else Decimal('0')
            expected_cash = old_cash - direction * notional - quote_fee - stress
            if new_cash != expected_cash:
                raise ValueError('C128_SPOT_CASH_DOUBLE_CHARGE_OR_OMISSION')
            # At the execution mark, the entire fee must reduce economic NAV.
            nav_delta = new_cash - old_cash + (new_spot[asset] - old_spot[asset]) * price
            base_native_fees += native if base_fee else Decimal('0')
            quote_native_fees += quote_fee
        else:
            if new_spot[asset] != old_spot[asset]:
                raise ValueError('C128_PERP_FILL_CHANGED_SPOT_INVENTORY')
            if new_perp[asset] != old_perp[asset] + direction * quantity:
                raise ValueError('C128_PERP_POSITION_MISMATCH')
            if new_cash != old_cash - native - stress:
                raise ValueError('C128_PERP_FEE_CASH_MISMATCH')
            nav_delta = new_cash - old_cash
            quote_native_fees += native
        if nav_delta != -(native + stress):
            raise ValueError('C128_PER_FILL_NAV_FEE_IDENTITY')
        total_fees += native + stress
        total_stress += stress
        previous_after = after
    if total_fees != Decimal(c127['total_modeled_fee_quote']):
        raise ValueError('C128_C127_TOTAL_FEE_DISAGREEMENT')
    if base_native_fees + quote_native_fees != Decimal(c127['native_fee_quote']):
        raise ValueError('C128_C127_NATIVE_FEE_DISAGREEMENT')
    return {
        'status': 'C128_INDEPENDENT_ACCOUNT_TRANSITION_ONLY_NO_ECONOMICS',
        'scenario': scenario, 'fills_replayed': len(fills),
        'native_base_inventory_fee_quote': str(base_native_fees),
        'native_quote_cash_fee_quote': str(quote_native_fees),
        'incremental_stress_cash_fee_quote': str(total_stress),
        'total_economic_fee_quote': str(total_fees),
        'last_declared_account_state': _snapshot(*previous_after),
        'c127_independent_fee_identity_passed': True,
        'exchange_receipts_authenticated': False,
        'actual_account_state_authenticated': False,
        'settled_funding_authenticated': False,
        'historical_economics_authorized': False,
        'validation_opened': False, 'holdout_opened': False,
        'promotion_authorized': False, 'orders_enabled': False,
    }
