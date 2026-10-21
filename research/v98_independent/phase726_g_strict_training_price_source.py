#!/usr/bin/env python3
"""V98 Independent Phase726: immutable streaming OHLC training-prefix loader.

Reads exactly header + Dec-2022..Dec-2024 rows; never parses 2025 rows.
Training source integrity only, not vendor-origin attestation or economic PnL.
"""
from __future__ import annotations
import hashlib,io
from pathlib import Path
import numpy as np
import pandas as pd
from phase698_f_training_structure import ROOT,INDEX,ASSETS,N

PREFIX_SHA={
 'BTCUSDT':'5fecf1d58c8f998c9bba2a3f937c384896bf8d794b98a2755b17af807b3f0190',
 'ETHUSDT':'541748f469cddf34579a3f7865bdec04dab86f886dbd029e90b69ae24ab1325f',
 'BNBUSDT':'f0776970a530a37fe8f5c434b080fe46919ddb5194d3aa98d02589fed0a2d058',
 'SOLUSDT':'fa7b07c0892370da2375fb4be2ba1dc82fe700173f0eb8b0807ef16b303ca085'}
FIELDS=('open','high','low','close','volume','quote_volume')
# Immutable byte-exact prefix lengths: header + 18,288 hourly bars only.
# A bounded read never requests a 2025 byte, including at the buffered I/O layer.
PREFIX_BYTES={'BTCUSDT':1451038,'ETHUSDT':1479522,
              'BNBUSDT':1384866,'SOLUSDT':1371664}

def read_training_price_prefix(asset, root=ROOT):
    if asset not in ASSETS:
        raise ValueError('forbidden price asset')
    p=Path(root)/'phase243_clean4_canonical'/f'{asset}_1h.csv'
    with p.open('rb',buffering=0) as f:
        prefix=f.read(PREFIX_BYTES[asset])
    if (len(prefix)!=PREFIX_BYTES[asset] or not prefix.endswith(b'\n') or
            prefix.count(b'\n')!=N+1 or
            hashlib.sha256(prefix).hexdigest()!=PREFIX_SHA[asset]):
        raise ValueError(asset+': immutable training-only prefix digest mismatch')
    return prefix

def load_training_prices(root=ROOT):
    root=Path(root)
    arrays={k:np.empty((N,4),float) for k in FIELDS}
    for j,asset in enumerate(ASSETS):
        prefix=read_training_price_prefix(asset,root)
        frame=pd.read_csv(io.BytesIO(prefix))
        if list(frame.columns)!=['open_time',*FIELDS] or len(frame)!=N:
            raise ValueError(asset+': training-only price schema/row count')
        t=pd.DatetimeIndex(pd.to_datetime(frame.open_time,utc=True,errors='raise'))
        if not t.equals(INDEX):raise ValueError(asset+': training-only UTC calendar mismatch')
        for k in FIELDS:arrays[k][:,j]=frame[k].to_numpy(float)
    if any(not np.isfinite(a).all() for a in arrays.values()):
        raise ValueError('training OHLCV contains nonfinite value')
    p,c,h,l=(arrays[k] for k in ('open','close','high','low'))
    if ((l<=0)|(l>np.minimum(p,c))|(h<np.maximum(p,c))).any():
        raise ValueError('training OHLC geometry invalid')
    if (arrays['volume']<0).any() or (arrays['quote_volume']<0).any():
        raise ValueError('training liquidity negative')
    return {'prices':{k:arrays[k] for k in ('open','high','low','close')},
        'no_trade':arrays['volume']==0,
        'quote_volume':arrays['quote_volume'],
        'training_prefix_only':True,'validation_2025_prices_read':False,
        'vendor_origin_attested':False,'historical_pnl_computed':False}
