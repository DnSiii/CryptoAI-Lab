"""C135: independent marked execution bridge for D1 two-asset hourly ledger.

Read-only, TRAIN-only, deterministic and synthetic/model inputs only.
No claims of native OKX execution, funding settlement or historical PnL.
The accounting identity is: NAV delta at mark = execution slippage PnL
minus quote/native BASE fee value at MARK minus scenario stress fees.
"""
from decimal import Decimal
from research.tools.v99_r106_d1_native_fee_binding_cycle127 import (
    audit_native_plus_stress, decimal_string,
)
from research.tools.v99_r106_d1_cash_inventory_oracle_cycle128 import _state, _snapshot, ASSETS
from research.verification.independent_d1_mark_slippage_oracle_cycle130 import reconcile_marked_fill


def reconcile_marked_two_asset_fills(*, scenario, fills, marks, native_fee_schedule):
    """Verify each spot/perp fill, including off-mark execution, against full states.

    C127 independently checks native fee tier + scenario stress at execution;
    C130 checks cash/inventory and slippage at the declared hourly mark.
    Every intermediate state is chained; other-asset inventory is invariant.
    These declared inputs are NOT proof that an exchange fill occurred.
    """
    if not isinstance(marks, dict) or set(marks) != ASSETS or any(
        not isinstance(marks[a], dict) or set(marks[a]) != {'spot', 'perp'}
        for a in ASSETS
    ):
        raise ValueError('C135_TWO_ASSET_MARKS_REQUIRED')
    for asset in ASSETS:
        for leg in ('spot', 'perp'):
            decimal_string(marks[asset][leg], positive=True)
    fees = audit_native_plus_stress(
        scenario=scenario, trade_rows=fills, native_fee_schedule=native_fee_schedule)
    prev_state = None
    prev_time = None
    slip_total = Decimal('0')
    mark_fee_total = Decimal('0')
    for fill in fills:
        if not isinstance(fill, dict):
            raise ValueError('C135_FILL_MAPPING_REQUIRED')
        asset, leg = fill['asset'], fill['leg']
        if asset not in ASSETS or leg not in ('spot', 'perp'):
            raise ValueError('C135_ASSET_OR_LEG')
        if prev_time is not None and fill['time'] < prev_time:
            raise ValueError('C135_NONCHRONOLOGICAL_FILLS')
        prev_time = fill['time']
        before = _state(fill.get('before'))
        after = _state(fill.get('after'))
        if prev_state is not None and before != prev_state:
            raise ValueError('C135_CROSS_FILL_STATE_DISCONTINUITY')
        if any(before[1][a] != after[1][a] or before[2][a] != after[2][a]
               for a in ASSETS if a != asset):
            raise ValueError('C135_OTHER_ASSET_CHANGED')
        quantity = decimal_string(fill['base_quantity'], positive=True)
        px = decimal_string(fill['execution_price_quote_per_base'], positive=True)
        if decimal_string(fill['quote_notional'], positive=True) != quantity * px:
            raise ValueError('C135_NOTIONAL_PRICE_QUANTITY_MISMATCH')
        tier = next((r for r in native_fee_schedule[asset]
                     if r['start'] <= fill['time'] < r['end']), None)
        if tier is None:
            raise ValueError('C135_MISSING_NATIVE_TIER')
        fee_currency = tier['spot_fee_currency'] if leg == 'spot' else 'QUOTE'
        proof = reconcile_marked_fill(
            timestamp=fill['time'], leg=leg, side=fill['side'],
            fee_currency=fee_currency, quantity=fill['base_quantity'],
            execution_price=fill['execution_price_quote_per_base'],
            mark_price=marks[asset][leg],
            native_fee_quote=fill['native_fee_quote'],
            stress_fee_quote=fill['stress_fee_quote'],
            base_fee_units=fill.get('base_fee_units', '0'),
            before={'cash_quote': str(before[0]),
                    'spot_base': str(before[1][asset]),
                    'perp_base': str(before[2][asset])},
            after={'cash_quote': str(after[0]),
                   'spot_base': str(after[1][asset]),
                   'perp_base': str(after[2][asset])},
        )
        slip_total += Decimal(proof['slippage_pnl_quote'])
        mark_fee_total += Decimal(proof['fees_at_mark_quote'])
        prev_state = after
    # Native BASE fees are converted at mark for NAV; their booked quote
    # equivalent at execution can differ. Never silently equate the two.
    return {
        'status': 'C135_STRUCTURAL_TWO_ASSET_MARK_FILL_ONLY_HOLD',
        'fills_replayed': len(fills),
        'execution_slippage_pnl_quote': str(slip_total),
        'fees_at_mark_quote': str(mark_fee_total),
        'total_economic_fee_quote': fees['total_modeled_fee_quote'],
        'last_declared_account_state': _snapshot(*prev_state),
        'actual_okx_fills_authenticated': False,
        'historical_economics_authorized': False,
        'validation_opened': False, 'holdout_opened': False,
        'promotion_authorized': False, 'orders_enabled': False,
    }
