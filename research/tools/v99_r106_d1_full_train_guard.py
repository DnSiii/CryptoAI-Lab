"""Read-only D1 full TRAIN coverage gate; NEVER grants economic authorization.

Reject partial 200-hour synthetic samples masquerading as the preregistered
15,864-hour TRAIN. This is a calendar guard, not OKX authentication.
"""
from datetime import datetime, timedelta, timezone

UTC = timezone.utc
START = datetime(2021, 12, 9, tzinfo=UTC)
END = datetime(2023, 10, 1, tzinfo=UTC)
HOURS = 15864
FOLD_EDGES = (
    START,
    datetime(2022, 4, 20, 4, tzinfo=UTC),
    datetime(2022, 8, 30, 9, tzinfo=UTC),
    datetime(2023, 1, 9, 14, tzinfo=UTC),
    datetime(2023, 5, 21, 19, tzinfo=UTC),
    END,
)


def _parse_utc(value):
    if not isinstance(value, str) or not (value.endswith('Z') or value.endswith('+00:00')):
        raise ValueError('D1_EXPLICIT_UTC_REQUIRED')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('D1_INVALID_TIME') from exc
    if parsed.utcoffset() != timedelta(0):
        raise ValueError('D1_NON_UTC_TIME')
    return parsed


def check_complete_train(audit):
    """Check already independently audited paired grids, without parsing sealed data.

    Requires the *exact* preregistered period for both assets, not merely a
    contiguous but shortened window. Cannot prove original exchange source,
    fills, fee tiers, or account funding, and never authorizes PnL.
    """
    if not isinstance(audit, dict) or audit.get('status') != 'STRUCTURAL_ONLY_NOT_AUTHENTICATED':
        raise ValueError('D1_NATIVE_STRUCTURAL_AUDIT_REQUIRED')
    assets = audit.get('assets')
    if not isinstance(assets, dict) or set(assets) != {'BTC', 'ETH'}:
        raise ValueError('D1_COMPLETE_BTC_ETH_REQUIRED')
    if (END - START) != timedelta(hours=HOURS) or len(FOLD_EDGES) != 6 or any(
        a >= b for a, b in zip(FOLD_EDGES, FOLD_EDGES[1:])
    ):
        raise AssertionError('D1_PREREGISTERED_CALENDAR_CORRUPTED')
    for asset in ('BTC', 'ETH'):
        item = assets[asset]
        if not isinstance(item, dict):
            raise ValueError('D1_BAD_ASSET_AUDIT')
        try:
            first, last = _parse_utc(item['first_hour']), _parse_utc(item['last_hour'])
            count = item['paired_hours']
        except (KeyError, TypeError) as exc:
            raise ValueError('D1_MISSING_TRAIN_COVERAGE_FIELDS') from exc
        if (type(count) is not int or count != HOURS or first != START or
            last != END - timedelta(hours=1)):
            raise ValueError('D1_INCOMPLETE_OR_SHIFTED_TRAIN_GRID')
        if type(item.get('funding_rows')) is not int or item['funding_rows'] < 3:
            raise ValueError('D1_FUNDING_HISTORY_INSUFFICIENT')
    return {
        'status': 'COMPLETE_CALENDAR_STRUCTURAL_ONLY',
        'paired_hours_per_asset': HOURS,
        'five_chronological_folds': True,
        'exchange_authenticated': False,
        'historical_economics_authorized': False,
        'validation_opened': False,
        'holdout_opened': False,
        'promotion_authorized': False,
    }
