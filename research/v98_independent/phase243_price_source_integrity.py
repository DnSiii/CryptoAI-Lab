#!/usr/bin/env python3
"""V98-only Phase243 five-asset hourly canonical OHLCV source gate.

No alpha, no fill-forward, no 2026+ data. This checks training coverage,
calendar continuity, OHLC invariants and quote-volume units/provenance. A
successful result is DATA_ONLY, not a profitable trading system.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT')
START=pd.Timestamp('2023-01-01T00:00:00Z')
CUT=pd.Timestamp('2026-01-01T00:00:00Z')
TIME_NAMES=('open_time','timestamp','time','datetime','date')
QUOTE_NAMES=('quote_volume','quote_asset_volume','quotevolume')
BASE_NAMES=('volume','base_volume','base_asset_volume')


def audit_price_panel(root:Path, start=START, cut=CUT, *, warmup_hours=336):
    if start < START or cut > CUT or cut <= start:
        raise ValueError('holdout firewall or invalid training window')
    if warmup_hours < 0 or warmup_hours > 10000:
        raise ValueError('invalid warmup')
    expected=pd.date_range(start-pd.Timedelta(hours=warmup_hours),
                           cut-pd.Timedelta(hours=1),freq='h')
    manifest={'mode':'V98_ONLY_PRICE_SOURCE_DATA_ONLY_NO_ALPHA',
              'holdout_accessed':False,'start':start.isoformat(),
              'cut_exclusive':cut.isoformat(),'warmup_hours':warmup_hours,
              'expected_rows':len(expected),'assets':{}}
    opens={};closes={};quotes={}
    for asset in ASSETS:
        path=Path(root)/f'{asset}_1h.csv'
        raw=path.read_bytes()
        d=pd.read_csv(path)
        names={str(c).lower():c for c in d.columns}
        if len(names)!=len(d.columns):
            raise ValueError(f'{asset}: ambiguous duplicate-case column names')
        time=next((names[k] for k in TIME_NAMES if k in names),None)
        quote=next((names[k] for k in QUOTE_NAMES if k in names),None)
        base=next((names[k] for k in BASE_NAMES if k in names),None)
        if time is None or quote is None or any(k not in names for k in ('open','high','low','close')):
            raise ValueError(f'{asset}: missing canonical OHLC/quote volume fields')
        idx=pd.DatetimeIndex(pd.to_datetime(d[time],utc=True,errors='raise'))
        if idx.hasnans or idx.has_duplicates or not idx.is_monotonic_increasing:
            raise ValueError(f'{asset}: duplicate, null or unordered price timestamp')
        if (idx>=CUT).any():
            raise ValueError(f'{asset}: 2026+ holdout row present')
        if not (idx==idx.floor('h')).all():
            raise ValueError(f'{asset}: off-hour price timestamp')
        chosen=(idx>=expected[0])&(idx<=expected[-1])
        observed=idx[chosen]
        if not observed.equals(expected):
            raise ValueError(f'{asset}: missing or extra hourly price bar')
        x=d.loc[chosen,[names[k] for k in ('open','high','low','close')]+[quote]].apply(pd.to_numeric,errors='raise')
        a=x.to_numpy(dtype=float)
        if not np.isfinite(a).all() or (a[:,:4]<=0).any() or (a[:,4]<0).any():
            raise ValueError(f'{asset}: nonfinite/nonpositive price or invalid quote volume')
        o,h,l,c,v=(a[:,i] for i in range(5))
        tol=1e-10*np.maximum.reduce([o,h,l,c])
        if np.any(h+tol < np.maximum(o,c)) or np.any(l-tol > np.minimum(o,c)) or np.any(h+tol < l):
            raise ValueError(f'{asset}: invalid OHLC candle geometry')
        # Decision-grade unit provenance: quote traded notional must agree
        # with base traded quantity times a VWAP within [low, high].
        # Fail closed when base volume is absent; cannot validate units.
        if base is None:
            raise ValueError(f'{asset}: base volume required for decision-grade quote-volume unit check')
        base_vol=pd.to_numeric(d.loc[chosen,base],errors='raise').to_numpy(dtype=float)
        if not np.isfinite(base_vol).all() or np.any(base_vol<0):
            raise ValueError(f'{asset}: invalid base volume')
        margin=1e-6*np.maximum(1.,np.abs(v))
        if np.any(v < base_vol*l-margin) or np.any(v > base_vol*h+margin):
            raise ValueError(f'{asset}: quote-volume/base-volume unit inconsistency')
        opens[asset]=o;closes[asset]=c;quotes[asset]=v
        manifest['assets'][asset]={
            'sha256_raw_csv':hashlib.sha256(raw).hexdigest(),
            'rows':int(len(a)),
            'first':observed[0].isoformat(),'last':observed[-1].isoformat(),
            'quote_volume_column':str(quote),
            'base_volume_column':str(base),
            'quote_base_consistency_checked':True,
            'zero_quote_volume_bars':int(np.sum(v==0)),
            'min_open':float(o.min()),'max_open':float(o.max()),
            'max_abs_open_close_gap':float(np.max(np.abs(c/o-1))),
        }
    op=pd.DataFrame(opens,index=expected)
    cl=pd.DataFrame(closes,index=expected)
    qv=pd.DataFrame(quotes,index=expected)
    manifest['quote_base_unit_gate']='PASS_ALL_FIVE_ASSETS'
    manifest['panel_sha256']=hashlib.sha256(np.column_stack([
        op.to_numpy(dtype='<f8'),cl.to_numpy(dtype='<f8'),qv.to_numpy(dtype='<f8')]).tobytes()).hexdigest()
    return {'manifest':manifest,'opens':op,'closes':cl,'quote_volume':qv}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data-root',default='data/canonical')
    p.add_argument('--out',default='research/v98_independent/phase243_price_source_integrity_results.json')
    p.add_argument('--warmup-hours',type=int,default=336)
    a=p.parse_args()
    result=audit_price_panel(Path(a.data_root),warmup_hours=a.warmup_hours)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result['manifest'],indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'mode':result['manifest']['mode'],
                      'rows_per_asset':result['manifest']['expected_rows'],
                      'panel_sha256':result['manifest']['panel_sha256']}))

if __name__=='__main__':main()
