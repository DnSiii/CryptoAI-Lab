#!/usr/bin/env python3
"""Self-contained authenticated V98 Clean-4 TRAINING source reader; never loads 2025+."""
from __future__ import annotations
from pathlib import Path
import csv, hashlib, json
import numpy as np
import pandas as pd
ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
HOURS=18288
WARMUP=744
START=pd.Timestamp('2022-12-01 00:00:00+00:00')
END=pd.Timestamp('2024-12-31 23:00:00+00:00')
FUNDING_SHA='f706812b7989666c3efd0b24045a5c31f4d9c79b46d61da7b5e6cde6c6e73f5e'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(root):
    root=Path(root)
    manifest=json.loads((root/'phase803_official_training_ohlc_receipt.json').read_text())
    policy=json.loads((root/'phase1000_four_asset_source_policy_receipt.json').read_text())
    if manifest.get('decision')!='PASS_PHASE803_100_OFFICIAL_KLINE_ARCHIVES_TRAINING_ONLY':
        raise ValueError('V98_BAD_OHLC_MANIFEST')
    if policy.get('bounds_csv_sha256')!=FUNDING_SHA:
        raise ValueError('V98_BAD_FUNDING_MANIFEST')
    fields=[];time=None
    for a in ASSETS:
        path=root/(a+'_1h.csv')
        if sha(path)!=manifest['assets'][a]['sha256']:
            raise ValueError('V98_OHLC_SHA_MISMATCH_'+a)
        frame=pd.read_csv(path)
        ts=pd.to_datetime(frame['open_time'],utc=True)
        if len(ts)!=HOURS or ts.iloc[0]!=START or ts.iloc[-1]!=END or not np.all(np.diff(ts.view('i8'))==3600*10**9):
            raise ValueError('V98_TIME_INTEGRITY_'+a)
        if time is not None and not ts.equals(time):raise ValueError('V98_ASSET_TIME_MISMATCH')
        time=ts
        x=frame[['open','high','low','close','quote_volume']].to_numpy(float)
        if not np.isfinite(x).all() or np.any(x[:,:4]<=0) or np.any(x[:,2]>np.minimum(x[:,0],x[:,3])) or np.any(x[:,1]<np.maximum(x[:,0],x[:,3])) or np.any(x[:,4]<0):
            raise ValueError('V98_OHLC_INVALID_'+a)
        fields.append(x)
    data=np.stack(fields,axis=1)
    bound=root/'phase1000_four_asset_conservative_bounds_source_only.csv'
    if sha(bound)!=FUNDING_SHA:raise ValueError('V98_NATIVE_FUNDING_SHA_MISMATCH')
    rate=np.zeros((HOURS,4));mark=np.full((HOURS,4),np.nan);event=np.zeros((HOURS,4),bool)
    counts={a:0 for a in ASSETS}
    with bound.open() as f:
        for row in csv.DictReader(f):
            a=row['asset'];j=ASSETS.index(a)
            ms=int(row['funding_slot_ms']);ts=pd.Timestamp(ms,unit='ms',tz='UTC')
            if ts<START or ts>END or ts.minute or ts.second:raise ValueError('V98_FUNDING_OUT_OF_RANGE')
            t=int((ts-START).total_seconds()//3600)
            if t%8!=0 or event[t,j]:raise ValueError('V98_FUNDING_DUPLICATE_OR_OFFSLOT')
            r=float(row['funding_rate']);m=float(row['conservative_mark'])
            if not np.isfinite(r) or not np.isfinite(m) or m<=0:raise ValueError('V98_FUNDING_INVALID')
            rate[t,j]=r;mark[t,j]=m;event[t,j]=True;counts[a]+=1
    if any(v!=2286 for v in counts.values()) or event.sum()!=9144:raise ValueError('V98_FUNDING_EVENT_COUNT')
    return {'o':data[:,:,0],'h':data[:,:,1],'l':data[:,:,2],'c':data[:,:,3],
            'q':data[:,:,4],'rate':rate,'mark':mark,'event':event,'time':time,
            'manifest_sha':{a:manifest['assets'][a]['sha256'] for a in ASSETS},
            'funding_sha':FUNDING_SHA}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args()
    x=load(a.root)
    print('V98_CLEAN4_AUTHENTICATED',len(x['time']),int(x['event'].sum()),
          'zero_quote_hours',np.flatnonzero(np.any(x['q']==0,axis=1)).tolist())
