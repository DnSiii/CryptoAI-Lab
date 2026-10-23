"""C132 independent source-only funding calendar audit; not receipt authentication.

Checks a *separately supplied* schedule against the journal. The schedule must
ultimately come from independently verified historical OKX instrument terms;
caller-provided times alone can never authorize economic claims.
"""
from datetime import datetime, timezone

ASSETS = ('BTC', 'ETH')


def _hour(t):
    return (type(t) is datetime and t.tzinfo is timezone.utc and
            t.minute == t.second == t.microsecond == 0)


def audit_funding_schedule(frames, expected_by_asset, *, start, end):
    if not (_hour(start) and _hour(end) and start < end):
        raise ValueError('C132_BAD_TRAIN_WINDOW')
    if not isinstance(expected_by_asset, dict) or set(expected_by_asset) != set(ASSETS):
        raise ValueError('C132_MISSING_EXTERNAL_SCHEDULE')
    if not isinstance(frames, (list, tuple)) or not frames:
        raise ValueError('C132_EMPTY_JOURNAL')
    schedule = set()
    for asset in ASSETS:
        times = expected_by_asset[asset]
        if not isinstance(times, (list, tuple)):
            raise ValueError('C132_INVALID_EXTERNAL_SCHEDULE')
        if any(not _hour(t) or not start <= t < end for t in times):
            raise ValueError('C132_SEALED_OR_INVALID_FIX_TIME')
        if list(times) != sorted(set(times)):
            raise ValueError('C132_DUPLICATE_OR_UNORDERED_SCHEDULE')
        schedule.update((asset, t) for t in times)
    observed = set()
    previous = None
    for frame in frames:
        if not isinstance(frame, dict) or not _hour(frame.get('time')):
            raise ValueError('C132_INVALID_JOURNAL_FRAME')
        t = frame['time']
        if not start <= t < end or (previous is not None and (t - previous).total_seconds() != 3600):
            raise ValueError('C132_NONCONTIGUOUS_OR_SEALED_HOUR')
        previous = t
        if not isinstance(frame.get('funding'), (list, tuple)):
            raise ValueError('C132_INVALID_FUNDING_ROWS')
        for row in frame['funding']:
            if (not isinstance(row, dict) or row.get('asset') not in ASSETS or
                    row.get('time') != t):
                raise ValueError('C132_INVALID_FUNDING_EVENT')
            event = (row['asset'], t)
            if event in observed:
                raise ValueError('C132_DUPLICATE_FUNDING_EVENT')
            observed.add(event)
    # Require exact match only for the hours actually present in this journal.
    window = {key for key in schedule if frames[0]['time'] <= key[1] <= frames[-1]['time']}
    if observed != window:
        raise ValueError('C132_UNSCHEDULED_OR_MISSING_FUNDING_FIX')
    return {'status': 'C132_STRUCTURAL_SCHEDULE_ONLY_NO_ECONOMICS',
            'journal_hours': len(frames), 'scheduled_fixes_in_journal': len(window),
            'observed_fixes': len(observed), 'schedule_source_authenticated': False,
            'account_settlement_authenticated': False,
            'historical_roi_authorized': False, 'validation_opened': False,
            'holdout_opened': False, 'promotion_authorized': False,
            'orders_enabled': False}
