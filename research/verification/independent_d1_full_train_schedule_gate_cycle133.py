"""C133 independent full-window funding schedule closure for frozen D1.

PRE-ECONOMIC, NO ORDERS. Reject a partial journal/schedule masquerading as
full historical TRAIN. Does NOT attest source, actual settlements, fee tiers,
execution fills or performance. No posthoc changes to D1 strategy parameters.
"""
from datetime import datetime, timedelta, timezone

from research.verification.independent_d1_funding_schedule_cycle132 import (
    audit_funding_schedule,
)

UTC = timezone.utc
TRAIN_START = datetime(2021, 12, 9, tzinfo=UTC)
TRAIN_END = datetime(2023, 10, 1, tzinfo=UTC)
TRAIN_HOURS = 15864
FUNDING_HOURS = 8
ASSETS = ('BTC', 'ETH')
FOLD_EDGES = (
    TRAIN_START,
    datetime(2022, 4, 20, 4, tzinfo=UTC),
    datetime(2022, 8, 30, 9, tzinfo=UTC),
    datetime(2023, 1, 9, 14, tzinfo=UTC),
    datetime(2023, 5, 21, 19, tzinfo=UTC),
    TRAIN_END,
)


def verify_full_train_funding_closure(frames, schedule):
    """Require exact 15,864h and 5 folds; no permission to score economics.

    The separately supplied schedule is a structural input, NOT authenticated
    first-party settlement. Each asset's original funding cadence must agree
    with the frozen 8-hour hypothesis, otherwise reject instead of retuning.
    """
    if type(frames) not in (list, tuple) or len(frames) != TRAIN_HOURS:
        raise ValueError('C133_FULL_TRAIN_15864H_REQUIRED')
    if (type(frames[0]) is not dict or type(frames[-1]) is not dict or
            frames[0].get('time') != TRAIN_START or
            frames[-1].get('time') != TRAIN_END - timedelta(hours=1)):
        raise ValueError('C133_TRAIN_BOUNDARY_MISMATCH')
    if type(schedule) is not dict or set(schedule) != set(ASSETS):
        raise ValueError('C133_BTC_ETH_SCHEDULE_REQUIRED')
    if (TRAIN_END - TRAIN_START) != timedelta(hours=TRAIN_HOURS):
        raise AssertionError('C133_FROZEN_TRAIN_CORRUPTED')
    for asset in ASSETS:
        times = schedule[asset]
        if type(times) not in (list, tuple) or len(times) != TRAIN_HOURS // FUNDING_HOURS:
            raise ValueError('C133_PREREG_FUNDING_CADENCE_COUNT_MISMATCH')
        if any(type(t) is not datetime or t.tzinfo is not UTC or
               t.minute or t.second or t.microsecond or
               not TRAIN_START <= t < TRAIN_END for t in times):
            raise ValueError('C133_INVALID_FUNDING_TIMESTAMP')
        if any(b - a != timedelta(hours=FUNDING_HOURS)
               for a, b in zip(times, times[1:])):
            raise ValueError('C133_PREREG_FUNDING_INTERVAL_MISMATCH')
    out = audit_funding_schedule(frames, schedule, start=TRAIN_START, end=TRAIN_END)
    folds = []
    for a, b in zip(FOLD_EDGES, FOLD_EDGES[1:]):
        i = int((a - TRAIN_START).total_seconds() // 3600)
        j = int((b - TRAIN_START).total_seconds() // 3600)
        if not 0 <= i < j <= TRAIN_HOURS or frames[i]['time'] != a or frames[j-1]['time'] != b-timedelta(hours=1):
            raise ValueError('C133_FOLD_BOUNDARY_MISMATCH')
        folds.append(j-i)
    if sum(folds) != TRAIN_HOURS:
        raise AssertionError('C133_FOLD_COVERAGE_CORRUPTED')
    return {
        'status': 'C133_FULL_TRAIN_STRUCTURAL_ONLY_NO_ECONOMICS',
        'journal_hours': TRAIN_HOURS, 'fold_hours': folds,
        'scheduled_funding_fixes_per_asset': TRAIN_HOURS // FUNDING_HOURS,
        'observed_funding_events': out['observed_fixes'],
        'schedule_source_authenticated': False,
        'account_settlement_authenticated': False,
        'native_fee_tier_authenticated': False,
        'execution_fills_authenticated': False,
        'historical_roi_authorized': False,
        'validation_opened': False, 'holdout_opened': False,
        'promotion_authorized': False, 'orders_enabled': False,
    }
