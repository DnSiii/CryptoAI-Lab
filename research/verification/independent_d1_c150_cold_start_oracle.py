"""C150 independent cold-start + C149 accounting oracle; synthetic only.

A balanced inherited spot/perp hedge can pass an accounting identity while
silently importing pre-TRAIN capital/exposure. No exchange authentication.
"""
from datetime import timedelta
from research.tools.v99_r106_d1_full_train_guard import START, HOURS
from research.verification.independent_d1_c149_account_oracle import oracle, state

WARMUP = 168
ASSETS = ('BTC', 'ETH')


def cold_start_oracle(journal, initial_marks, initial_marks_time, scenario,
                      *, full_train=False):
    frames = journal.get('frames')
    if not isinstance(frames, list) or len(frames) < WARMUP:
        raise ValueError('C150_INSUFFICIENT_WARMUP')
    if full_train and (len(frames) != HOURS or
                       initial_marks_time != START - timedelta(hours=1) or
                       frames[0].get('time') != START):
        raise ValueError('C150_FULL_TRAIN_BOUNDARY')
    if frames[0]['time'] != initial_marks_time + timedelta(hours=1):
        raise ValueError('C150_INITIAL_TIME_MISMATCH')
    cash, spot, perp = state(frames[0]['before'])
    if cash <= 0 or any(spot[a] != 0 or perp[a] != 0 for a in ASSETS):
        raise ValueError('C150_INHERITED_POSITION_OR_CAPITAL')
    expected = (cash, spot, perp)
    for i, fr in enumerate(frames[:WARMUP]):
        if fr['time'] != frames[0]['time'] + timedelta(hours=i):
            raise ValueError('C150_WARMUP_TIME_GAP')
        if fr['fills']:
            raise ValueError('C150_PREDECISION_FILL')
        for key in ('before', 'after_mark', 'after_funding', 'after'):
            if state(fr[key]) != expected:
                raise ValueError('C150_WARMUP_CAPITAL_CONTAMINATION')
    proof = oracle(journal, initial_marks, initial_marks_time, scenario)
    return {
        **proof,
        'status': 'C150_INDEPENDENT_COLD_START_AND_ACCOUNTING_SYNTHETIC_ONLY',
        'cold_start_cash_quote': str(cash),
        'flat_warmup_hours_verified': WARMUP,
        'no_predecision_capital_or_position_pnl': True,
        'exchange_authenticated': False,
        'historical_roi_authorized': False,
        'validation_opened': False,
        'holdout_opened': False,
        'promotion_authorized': False,
        'orders_enabled': False,
    }
