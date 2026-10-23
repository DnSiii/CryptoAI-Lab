#!/usr/bin/env python3
"""V98 AJ1260 official Clean-4 historical source-only causal digests; NO PnL."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from phase803_training_ohlc_official_replay import ASSETS,PINS
from phase1255_aj_signed_sources import source_bundle

ROOT=Path(__file__).resolve().parent
HOURS=18288
START=pd.Timestamp('2022-12-01T00:00:00Z')
PATHS=('AJ_core_only','AJ_full','AJ_minus_opportunity',
       'AJ_minus_RV','AJ_minus_stress')
CAPITAL=('immediate','capacity_1m','capacity_10m')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def load_official(root=ROOT):
    root=Path(root)
    with open(root/'phase803_official_training_ohlc_receipt.json') as f:
        ohlc_receipt=json.load(f)
    with open(root/'phase1000_four_asset_source_policy_receipt.json') as f:
        native_receipt=json.load(f)
    if (ohlc_receipt.get('decision') !=
        'PASS_PHASE803_100_OFFICIAL_KLINE_ARCHIVES_TRAINING_ONLY' or
        not native_receipt.get('decision','').startswith(
            'PASS_100_MARK_100_FUNDING_')):
        raise ValueError('AJ1260_OFFICIAL_PROVENANCE_NOT_PASSED')
    cols={k:[] for k in ('open','high','low','close','quote_volume')}
    expected=pd.date_range(START,periods=HOURS,freq='h',tz='UTC')
    expected_ms=(expected.asi8//1000000).astype(np.int64)
    for asset in ASSETS:
        path=root/'phase243_clean4_canonical'/(asset+'_1h.csv')
        raw=path.read_bytes()
        pin,size=PINS[asset]
        if len(raw)!=size or sha(raw)!=pin:
            raise ValueError('AJ1260_OHLC_PIN_'+asset)
        df=pd.read_csv(path)
        if len(df)!=HOURS:
            raise ValueError('AJ1260_HOURS_'+asset)
        ts=pd.to_datetime(df['open_time'],utc=True)
        if not ts.equals(pd.Series(expected)):
            raise ValueError('AJ1260_UTC_CALENDAR_'+asset)
        for key in cols:
            a=pd.to_numeric(df[key],errors='raise').to_numpy(dtype=float)
            if not np.isfinite(a).all():
                raise ValueError('AJ1260_NONFINITE_'+key)
            cols[key].append(a)
    arrays={k:np.column_stack(v) for k,v in cols.items()}
    o,h,l,c,q=(arrays[k] for k in
        ('open','high','low','close','quote_volume'))
    if (np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0)):
        raise ValueError('AJ1260_OHLC_GEOMETRY')
    bounds_path=root/'phase1000_four_asset_conservative_bounds_source_only.csv'
    raw=bounds_path.read_bytes()
    if sha(raw)!=native_receipt['bounds_csv_sha256']:
        raise ValueError('AJ1260_NATIVE_BOUNDS_PIN')
    r=np.zeros((HOURS,4))
    e=np.zeros((HOURS,4))
    ml=c.copy()
    mh=c.copy()
    seen=set()
    index={asset:j for j,asset in enumerate(ASSETS)}
    start_ms=int(expected_ms[0])
    with bounds_path.open(newline='') as stream:
        reader=csv.DictReader(stream)
        required={'asset','funding_slot_ms','funding_time_ms',
                  'funding_rate','mark_low','mark_high','conservative_mark'}
        if set(reader.fieldnames or [])!=required:
            raise ValueError('AJ1260_NATIVE_SCHEMA')
        for row in reader:
            asset=row['asset']
            if asset not in index:
                raise ValueError('AJ1260_ASSET_QUARANTINE')
            slot=int(row['funding_slot_ms'])
            event_ms=int(row['funding_time_ms'])
            delta=slot-start_ms
            if (delta<0 or delta%3600000 or
                not slot<=event_ms<=slot+29):
                raise ValueError('AJ1260_NATIVE_EVENT_TIME')
            t=delta//3600000
            if t>=HOURS or t%8:
                raise ValueError('AJ1260_NATIVE_EVENT_GRID')
            j=index[asset]
            if (t,j) in seen:
                raise ValueError('AJ1260_DUPLICATE_NATIVE')
            seen.add((t,j))
            rate=float(row['funding_rate'])
            low=float(row['mark_low'])
            high=float(row['mark_high'])
            conservative=float(row['conservative_mark'])
            if (not np.isfinite([rate,low,high,conservative]).all()
                or low<=0 or high<low or
                abs(conservative-(high if rate>=0 else low))>1e-8):
                raise ValueError('AJ1260_NATIVE_MARK_BOUNDS')
            r[t,j]=rate
            e[t,j]=1.
            ml[t,j]=low
            mh[t,j]=high
    if len(seen)!=9144 or any(int(e[:,j].sum())!=2286 for j in range(4)):
        raise ValueError('AJ1260_NATIVE_EVENT_COUNT')
    for j in range(4):
        if not np.array_equal(np.flatnonzero(e[:,j]),np.arange(0,HOURS,8)):
            raise ValueError('AJ1260_NATIVE_8H_COVERAGE')
    manifests={'ohlc_pins':{a:PINS[a][0] for a in ASSETS},
        'bounds_csv_sha256':native_receipt['bounds_csv_sha256'],
        'mark_zip_manifest_sha256':native_receipt['mark_zip_manifest_sha256'],
        'funding_manifest_sha256':native_receipt['funding_manifest_sha256'],
        'calendar_sha256':sha(expected_ms.astype('<i8').tobytes())}
    return (o,h,l,c,q,r,e,ml,mh),manifests

def run(root=ROOT):
    frames,manifests=load_official(root)
    o,h,l,c,q,r,e,ml,mh=frames
    sources=source_bundle(c,h,l,r,e)
    raw_source_sha=[sha(np.asarray(x,dtype='<f8').tobytes())
                    for x in sources[:4]]
    router_sha=sha('|'.join(sources[4]['state']).encode())
    manifest_raw=json.dumps(manifests,sort_keys=True,
                            separators=(',',':')).encode()
    manifest_sha=sha(manifest_raw)
    static={}
    for path in PATHS:
        s=np.stack(sources[:4]).copy()
        if path=='AJ_core_only':
            s[1:]=0.
        elif path=='AJ_minus_opportunity':
            s[1]=0.
        elif path=='AJ_minus_RV':
            s[2]=0.
        elif path=='AJ_minus_stress':
            s[3]=0.
        weights=np.round(s,6).astype('<f8')
        weights[weights==0.]=0.
        for capital in CAPITAL:
            payload=(('V98_AJ1260|'+path+'|'+capital+'|').encode()+
                manifest_raw+router_sha.encode()+weights.tobytes())
            static[path+'|'+capital]=sha(payload)
    years={}
    for year,sl in [('2023',slice(744,9504)),
                    ('2024',slice(9504,HOURS))]:
        years[year]={
            'source_active_hours':[int(np.count_nonzero(
                np.abs(x[sl]).sum(axis=1)>1e-10)) for x in sources[:4]],
            'regimes':{state:int(np.count_nonzero(
                sources[4]['state'][sl]==state))
                for state in ('TREND','RANGE','CRISIS','REBOUND')}}
    return {'phase':1260,'architecture':'AJ','source_only':True,
        'historical_system_pnl_computed':False,
        'validation_2025_read':False,'external_benchmarks_used':False,
        'hours':HOURS,'assets':list(ASSETS),'native_events':int(e.sum()),
        'manifests':manifests,'manifest_sha256':manifest_sha,
        'raw_source_sha256':raw_source_sha,'router_sha256':router_sha,
        'static_path_capital_sha256':static,'year_activity':years,
        'decision':'PASS_AJ1260_OFFICIAL_SOURCE_ONLY_NOT_ECONOMIC'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--output',default='aj1260_source_only_receipt.json')
    args=p.parse_args()
    result=run()
    with open(args.output,'w') as f:
        json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
    print('AJ1260_SOURCE_ONLY',json.dumps(result,sort_keys=True))
