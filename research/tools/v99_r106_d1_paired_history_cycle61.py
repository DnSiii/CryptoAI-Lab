"""Strict historical BTC/ETH spot+swap candle coverage; source evidence, not PnL.

A source ZIP may contain duplicated, unconfirmed, stale or future observations.
Counting rows (rather than unique per-instrument UTC hours) is not a coverage
certificate. No market data are downloaded and no protected partition is read.
"""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

ASSETS = ('BTC', 'ETH')
REQUIRED = tuple(f'{asset}-USDT{suffix}' for asset in ASSETS for suffix in ('', '-SWAP'))
START = datetime(2021, 12, 9, tzinfo=timezone.utc)
END = datetime(2023, 10, 1, tzinfo=timezone.utc)
HOUR_MS = 3_600_000
START_MS = int(START.timestamp() * 1000)
END_MS = int(END.timestamp() * 1000)
EXPECTED = (END_MS - START_MS) // HOUR_MS


def _valid_candle(row):
    if not isinstance(row, list) or len(row) < 9 or str(row[-1]) != '1':
        return False
    try:
        o, h, l, c, volume = (Decimal(str(v)) for v in row[1:6])
        if not all(x.is_finite() for x in (o, h, l, c, volume)):
            return False
        return min(o, h, l, c) > 0 and volume >= 0 and h >= max(o, c) and l <= min(o, c) and h >= l
    except (InvalidOperation, ValueError, TypeError):
        return False


def assess_paired_hourly_coverage(candles_by_instrument: dict):
    """Return coverage diagnostics; NEVER authorize economics, validation or holdout.

    Each instrument must cover every UTC hourly candle in TRAIN exactly once.
    A duplicate (even a byte-identical duplicate) invalidates that hour.
    A missing, unconfirmed or malformed row invalidates that hour. Out-of-TRAIN
    rows are counted but never included in TRAIN coverage.
    """
    if not isinstance(candles_by_instrument, dict):
        raise TypeError('D1_C61_INSTRUMENT_MAP_REQUIRED')
    coverage = {}
    hour_sets = {}
    for inst in REQUIRED:
        rows = candles_by_instrument.get(inst)
        if not isinstance(rows, list):
            coverage[inst] = {'valid_unique_hours':0, 'missing_hours':EXPECTED,
                              'duplicate_hours':0, 'invalid_hours':0,
                              'outside_train_rows':0, 'complete':False}
            hour_sets[inst] = set()
            continue
        seen, invalid, duplicate = set(), set(), set()
        outside = 0
        for row in rows:
            try:
                ts = int(row[0])
                if str(row[0]) != str(ts):
                    raise ValueError('NONCANONICAL_TIMESTAMP')
            except (IndexError, TypeError, ValueError, OverflowError):
                raise ValueError('D1_C61_BAD_TIMESTAMP')
            if ts < START_MS or ts >= END_MS:
                outside += 1
                continue
            if (ts - START_MS) % HOUR_MS:
                raise ValueError('D1_C61_NON_HOURLY_TIMESTAMP')
            if ts in seen:
                duplicate.add(ts)
            seen.add(ts)
            if not _valid_candle(row):
                invalid.add(ts)
        valid = seen - invalid - duplicate
        hour_sets[inst] = valid
        coverage[inst] = {
            'valid_unique_hours':len(valid), 'missing_hours':EXPECTED-len(valid),
            'duplicate_hours':len(duplicate), 'invalid_hours':len(invalid),
            'outside_train_rows':outside,
            'complete':len(valid)==EXPECTED and not invalid and not duplicate,
        }
    intersection = set.intersection(*(hour_sets[i] for i in REQUIRED))
    return {
        'status':'SOURCE_COVERAGE_ONLY_NO_ECONOMICS_AUTHORIZATION',
        'expected_train_hours_per_instrument':EXPECTED,
        'required_instruments':list(REQUIRED),
        'per_instrument':coverage,
        'paired_four_leg_hours':len(intersection),
        'paired_four_leg_missing_hours':EXPECTED-len(intersection),
        'complete_structural_coverage':len(intersection)==EXPECTED and all(coverage[i]['complete'] for i in REQUIRED),
        'source_authenticated':False, 'account_receipts_authenticated':False,
        'historical_economics_authorized':False, 'validation_opened':False,
        'final_holdout_opened':False, 'promotion_authorized':False, 'orders_enabled':False,
    }
