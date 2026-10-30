#!/usr/bin/env python3
"""V98 Independent Phase733: canonical Phase206 native training-only funding reader.

No 2025+ reads; no vendor attestation or PnL. The Phase206 CSV begins in
Jan-2022. SOL had 75 extra 2h/4h pretraining events in Nov-2022.
"""
from __future__ import annotations
import csv
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone, timedelta
from itertools import islice
from pathlib import Path

ASSETS = ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT')
SOURCE_START = 1640995200000  # Jan-2022 native file first event
TRAIN_START = 1669852800000   # Dec-2022 V98 warmup
TRAIN_CUT = 1735689600000     # Jan-2025 (exclusive)
STEP = 28800000
TRAIN_EVENTS = (TRAIN_CUT - TRAIN_START) // STEP  # 2286
PRETRAIN_ROWS = {'BTCUSDT': 1002, 'ETHUSDT': 1002,
                 'BNBUSDT': 1002, 'SOLUSDT': 1077}
SCHEMA = ['fundingTime_ms', 'fundingTime_utc', 'fundingRate', 'fundingIntervalHours']
assert TRAIN_EVENTS == 2286


def native_prefix(asset: str, manifest=None, root=None):
    """Return Dec-2022..Dec-2024 funding; read no bytes of 2025 rows.

    `manifest` is accepted for compatibility with the Phase728 call site.
    This function validates the pinned source-only structure; the caller must
    independently attest official vendor ZIP/CHECKSUM/API before economics.
    """
    if asset not in ASSETS:
        raise ValueError('forbidden funding asset')
    if root is None:
        root = Path(__file__).resolve().parent
    path = Path(root) / 'data/phase206_funding' / f'{asset}_funding.csv'
    early = PRETRAIN_ROWS[asset]
    # Read exactly the header and the known 2022-2024 records, not even the
    # first 2025 line. A truncated/misaligned prefix is rejected below.
    with path.open('rb', buffering=0) as fh:
        prefix = b''.join(islice(fh, early + TRAIN_EVENTS + 1))
    try:
        from io import StringIO
        rd = csv.DictReader(StringIO(prefix.decode('utf-8-sig')))
        if rd.fieldnames != SCHEMA:
            raise ValueError(f'{asset}: native funding schema mismatch')
        result = {}
        previous = -1
        count = 0
        for i, row in enumerate(rd):
            count += 1
            timestamp = int(row['fundingTime_ms'])
            utc_text = datetime.fromisoformat(row['fundingTime_utc'])
            if utc_text.tzinfo is None or utc_text.utcoffset() != timedelta(0):
                raise ValueError(f'{asset}: funding UTC label lacks zero offset')
            utc = utc_text.astimezone(timezone.utc)
            delta = utc - datetime(1970, 1, 1, tzinfo=timezone.utc)
            label_ms = delta.days*86400000 + delta.seconds*1000 + delta.microseconds//1000
            if delta.microseconds % 1000 or label_ms != timestamp:
                raise ValueError(f'{asset}: funding UTC label/timestamp mismatch')
            rate = Decimal(row['fundingRate'])
            interval = Decimal(row['fundingIntervalHours'])
            if not (timestamp > previous and SOURCE_START <= timestamp < TRAIN_CUT
                    and rate.is_finite() and interval in (2, 4, 8)):
                raise ValueError(f'{asset}: native funding time/rate invalid')
            if i < early:
                if timestamp >= TRAIN_START:
                    raise ValueError(f'{asset}: pretraining row count drift')
                if i == 0 and not SOURCE_START <= timestamp <= SOURCE_START + 29:
                    raise ValueError(f'{asset}: native source start mismatch')
            else:
                slot = TRAIN_START + (i - early) * STEP
                if not slot <= timestamp <= slot + 29 or interval != 8:
                    raise ValueError(f'{asset}: training funding calendar mismatch')
                result[slot] = (timestamp, interval, rate)
            previous = timestamp
        if count != early + TRAIN_EVENTS or len(result) != TRAIN_EVENTS:
            raise ValueError(f'{asset}: incomplete native training prefix')
        return result
    except (UnicodeError, KeyError, TypeError, InvalidOperation) as exc:
        raise ValueError(f'{asset}: malformed native funding prefix') from exc
