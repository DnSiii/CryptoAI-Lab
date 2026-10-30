#!/usr/bin/env python3
"""V98 AC four-runner official source-only 15 integer-hash attestation.

Fresh vendor OHLC and native mark/funding, no historical PnL, 2025, XRP,
external benchmarks or rejected-engine signal imports.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from phase1174_ac_discrete_intents import ASSETS, MODES, PATHS, compose_intents, canonical_hash
from phase803_training_ohlc_official_replay import run as official_ohlc, PASS as OHLC_PASS, PINS
from phase1000_four_asset_source_policy import run as official_mark, OUT as MARK_OUT, BOUNDS

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'phase1175_ac_authenticated_source_receipt.json'
START = pd.Timestamp('2022-12-01T00:00:00Z')
END = pd.Timestamp('2024-12-31T23:00:00Z')
FIELDS = ('asset', 'funding_slot_ms', 'funding_time_ms', 'funding_rate',
          'mark_low', 'mark_high', 'conservative_mark')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_frames():
    idx = pd.date_range(START, END, freq='h')
    if len(idx) != 18288:
        raise ValueError('AC1175_CALENDAR')
    frames = {}
    for asset in ASSETS:
        path = ROOT / 'phase243_clean4_canonical' / (asset + '_1h.csv')
        expected_sha, expected_size = PINS[asset]
        if path.stat().st_size != expected_size or sha256(path) != expected_sha:
            raise PermissionError('AC1175_PIN_' + asset)
        frame = pd.read_csv(path)
        if (len(frame) != len(idx) or tuple(frame.columns) !=
                ('open_time', 'open', 'high', 'low', 'close', 'volume', 'quote_volume')):
            raise ValueError('AC1175_OHLC_SCHEMA_' + asset)
        if not pd.DatetimeIndex(pd.to_datetime(frame['open_time'], utc=True)).equals(idx):
            raise ValueError('AC1175_OHLC_TIME_' + asset)
        frames[asset] = frame
    data = {}
    for field in ('open', 'high', 'low', 'close', 'quote_volume'):
        data[field] = pd.DataFrame({asset: frames[asset][field].to_numpy(dtype=float)
                                    for asset in ASSETS}, index=idx)
    return idx, data


def native_bounds(idx):
    n = len(idx)
    rate = np.zeros((n, 4), dtype=float)
    event = np.zeros((n, 4), dtype=bool)
    low = np.full((n, 4), np.nan)
    high = np.full((n, 4), np.nan)
    first = int(START.timestamp() * 1000)
    with BOUNDS.open(newline='') as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError('AC1175_NATIVE_SCHEMA')
        for row in reader:
            asset = row['asset']
            if asset not in ASSETS:
                raise ValueError('AC1175_NON_CLEAN4')
            j = ASSETS.index(asset)
            slot, ts = int(row['funding_slot_ms']), int(row['funding_time_ms'])
            if (slot < first or slot > int(END.timestamp() * 1000)
                    or (slot - first) % 28_800_000 or not slot <= ts <= slot + 29):
                raise ValueError('AC1175_FUNDING_CALENDAR')
            t = (slot - first) // 3_600_000
            if event[t, j]:
                raise ValueError('AC1175_DUPLICATE_NATIVE_EVENT')
            r = float(row['funding_rate'])
            lo = float(row['mark_low'])
            hi = float(row['mark_high'])
            mark = float(row['conservative_mark'])
            if (not np.isfinite([r, lo, hi, mark]).all() or lo <= 0 or hi < lo
                    or mark != (hi if r >= 0 else lo)):
                raise ValueError('AC1175_SIGNED_MARK')
            rate[t, j], low[t, j], high[t, j], event[t, j] = r, lo, hi, True
    if (int(event.sum()) != 9144 or
            any(int(event[:, j].sum()) != 2286 for j in range(4)) or
            not np.isfinite(low[event]).all() or not np.isfinite(high[event]).all() or
            np.isfinite(low[~event]).any() or np.isfinite(high[~event]).any()):
        raise ValueError('AC1175_NATIVE_GEOMETRY')
    return pd.DataFrame(rate, index=idx, columns=ASSETS), event


def attest(idx, data, funding, event):
    if (len(idx) != 18288 or idx[0] != START or idx[-1] != END
            or event.shape != (len(idx), 4) or int(event.sum()) != 9144):
        raise ValueError('AC1175_TRAINING_ONLY')
    result, diag = compose_intents(data['open'], data['high'], data['low'],
                                   data['close'], data['quote_volume'], funding,
                                   diagnostics=True)
    hashes = {p + '__' + m: canonical_hash(result[p, m], idx, p, m)
              for p in PATHS for m in MODES}
    if len(hashes) != 15 or len(set(hashes.values())) != 15:
        raise ValueError('AC1175_15_HASH_GEOMETRY')
    return {'canonical_sha256': dict(sorted(hashes.items())),
            'official_hours': len(idx), 'native_funding_events': int(event.sum()),
            'typed_mark_shape': [len(idx), 4, 2],
            'typed_mark_csv_sha256': sha256(BOUNDS),
            'diagnostics': diag}


def run():
    receipt = {'phase': 1175, 'decision': 'BLOCKED_BEFORE_PNL',
               'source_only': True, 'historical_pnl_computed': False,
               'validation_2025_read': False, 'holdout_accessed': False,
               'external_benchmarks_used': False, 'promotion_eligible': False,
               'frozen': False}
    try:
        o = official_ohlc()
        if (o.get('decision') != OHLC_PASS or o.get('vendor_origin_attested') is not True
                or any(o.get('assets', {}).get(a, {}).get('sha256') != PINS[a][0]
                       for a in ASSETS)):
            raise PermissionError('AC1175_OFFICIAL_OHLC')
        if official_mark() != 0:
            raise PermissionError('AC1175_OFFICIAL_NATIVE_MARK')
        mark_receipt = json.loads(MARK_OUT.read_text())
        if (mark_receipt.get('decision') !=
                'PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY'
                or mark_receipt.get('vendor_archive_checksum_attested') is not True
                or mark_receipt.get('verified_asset_events') != 9144
                or mark_receipt.get('validation_2025_read') is not False
                or mark_receipt.get('bounds_csv_sha256') != sha256(BOUNDS)):
            raise PermissionError('AC1175_NATIVE_VENDOR_PROVENANCE')
        idx, data = source_frames()
        funding, event = native_bounds(idx)
        receipt.update(attest(idx, data, funding, event))
        receipt['decision'] = 'PASS_AC_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN'
    except Exception as exc:
        receipt['reason'] = type(exc).__name__ + ': ' + str(exc)[:350]
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({k: receipt.get(k) for k in ('phase', 'decision', 'reason',
                 'official_hours', 'native_funding_events', 'canonical_sha256')}, sort_keys=True))
    return 0 if receipt['decision'].startswith('PASS_') else 2


if __name__ == '__main__':
    raise SystemExit(run())
