"""C129 independently bridge spot/perp marks, modeled funding and native-fee fills.

TRAIN-only synthetic structural accounting; never authenticates OKX receipts,
fees, account balances, ROI or settled funding. Never submits orders.
The first market mark is explicitly the hour before the first frame.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from research.tools.v99_r106_d1_cash_inventory_oracle_cycle128 import (
    _state, _signed_decimal,
)
from research.tools.v99_r106_d1_mark_fill_bridge_cycle135 import reconcile_marked_two_asset_fills
from research.tools.v99_r106_d1_basis_carry_preregistered import TRAIN_END
from research.tools.v99_r106_d1_full_train_guard import START

ASSETS = frozenset(('BTC', 'ETH'))


def _utc_hour(t):
    return (type(t) is datetime and t.tzinfo is timezone.utc
            and t.minute == t.second == t.microsecond == 0)


def _marks(row):
    if not isinstance(row, dict) or set(row) != ASSETS:
        raise ValueError('C129_COMPLETE_BTC_ETH_MARKS_REQUIRED')
    result = {}
    for asset in ASSETS:
        m = row[asset]
        if not isinstance(m, dict) or set(m) != {'spot', 'perp'}:
            raise ValueError('C129_PAIRED_SPOT_PERP_MARK_REQUIRED')
        result[asset] = {leg: _signed_decimal(m[leg]) for leg in ('spot', 'perp')}
        if any(v <= 0 for v in result[asset].values()):
            raise ValueError('C129_NONPOSITIVE_MARK')
    return result


def _same_inventory(before, after, error):
    if before[1:] != after[1:]:
        raise ValueError(error)


def reconcile_hourly_account(*, scenario, frames, initial_marks,
                             initial_marks_time, native_fee_schedule):
    """Re-execute hourly pre-trade accounting, then C128 native+stress fills.

    A frame is a UTC TRAIN hour with before/after_mark/after_funding/after
    full account snapshots, new paired marks, zero or more modeled funding
    settlements, and zero or more fill rows. All funding uses positions held
    *before* any same-hour fills. Funding is a MODEL, never a bank receipt.
    """
    if not isinstance(frames, (tuple, list)) or not frames:
        raise ValueError('C129_EMPTY_HOURLY_JOURNAL')
    if not _utc_hour(initial_marks_time):
        raise ValueError('C129_INITIAL_MARK_TIME_INVALID')
    prev_marks = _marks(initial_marks)
    prev_after = None
    prev_time = initial_marks_time
    mark_total = Decimal('0')
    funding_total = Decimal('0')
    fee_total = Decimal('0')
    fills_count = 0
    funded = set()
    modeled_nav_delta = Decimal('0')
    execution_slippage_total = Decimal('0')
    mark_fee_total = Decimal('0')
    for frame in frames:
        if not isinstance(frame, dict) or set(frame) != {
            'time', 'marks', 'before', 'after_mark', 'funding',
            'after_funding', 'fills', 'after'}:
            raise ValueError('C129_HOURLY_FRAME_SCHEMA')
        t = frame['time']
        if (not _utc_hour(t) or not START <= t < TRAIN_END
                or t != prev_time + timedelta(hours=1)):
            raise ValueError('C129_NONCONTIGUOUS_OR_SEALED_HOUR')
        marks = _marks(frame['marks'])
        before = _state(frame['before'])
        after_mark = _state(frame['after_mark'])
        after_funding = _state(frame['after_funding'])
        after = _state(frame['after'])
        if prev_after is not None and before != prev_after:
            raise ValueError('C129_CROSS_HOUR_ACCOUNT_DISCONTINUITY')
        _same_inventory(before, after_mark, 'C129_MARK_CHANGED_POSITIONS')
        expected_variation = sum(
            before[2][a] * (marks[a]['perp'] - prev_marks[a]['perp'])
            for a in ASSETS)
        if after_mark[0] != before[0] + expected_variation:
            raise ValueError('C129_PERP_VARIATION_MARGIN_MISMATCH')
        _same_inventory(after_mark, after_funding,
                        'C129_FUNDING_CHANGED_POSITIONS')
        rows = frame['funding']
        if not isinstance(rows, (list, tuple)) or len(rows) > len(ASSETS):
            raise ValueError('C129_FUNDING_EVENTS_INVALID')
        funding_cash = Decimal('0')
        seen = set()
        for r in rows:
            if not isinstance(r, dict) or set(r) != {
                    'asset', 'time', 'rate', 'source', 'instrument'}:
                raise ValueError('C129_FUNDING_EVENT_SCHEMA')
            a = r['asset']
            if (a not in ASSETS or a in seen or r['time'] != t or
                    r['source'] != 'OKX' or
                    r['instrument'] != f'{a}-USDT-SWAP' or
                    (a, t) in funded):
                raise ValueError('C129_DUPLICATE_OR_UNBOUND_FUNDING')
            rate = _signed_decimal(r['rate'])
            if abs(rate) > Decimal('.1'):
                raise ValueError('C129_FUNDING_RATE_OUT_OF_RANGE')
            funding_cash -= before[2][a] * marks[a]['perp'] * rate
            seen.add(a)
            funded.add((a, t))
        if after_funding[0] != after_mark[0] + funding_cash:
            raise ValueError('C129_MODELED_FUNDING_CASH_MISMATCH')
        fills = frame['fills']
        if not isinstance(fills, (tuple, list)):
            raise ValueError('C129_FILLS_LIST_REQUIRED')
        if fills:
            if _state(fills[0]['before']) != after_funding:
                raise ValueError('C129_FILLS_NOT_ANCHORED_TO_FUNDING')
            if any(f['time'] != t for f in fills):
                raise ValueError('C129_FILL_WRONG_HOUR')
            try:
                proof = reconcile_marked_two_asset_fills(
                    scenario=scenario, fills=fills,
                    marks={a:{leg:str(marks[a][leg]) for leg in ('spot','perp')}
                           for a in ASSETS},
                    native_fee_schedule=native_fee_schedule)
            except ValueError as exc:
                if any(_signed_decimal(f['execution_price_quote_per_base']) !=
                       marks[f['asset']][f['leg']] for f in fills):
                    raise ValueError('C129_OFF_MARK_FILL_REQUIRES_SLIPPAGE_LEDGER') from exc
                raise
            if _state(proof['last_declared_account_state']) != after:
                raise ValueError('C129_FINAL_FILL_STATE_MISMATCH')
            fee_total += Decimal(proof['total_economic_fee_quote'])
            fills_count += proof['fills_replayed']
            fill_nav_effect = (Decimal(proof['execution_slippage_pnl_quote']) -
                               Decimal(proof['fees_at_mark_quote']))
            execution_slippage_total += Decimal(proof['execution_slippage_pnl_quote'])
            mark_fee_total += Decimal(proof['fees_at_mark_quote'])
        elif after != after_funding:
            raise ValueError('C129_UNEXPLAINED_NO_FILL_ACCOUNT_CHANGE')
        if not fills:
            fill_nav_effect = Decimal('0')
        before_nav = before[0] + sum(before[1][a] * prev_marks[a]['spot'] for a in ASSETS)
        after_nav = after[0] + sum(after[1][a] * marks[a]['spot'] for a in ASSETS)
        expected_nav_delta = (sum(before[1][a] *
                                  (marks[a]['spot'] - prev_marks[a]['spot'])
                                  for a in ASSETS) + expected_variation +
                              funding_cash + fill_nav_effect)
        if after_nav - before_nav != expected_nav_delta:
            raise ValueError('C129_HOURLY_NAV_RECONCILIATION_MISMATCH')
        modeled_nav_delta += expected_nav_delta
        mark_total += expected_variation
        funding_total += funding_cash
        prev_time, prev_marks, prev_after = t, marks, after
    return {
        'status': 'C129_STRUCTURAL_HOURLY_ACCOUNT_ONLY_NO_ECONOMICS',
        'scenario': scenario, 'hours_replayed': len(frames),
        'fills_replayed': fills_count, 'funding_events_modeled': len(funded),
        'perp_variation_margin_quote': str(mark_total),
        'modeled_funding_quote': str(funding_total),
        'modeled_net_nav_delta_quote': str(modeled_nav_delta),
        'modeled_native_plus_stress_fees_quote': str(fee_total),
        'execution_slippage_pnl_quote': str(execution_slippage_total),
        'modeled_fees_at_mark_quote': str(mark_fee_total),
        'last_declared_account_state': frames[-1]['after'],
        'actual_okx_fills_authenticated': False,
        'native_fee_tier_authenticated': False,
        'actual_settled_funding_authenticated': False,
        'historical_economic_result_authorized': False,
        'validation_opened': False, 'holdout_opened': False,
        'promotion_authorized': False, 'orders_enabled': False,
    }


def reconcile_dual_cost_scenarios(*, frames_by_scenario, initial_marks,
                                  initial_marks_time, native_fee_schedule):
    """Bind both fee scenarios to the SAME exogenous market/funding path.

    Scenario-dependent trades/positions/capital are allowed and replayed
    separately; a better supersevere result is not thereby evidence of alpha.
    """
    scenarios = ('severe_model_only', 'supersevere_model_only')
    if not isinstance(frames_by_scenario, dict) or set(frames_by_scenario) != set(scenarios):
        raise ValueError('C129_BOTH_COST_SCENARIOS_REQUIRED')
    a, b = (frames_by_scenario[k] for k in scenarios)
    if len(a) != len(b) or not a:
        raise ValueError('C129_SCENARIO_HOUR_COUNTS_MISMATCH')
    for left, right in zip(a, b):
        if (left['time'] != right['time'] or
                _marks(left['marks']) != _marks(right['marks']) or
                left['funding'] != right['funding']):
            raise ValueError('C129_SCENARIO_EXOGENOUS_PATH_MISMATCH')
    proofs = {scenario: reconcile_hourly_account(
        scenario=scenario, frames=frames_by_scenario[scenario],
        initial_marks=initial_marks, initial_marks_time=initial_marks_time,
        native_fee_schedule=native_fee_schedule)
        for scenario in scenarios}
    return {'status': 'C129_DUAL_SCENARIO_MODEL_ONLY_NO_ECONOMICS',
            'proofs': proofs, 'same_exogenous_market_and_funding_path': True,
            'scenario_specific_positions_allowed': True,
            'scenario_ordering_is_not_alpha_proof': True,
            'historical_economic_result_authorized': False,
            'validation_opened': False, 'holdout_opened': False,
            'promotion_authorized': False, 'orders_enabled': False}
