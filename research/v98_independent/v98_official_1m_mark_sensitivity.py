#!/usr/bin/env python3
"""V98 Independent 1m SOURCE SENSITIVITY ONLY; never substitute for exact funding tick.
Primary conservative gate stays the separately pinned official 1h worst-side envelope.
"""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import ASSETS,START,HOURS,load
from v98_mark_envelope_settlement import read_envelope,worst_funding
EXPECTED_ONE_MINUTE_SHA='bfb9cc181a326acd49d5ee5b8a620da1f36a6ef0400f132ecd6a9165bebf355a'
SCHEMA=('symbol','funding_time_ms','one_minute_lower','one_minute_upper',
        'original_conservative_mark','one_hour_lower','one_hour_upper')

def read_sensitivity(path,d,old_envelope_path):
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual!=EXPECTED_ONE_MINUTE_SHA:
        raise ValueError('V98_1M_UNPINNED_SOURCE_SHA')
    oldlo,oldhi,oldsha=read_envelope(old_envelope_path,d)
    lo=oldlo.copy();hi=oldhi.copy()
    seen=np.zeros((HOURS,4),bool);start=int(START.timestamp()*1000)
    with Path(path).open(newline='') as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames or ())!=SCHEMA:
            raise ValueError('V98_1M_SOURCE_SCHEMA')
        for row in reader:
            if row['symbol'] not in ASSETS:raise ValueError('V98_1M_UNKNOWN_SYMBOL')
            j=ASSETS.index(row['symbol']);ms=int(row['funding_time_ms']);delta=ms-start
            if delta%3600000:raise ValueError('V98_1M_BAD_TIME')
            t=delta//3600000
            if not 0<=t<HOURS or not d['event'][t,j] or seen[t,j]:
                raise ValueError('V98_1M_BAD_CALENDAR_OR_DUPLICATE')
            a=float(row['one_minute_lower']);b=float(row['one_minute_upper'])
            orig=float(row['original_conservative_mark'])
            olda=float(row['one_hour_lower']);oldb=float(row['one_hour_upper'])
            if not np.isfinite((a,b,orig,olda,oldb)).all() or a<=0 or a>b:
                raise ValueError('V98_1M_INVALID_INTERVAL')
            if abs(orig-d['mark'][t,j])>1e-8 or abs(olda-oldlo[t,j])>1e-8 or abs(oldb-oldhi[t,j])>1e-8:
                raise ValueError('V98_1M_PINNED_ORIGINAL_CONFLICT')
            if a<oldlo[t,j]-1e-7 or b>oldhi[t,j]+1e-7:
                raise ValueError('V98_1M_NOT_NESTED')
            lo[t,j]=a;hi[t,j]=b;seen[t,j]=True
    if not np.array_equal(seen,d['event']) or int(seen.sum())!=9144:
        raise ValueError('V98_1M_MISSING_NATIVE_EVENTS')
    return lo,hi,{'source_sha256':actual,'old_envelope_sha256':oldsha,
                  'events':int(seen.sum()),'exact_native_tick_mark_attested':False,
                  'use':'SENSITIVITY_ONLY_NOT_PRIMARY_EXACT_TICK_GATE'}

def verify(d,lo,hi,oldlo,oldhi):
    checked=0;worst_gap=0.
    for t in np.flatnonzero(d['event'][:,0]):
        r=d['rate'][t];event=d['event'][t]
        for sign in (-1.,1.):
            old=np.full(4,sign)
            new=-old
            for order in ('carried_before_fill','new_after_fill'):
                conservative=worst_funding(old,new,r,event,oldlo[t],oldhi[t],order)
                sensitivity=worst_funding(old,new,r,event,lo[t],hi[t],order)
                if sensitivity<conservative-1e-8:
                    raise ValueError('V98_1M_SENSITIVITY_CASH_NOT_NESTED')
                worst_gap=max(worst_gap,sensitivity-conservative);checked+=1
    return {'signed_four_asset_settlement_cases':checked,
            'max_sensitivity_vs_primary_cash_gap_per_unit_contract':worst_gap,
            'pnl_computed':False,'exact_native_tick_attested':False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True);p.add_argument('--envelope-csv',required=True)
    p.add_argument('--minute-csv',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    d=load(a.root);lo,hi,src=read_sensitivity(a.minute_csv,d,a.envelope_csv)
    oldlo,oldhi,_=read_envelope(a.envelope_csv,d)
    result=verify(d,lo,hi,oldlo,oldhi)
    result.update(src)
    result.update({'decision':'PASS_PINNED_ONE_MINUTE_FUNDING_SENSITIVITY_NOT_EXACT_TICK',
        'training_only':True,'holdout_read':False,'no_engine_promotion':True,
        'primary_worst_side_one_hour_envelope_preserved':True})
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('V98_1M_SENSITIVITY_ADAPTER',json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
