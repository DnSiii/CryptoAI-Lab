#!/usr/bin/env python3
"""V98 AE authenticated Clean-4 static source attestation; no system PnL."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from phase1205_ae_breakout_source import ASSETS,START,ae_breakout_source,source_digest
from phase803_training_ohlc_official_replay import run as vendor_ohlc, PASS as OHLC_PASS, PINS
from phase1000_four_asset_source_policy import run as vendor_native, OUT as NATIVE_RECEIPT, BOUNDS

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'phase1212_ae_official_source_receipt.json'
FIELDS=('asset','funding_slot_ms','funding_time_ms','funding_rate',
        'mark_low','mark_high','conservative_mark')
PATHS=('AE_core_only','AE_full','AE_minus_opportunity',
       'AE_minus_relative_value','AE_minus_stress')
MODES=('immediate','capacity_1m','capacity_10m')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def official_frames():
    idx=pd.date_range(START,periods=18288,freq='h')
    assets={}
    for asset in ASSETS:
        path=ROOT/'phase243_clean4_canonical'/(asset+'_1h.csv')
        digest,size=PINS[asset]
        if path.stat().st_size!=size or sha256(path)!=digest:
            raise PermissionError('AE1212_OHLC_PIN_'+asset)
        frame=pd.read_csv(path)
        if (len(frame)!=len(idx) or tuple(frame.columns)!=
                ('open_time','open','high','low','close','volume','quote_volume')):
            raise ValueError('AE1212_OHLC_SCHEMA_'+asset)
        if not pd.DatetimeIndex(pd.to_datetime(frame['open_time'],utc=True)).equals(idx):
            raise ValueError('AE1212_OHLC_CHRONOLOGY_'+asset)
        assets[asset]=frame
    data={name:pd.DataFrame({asset:assets[asset][name].to_numpy(float)
                             for asset in ASSETS},index=idx)
          for name in ('open','high','low','close','quote_volume')}
    return idx,data


def parse_native(index,path,strict=True):
    n=len(index)
    rate=np.zeros((n,4))
    event=np.zeros((n,4))
    mark_low=np.full((n,4),np.nan)
    mark_high=np.full((n,4),np.nan)
    first=int(index[0].timestamp()*1000)
    with Path(path).open(newline='') as stream:
        reader=csv.DictReader(stream)
        if tuple(reader.fieldnames or ())!=FIELDS:
            raise ValueError('AE1212_NATIVE_SCHEMA')
        for row in reader:
            asset=row['asset']
            if asset not in ASSETS:
                raise ValueError('AE1212_NON_CLEAN4')
            j=ASSETS.index(asset)
            slot=int(row['funding_slot_ms'])
            timestamp=int(row['funding_time_ms'])
            if (slot<first or slot>int(index[-1].timestamp()*1000) or
                    (slot-first)%28_800_000 or not slot<=timestamp<=slot+29):
                raise ValueError('AE1212_NATIVE_CLOCK')
            t=(slot-first)//3_600_000
            if event[t,j]:
                raise ValueError('AE1212_DUPLICATE_NATIVE_EVENT')
            f,lo,hi,mark=map(float,(row['funding_rate'],row['mark_low'],
                                    row['mark_high'],row['conservative_mark']))
            if (not np.isfinite([f,lo,hi,mark]).all() or lo<=0 or hi<lo or
                    mark!=(hi if f>=0 else lo)):
                raise ValueError('AE1212_NATIVE_SIGNED_MARK')
            rate[t,j]=f
            event[t,j]=1
            mark_low[t,j]=lo
            mark_high[t,j]=hi
    if strict and (n!=18288 or int(event.sum())!=9144 or
                   any(int(event[:,j].sum())!=2286 for j in range(4))):
        raise ValueError('AE1212_NATIVE_COVERAGE')
    return (pd.DataFrame(rate,index=index,columns=ASSETS),
            pd.DataFrame(event,index=index,columns=ASSETS),
            mark_low,mark_high)


def static_hash(index,outputs,path,mode):
    if path not in PATHS or mode not in MODES:
        raise ValueError('AE1212_PATH_MODE')
    core,op,rv,router=outputs
    n=len(index)
    if any(x.shape!=(n,4 if k<3 else 3) for k,x in enumerate(outputs)):
        raise ValueError('AE1212_SOURCE_SHAPE')
    o=op.copy()
    v=rv.copy()
    if path in ('AE_core_only','AE_minus_opportunity'):o[:]=0
    if path in ('AE_core_only','AE_minus_relative_value'):v[:]=0
    payload=np.column_stack((core,o,v,router))
    if not np.isfinite(payload).all():
        raise ValueError('AE1212_NONFINITE_SOURCE')
    quant=np.rint(payload*1_000_000).astype('<i8')
    header=('AE1212_STATIC_SOURCE_V1|'+path+'|'+mode+'|'+str(n)+'|'+
            ','.join(ASSETS)+'\n').encode('ascii')
    return hashlib.sha256(header+
        index.tz_convert('UTC').asi8.astype('<i8').tobytes()+
        quant.tobytes()).hexdigest()


def run():
    receipt={'phase':1212,'decision':'BLOCKED_BEFORE_AE_SYSTEM_PNL',
             'source_only':True,'historical_system_pnl_computed':False,
             'validation_2025_read':False,'external_benchmarks_used':False,
             'promotion_eligible':False,'nav_feedback_hashed':False}
    try:
        v=vendor_ohlc()
        if (v.get('decision')!=OHLC_PASS or v.get('vendor_origin_attested') is not True or
                any(v.get('assets',{}).get(a,{}).get('sha256')!=PINS[a][0]
                    for a in ASSETS)):
            raise PermissionError('AE1212_VENDOR_OHLC')
        if vendor_native()!=0:
            raise PermissionError('AE1212_VENDOR_NATIVE')
        native=json.loads(NATIVE_RECEIPT.read_text())
        if (native.get('decision')!='PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY'
                or native.get('vendor_archive_checksum_attested') is not True or
                native.get('verified_asset_events')!=9144 or
                native.get('validation_2025_read') is not False or
                native.get('bounds_csv_sha256')!=sha256(BOUNDS)):
            raise PermissionError('AE1212_NATIVE_PROVENANCE')
        idx,data=official_frames()
        funding,event,mark_low,mark_high=parse_native(idx,BOUNDS)
        frames=(data['open'],data['high'],data['low'],data['close'],
                data['quote_volume'],funding,event)
        outputs=ae_breakout_source(*frames)
        hashes={path+'__'+mode:static_hash(idx,outputs,path,mode)
                for path in PATHS for mode in MODES}
        if len(hashes)!=15 or len(set(hashes.values()))!=15:
            raise ValueError('AE1212_HASH_GEOMETRY')
        receipt.update({'decision':'PASS_AE_15_STATIC_SOURCE_HASHES_NOT_FULL_FREEZE',
            'official_hours':len(idx),'native_funding_events':int(event.to_numpy().sum()),
            'native_bounds_sha256':sha256(BOUNDS),
            'source_digest':source_digest(idx,outputs),
            'static_hashes':dict(sorted(hashes.items())),
            'growth_active_hours':int(np.any(outputs[0]!=0,axis=1).sum()),
            'opportunity_active_hours':int(np.any(outputs[1]!=0,axis=1).sum()),
            'relative_value_active_hours':int(np.any(outputs[2]!=0,axis=1).sum())})
    except Exception as exc:
        receipt['reason']=type(exc).__name__+': '+str(exc)[:350]
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:receipt.get(k) for k in ('decision','reason','official_hours',
          'native_funding_events','source_digest')},sort_keys=True))
    return 0 if receipt['decision'].startswith('PASS_') else 2


if __name__=='__main__':
    raise SystemExit(run())
