#!/usr/bin/env python3
"""V98 NO sealed 2025-only validation reader using independently authenticated source-only artifact, strict official provenance.
2022-24 is loaded ONLY as causal history; no 2023-24 PnL recomputed for validation.
"""
from pathlib import Path
import csv,hashlib,json
import numpy as np
from v98_clean4_training_reader import load as load_training,HOURS as TRAIN_HOURS
ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
HOURS_2025=8760;TOTAL=TRAIN_HOURS+HOURS_2025
START_2025_MS=1735689600000
STEP=3600000
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(training_root,validation_root):
    old=load_training(training_root)
    root=Path(validation_root)
    receipt=json.loads((root/'nh_2025_official_source_receipt.json').read_text())
    if receipt.get('decision')!='PASS_NH_2025_OFFICIAL_SOURCE_ONLY_NOT_VALIDATION' or receipt.get('official_archives_verified')!=144 or receipt.get('funding_events_verified')!=4380:
        raise ValueError('NO_2025_OFFICIAL_PROVENANCE_NOT_APPROVED')
    if receipt.get('frozen_training_commit')!='a9a2454282c2f97d92a1a58cbcfe305945306ab4':
        raise ValueError('NO_2025_SOURCE_ARTIFACT_ORIGIN_METADATA_MISMATCH')
    vals={k:[] for k in ('o','h','l','c','q','rate','event','lo','hi')}
    expected=np.arange(START_2025_MS,START_2025_MS+HOURS_2025*STEP,STEP,dtype=np.int64)
    for asset in ASSETS:
        meta=receipt['assets'][asset]
        a=root/(asset+'_1h_2025.csv');b=root/(asset+'_funding_2025.csv')
        if sha(a)!=meta['ohlc_csv_sha256'] or sha(b)!=meta['funding_envelope_csv_sha256']:
            raise ValueError('NO_2025_CANONICAL_CSV_SHA_'+asset)
        with a.open(newline='') as f:rows=list(csv.DictReader(f))
        if len(rows)!=HOURS_2025 or not np.array_equal(np.array([int(x['open_time_ms']) for x in rows],np.int64),expected):
            raise ValueError('NO_2025_HOURLY_CALENDAR_'+asset)
        x=np.array([[float(row[k]) for k in ('open','high','low','close','quote_volume')] for row in rows])
        if not np.isfinite(x).all() or np.any(x[:,:4]<=0) or np.any(x[:,4]<0) or np.any(x[:,2]>np.minimum(x[:,0],x[:,3])) or np.any(x[:,1]<np.maximum(x[:,0],x[:,3])):
            raise ValueError('NO_2025_HOURLY_GEOMETRY_'+asset)
        for i,k in enumerate(('o','h','l','c','q')):vals[k].append(x[:,i])
        rate=np.zeros(HOURS_2025);event=np.zeros(HOURS_2025,bool)
        lo=np.zeros(HOURS_2025);hi=np.zeros(HOURS_2025)
        with b.open(newline='') as f:fr=list(csv.DictReader(f))
        if len(fr)!=1095:raise ValueError('NO_2025_FUNDING_COUNT_'+asset)
        for i,row in enumerate(fr):
            t=i*8;ms=int(row['funding_slot_ms'])
            if ms!=int(expected[t]) or abs(int(row['exchange_offset_ms']))>60000:
                raise ValueError('NO_2025_FUNDING_CALENDAR_'+asset)
            r=float(row['funding_rate']);low=float(row['mark_lower_bound']);high=float(row['mark_upper_bound'])
            if not np.isfinite([r,low,high]).all() or low<=0 or low>high:
                raise ValueError('NO_2025_FUNDING_MARK_'+asset)
            rate[t]=r;lo[t]=low;hi[t]=high;event[t]=True
        vals['rate'].append(rate);vals['event'].append(event)
        vals['lo'].append(lo);vals['hi'].append(hi)
    d={}
    for k in ('o','h','l','c','q','rate','event'):
        new=np.stack(vals[k],axis=1)
        d[k]=np.concatenate((old[k],new),axis=0)
        if d[k].shape!=(TOTAL,4):raise ValueError('NO_2025_EXTENDED_SHAPE')
    d['lo']=np.stack(vals['lo'],axis=1);d['hi']=np.stack(vals['hi'],axis=1)
    if d['lo'].shape!=(HOURS_2025,4) or d['hi'].shape!=(HOURS_2025,4):
        raise ValueError('NO_2025_ENVELOPE_SHAPE')
    if int(d['event'][TRAIN_HOURS:].sum())!=4380 or int(d['event'][:TRAIN_HOURS].sum())!=9144:
        raise ValueError('NO_2025_EVENT_ISOLATION')
    d['source_receipt']=receipt
    d['2025_validation_only']=True
    d['holdout_accessed']=False
    return d
