#!/usr/bin/env python3
"""V98 Independent Phase243: fail-closed Binance USD-M 1h training archive assembler.

DATA_ONLY. Reads local, *original* monthly Binance futures ZIP archives, never
network or holdout. Uses the preregistered 2022-12 warmup through 2025-12,
five symbols, 1h contract. Archives are inputs, not trusted data: validate ZIP
members, UTC timestamps, all 12 raw columns, OHLCV geometry, quote/base units,
calendar and exact month coverage. Hash each original ZIP and raw member bytes.
Do not infer signal quality or strategy performance from this audit.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
from phase243_sell_residual_conservation import audit_trade_side_conservation

ASSETS = ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT')
MONTHS = tuple(f'{y:04d}-{m:02d}' for y in range(2022, 2026) for m in range(1,13)
               if (y,m) >= (2022,12))
CUTOFF = pd.Timestamp('2026-01-01T00:00:00Z')
COLUMNS = ('open_time','open','high','low','close','volume','close_time',
           'quote_volume','trade_count','taker_buy_base','taker_buy_quote','ignore')
# 1h Binance monthly archives are typically << 1 MiB uncompressed; this cap
# prevents accidental huge/wrong-frequency files and decompression bombs.
MAX_MEMBER_BYTES = 12_000_000


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_month(zip_path: Path, asset: str, month: str):
    if asset not in ASSETS or month not in MONTHS:
        raise ValueError('V98 frozen symbol/month or holdout firewall')
    name = f'{asset}-1h-{month}'
    if zip_path.stat().st_size > MAX_MEMBER_BYTES:
        raise ValueError(f'{name}: oversized ZIP')
    raw_zip = zip_path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as z:
        members = z.infolist()
        if len(members) != 1 or members[0].filename != name+'.csv':
            raise ValueError(f'{name}: archive must contain exactly the expected CSV')
        if members[0].is_dir() or members[0].file_size > MAX_MEMBER_BYTES:
            raise ValueError(f'{name}: invalid or oversized archive member')
        raw_csv = z.read(members[0])  # CRC checked by zipfile
    if len(raw_csv) > MAX_MEMBER_BYTES:
        raise ValueError(f'{name}: oversized decoded CSV')
    if not raw_csv or b'\x00' in raw_csv:
        raise ValueError(f'{name}: empty/binary CSV')
    # BOM may prefix an otherwise exact provider header; do not treat it as data.
    first = raw_csv.splitlines()[0].split(b',')[0].decode('utf-8-sig').strip().strip('"').lower()
    has_header = first in ('open_time', 'opentime')
    # Do not allow arbitrary headers, silently dropped lines, or unknown schema.
    d = pd.read_csv(io.BytesIO(raw_csv), header=0 if has_header else None,
                    dtype=str, keep_default_na=False, on_bad_lines='error')
    if has_header:
        hdr = tuple(x.strip().strip('\"').lower() for x in raw_csv.splitlines()[0].decode('utf-8-sig').split(','))
        # Historical USD-M 1h ZIPs also use count/taker_buy_volume labels.
        # Exact positional allowlist: reject unknown/reordered schemas.
        provider_tail = ('count','taker_buy_volume','taker_buy_quote_volume','ignore')
        provider_prefix = ('open_time','open','high','low','close','volume','close_time')
        allowed = (
            COLUMNS,
            ('open_time','open','high','low','close','volume','close_time',
             'quote_asset_volume','number_of_trades','taker_buy_base_asset_volume',
             'taker_buy_quote_asset_volume','ignore'),
            provider_prefix + ('quote_asset_volume',) + provider_tail,
            provider_prefix + ('quote_volume',) + provider_tail,
        )
        if hdr not in allowed:
            raise ValueError(f'{name}: unrecognized or reordered CSV header')
    if d.shape[1] != len(COLUMNS):
        raise ValueError(f'{name}: expected exactly 12 Binance kline fields')
    d.columns = COLUMNS
    if len(d) == 0 or (d == '').any().any():
        raise ValueError(f'{name}: empty or missing cell')
    # Timestamp unit is inferred *only* from raw magnitude, never guessed by
    # date; future 2026+ data is rejected by the exact expected month grid.
    ts = pd.to_numeric(d.open_time, errors='raise').to_numpy(dtype=np.float64)
    te = pd.to_numeric(d.close_time, errors='raise').to_numpy(dtype=np.float64)
    if not (np.isfinite(ts).all() and np.isfinite(te).all()):
        raise ValueError(f'{name}: nonfinite timestamp')
    if not (np.all(ts == np.floor(ts)) and np.all(te == np.floor(te))):
        raise ValueError(f'{name}: fractional timestamp')
    # Year 2022-25 milliseconds are ~1.7e12; microseconds ~1.7e15.
    scale = 1000 if 1e12 < ts[0] < 2e12 else (1_000_000 if 1e15 < ts[0] < 2e15 else None)
    if scale is None or not np.all((ts > (1e12 if scale == 1000 else 1e15)) &
                                    (ts < (2e12 if scale == 1000 else 2e15))):
        raise ValueError(f'{name}: unsupported or mixed timestamp unit')
    # Integer-valued timestamps within 2022-25 are exactly representable as f64.
    expected = pd.date_range(month+'-01', periods=1, tz='UTC')
    next_month = expected[0] + pd.offsets.MonthBegin(1)
    hours = pd.date_range(expected[0], next_month-pd.Timedelta(hours=1),freq='h')
    expected_ms = (hours.as_unit('ns').asi8 // 1_000_000).astype(np.int64)
    observed_ms = (ts / (scale/1000)).astype(np.int64)
    if len(observed_ms) != len(hours) or not np.array_equal(observed_ms, expected_ms):
        raise ValueError(f'{name}: missing/duplicate/shifted hourly bar or wrong month')
    # Binance's inclusive close_time is exactly 1 hour minus 1 ms/us.
    close_delta = 3_600_000 * (scale/1000) - 1
    if not np.all(te - ts == close_delta):
        raise ValueError(f'{name}: inconsistent close_time / timestamp unit')
    fields = ('open','high','low','close','volume','quote_volume',
              'trade_count','taker_buy_base','taker_buy_quote')
    numeric = d.loc[:,fields].apply(pd.to_numeric,errors='raise').to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError(f'{name}: NaN/Inf numeric field')
    o,h,l,c,v,q,n,tb,tq = (numeric[:,j] for j in range(9))
    if np.any(np.minimum.reduce([o,h,l,c]) <= 0) or np.any(np.minimum.reduce([v,q,n,tb,tq]) < 0):
        raise ValueError(f'{name}: negative volume/trades or nonpositive price')
    tol = 1e-9 * np.maximum.reduce([o,h,l,c])
    if np.any(h+tol < np.maximum(o,c)) or np.any(l-tol > np.minimum(o,c)) or np.any(h+tol < l):
        raise ValueError(f'{name}: invalid OHLC geometry')
    lower = v*l - 1e-6*np.maximum(1,q)
    upper = v*h + 1e-6*np.maximum(1,q)
    bad_vwap = (q < lower) | (q > upper)
    if np.any(bad_vwap):
        j = int(np.flatnonzero(bad_vwap)[0])
        raise ValueError(
            f'{name}: quote/base VWAP units inconsistent; row={j} '
            f'open_time={d.open_time.iloc[j]} base={v[j]:.17g} '
            f'quote={q[j]:.17g} low={l[j]:.17g} high={h[j]:.17g} '
            f'lower={lower[j]:.17g} upper={upper[j]:.17g} '
            f'violations={int(np.sum(bad_vwap))}')
    if np.any(tb > v + 1e-6*np.maximum(1,v)) or np.any(tq > q + 1e-6*np.maximum(1,q)):
        raise ValueError(f'{name}: taker-buy exceeds total traded volume')
    # No executed base volume can generate nonzero quote turnover; likewise
    # a zero taker-buy base cannot generate positive taker-buy quote volume.
    # Both directions are required: the absolute VWAP tolerance can otherwise
    # hide tiny positive base amounts paired with exactly zero quote turnover.
    if np.any((v == 0) != (q == 0)) or np.any((tb == 0) != (tq == 0)):
        raise ValueError(f'{name}: impossible zero-volume quote turnover')
    # The taker-buy fields are a second, independent price/volume witness.
    # An archive can satisfy total quote/base VWAP yet contain a corrupted
    # taker-buy quote value. Do not allow that silent inconsistency.
    taker_tol = 1e-6*np.maximum(1.,tq)
    if np.any(tq < tb*l-taker_tol) or np.any(tq > tb*h+taker_tol):
        raise ValueError(f'{name}: taker-buy quote/base VWAP units inconsistent')
    # Independently check implied seller residual conservation. The buy and
    # total VWAPs can both be legal while their difference is impossible.
    audit_trade_side_conservation(l,h,v,q,tb,tq)
    # The Binance 12th kline field is a reserved `ignore` field, not an
    # arbitrary payload. A nonzero/nonfinite value signals schema drift.
    ignore = pd.to_numeric(d['ignore'],errors='raise').to_numpy(dtype=float)
    if not np.isfinite(ignore).all() or np.any(ignore != 0):
        raise ValueError(f'{name}: invalid Binance reserved ignore field')
    if np.any(n != np.floor(n)) or np.any((n == 0) & (v > 0)):
        raise ValueError(f'{name}: invalid trade count')
    out = pd.DataFrame({'open_time':hours, 'open':o, 'high':h, 'low':l,
                        'close':c, 'volume':v, 'quote_volume':q})
    evidence = {'archive_sha256':_sha(raw_zip),'member_sha256':_sha(raw_csv),
                'rows':len(out),'timestamp_unit':'ms' if scale==1000 else 'us',
                'header_present':has_header,'first':hours[0].isoformat(),
                'last':hours[-1].isoformat(), 'zero_volume_bars':int(np.sum(v==0))}
    return out, evidence


def assemble(archive_root: Path, output_root: Path, *, write: bool = True):
    """Validate *all* 185 frozen archives before publishing any output.

    Call with write=False for an immutable integrity dry-run. Never consumes
    2026+ data or writes outside the V98-only caller-selected output root.
    """
    root, dest = Path(archive_root), Path(output_root)
    if 'v98_independent' not in root.resolve().parts:
        raise ValueError('archive root must resolve inside V98 Independent namespace')
    if len(MONTHS) != 37 or MONTHS[0] != '2022-12' or MONTHS[-1] != '2025-12':
        raise RuntimeError('frozen month enumeration changed')
    if 'v98_independent' not in dest.resolve().parts:
        raise ValueError('output path must be under V98 Independent namespace')
    manifest = {'mode':'V98_PHASE243_BINANCE_1H_SOURCE_ONLY_NO_ALPHA',
                'source':'Binance USD-M monthly klines archives',
                'market':'USD-M perpetual futures','interval':'1h',
                'months':list(MONTHS),'holdout_accessed':False,
                'cut_exclusive':CUTOFF.isoformat(),'assets':{},
                'promotion_eligible':False}
    frames = {}
    fingerprints = {}
    for asset in ASSETS:
        pieces=[]; month_ev={}
        for month in MONTHS:
            path = root / 'klines' / asset / '1h' / f'{asset}-1h-{month}.zip'
            df,ev = _parse_month(path,asset,month)
            pieces.append(df);month_ev[month]=ev
        joined=pd.concat(pieces,ignore_index=True)
        ix=pd.DatetimeIndex(joined.open_time)
        if (ix.has_duplicates or not ix.is_monotonic_increasing or
            not (ix[1:]-ix[:-1] == pd.Timedelta(hours=1)).all() or
            ix[0] != pd.Timestamp('2022-12-01T00:00:00Z') or
            ix[-1] != CUTOFF-pd.Timedelta(hours=1)):
            raise ValueError(f'{asset}: global continuity/holdout failure')
        frames[asset]=joined
        fingerprint=_sha(joined[['open','close','volume','quote_volume']].to_numpy(dtype='<f8').tobytes())
        if fingerprint in fingerprints.values():
            raise ValueError(f'{asset}: suspicious identical cross-asset price/volume panel')
        fingerprints[asset]=fingerprint
        manifest['assets'][asset]={'months':month_ev,'rows':len(joined),
                                   'cross_asset_panel_fingerprint':fingerprint,
                                   'first':ix[0].isoformat(),'last':ix[-1].isoformat()}
    if write:
        dest.mkdir(parents=True,exist_ok=True)
        for asset,df in frames.items():
            # Serialize deterministically; hash *actual* canonical output bytes.
            raw=df.to_csv(index=False,float_format='%.12g').encode('utf-8')
            (dest/f'{asset}_1h.csv').write_bytes(raw)
            manifest['assets'][asset]['canonical_sha256']=_sha(raw)
        (dest/'source_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True,allow_nan=False)+'\n')
    return manifest


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--archive-root',required=True)
    p.add_argument('--output-root',default='research/v98_independent/phase243_canonical_prices')
    p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    out=assemble(Path(a.archive_root),Path(a.output_root),write=not a.dry_run)
    print(json.dumps({'mode':out['mode'],'assets':len(out['assets']),
                      'rows_per_asset':out['assets']['BTCUSDT']['rows'],
                      'decision':'PASS_SOURCE_ONLY_NOT_ALPHA'}))

if __name__=='__main__':main()
