#!/usr/bin/env python3
"""V98 Independent K: SAME-RUN authenticated official 90-cell training gate.

Source failure is BLOCKED_BEFORE_PNL, never silently uses cached evidence.
2022-12 warmup, 2023/2024 training, no 2025+, XRP, Phase083 or benchmarks.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from phase866_k_sevenslot_source import ASSETS, PATHS, PINS, START, END, pinned_training_frames, compose_k
from phase876_k_funded_ledger import complete_matrix, growth_gate

ROOT=Path(__file__).resolve().parent
FROZEN={
 'K_core_only':'237fe4b099c88c9c5bc2302e1f08d11e035b70daa150db2d8d8f6c0cb99a51ce',
 'K_full':'2babec819c91a54cf2e3914724a63c2ae7ef5e289b4c173163c59daf9bd9a3a0',
 'K_minus_opportunity':'017ce48025d13409d63aa0ebec22d58a5c72d86a59594f9ee04a24502c10fe57',
 'K_minus_relative_value':'33b22a479d02e18da869f9c488e14a80093a2f4a384c368dcf82a4d336f26a38',
 'K_minus_recovery':'52722988fc8bf7d7a815570b6e39f97868e969d6cff4f4a800dd9de88c65e2d2'}
PASS_OHLC='PASS_PHASE803_100_OFFICIAL_KLINE_ARCHIVES_TRAINING_ONLY'
PASS_MARK='PASS_OFFICIAL_100_MARK_ARCHIVES_9144_CONSERVATIVE_BOUNDS_SOURCE_ONLY'


def require_fresh_sources(root=ROOT,ohlc_run=None,mark_run=None):
    """Network calls MUST be executed in this function invocation, no cached-pass bypass."""
    root=Path(root)
    if ohlc_run is None:
        from phase803_training_ohlc_official_replay import run as ohlc_run
    if mark_run is None:
        from phase797_official_mark_archive_attestor import run as mark_run
    # Actual downloads are required even if source files are already present.
    o=ohlc_run()
    if not isinstance(o,dict) or o.get('decision')!=PASS_OHLC or o.get('vendor_origin_attested') is not True:
        raise PermissionError('fresh official 100 OHLC ZIP+CHECKSUM source gate failed')
    m_status=mark_run()
    if m_status!=0:raise PermissionError('fresh official 100 funding + 100 mark ZIP source gate failed')
    m=json.loads((root/'phase797_official_mark_archive_receipt.json').read_text())
    required={'decision':PASS_MARK,'vendor_origin_attested':True,
              'verified_funding_monthly_archives':100,'verified_mark_monthly_archives':100,
              'verified_asset_events':9144,'historical_pnl_computed':False,
              'validation_2025_read':False,'holdout_accessed':False,
              'external_benchmarks_used':False}
    for k,v in required.items():
        if type(m.get(k))!=type(v) or m.get(k)!=v:
            raise PermissionError('official mark receipt failed: '+k)
    raw=(root/'phase797_conservative_training_funding_bounds.csv').read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if m.get('conservative_bounds_csv_sha256')!=sha:
        raise PermissionError('official mark CSV digest mismatch')
    for asset in ASSETS:
        item=o.get('assets',{}).get(asset,{})
        if item.get('sha256')!=PINS[asset] or item.get('monthly_archives')!=25 or item.get('hours')!=18288:
            raise PermissionError('official OHLC receipt incomplete '+asset)
    return {'ohlc':o,'mark':m,'bounds_csv_sha256':sha}


def load_source_arrays(root=ROOT):
    """Parse exact authenticated pre-2025 event calendar, no other assets."""
    root=Path(root)
    close,high=pinned_training_frames(root/'phase243_clean4_canonical')
    idx=close.index
    if idx[0]!=START or idx[-1]!=END or len(idx)!=18288:
        raise ValueError('training index changed')
    arrays={}
    for col in ('open','high','low','close','quote_volume'):
        arrays[col]=np.stack([pd.read_csv(root/'phase243_clean4_canonical'/f'{a}_1h.csv',usecols=[col])[col].to_numpy(float)
                              for a in ASSETS],axis=1)
    if not np.array_equal(arrays['close'],close.to_numpy(float)) or not np.array_equal(arrays['high'],high.to_numpy(float)):
        raise ValueError('source close/high re-read mismatch')
    event=np.zeros((len(idx),4),bool)
    rate=np.zeros((len(idx),4),float)
    mark=np.full((len(idx),4),np.nan)
    counts={a:0 for a in ASSETS}
    first=int(START.timestamp()*1000);last=int(END.timestamp()*1000)
    with (root/'phase797_conservative_training_funding_bounds.csv').open(newline='') as stream:
        reader=csv.DictReader(stream)
        if tuple(reader.fieldnames or ())!=('asset','funding_slot_ms','funding_time_ms','funding_rate',
                                           'mark_low','mark_high','conservative_mark'):
            raise ValueError('authenticated mark schema mismatch')
        for row in reader:
            a=row['asset']
            if a not in counts:raise ValueError('non Clean-4 mark source')
            j=ASSETS.index(a)
            slot=int(row['funding_slot_ms']);ts=int(row['funding_time_ms'])
            if not first<=slot<=last or (slot-first)%28_800_000 or not slot<=ts<=slot+29:
                raise ValueError('mark settlement calendar mismatch')
            t=(slot-first)//3_600_000
            if event[t,j]:raise ValueError('duplicate mark settlement')
            r=float(row['funding_rate']);lo=float(row['mark_low']);hi=float(row['mark_high']);m=float(row['conservative_mark'])
            if not all(map(math.isfinite,(r,lo,hi,m))) or lo<=0 or hi<lo or m!=(hi if r>=0 else lo):
                raise ValueError('mark conservative sign mismatch')
            event[t,j]=True;rate[t,j]=r;mark[t,j]=m;counts[a]+=1
    if counts!={a:2286 for a in ASSETS} or event.sum()!=9144:
        raise ValueError('incomplete authenticated mark event calendar')
    return arrays,rate,mark,event,idx.year.to_numpy()


def run():
    result={'phase':877,'decision':'BLOCKED_BEFORE_PNL','historical_pnl_computed':False,
            'vendor_origin_attested_this_run':False,'validation_2025_read':False,
            'holdout_accessed':False,'external_benchmarks_used':False,
            'promotion_eligible':False,'ledger_invocations':0}
    try:
        receipts=require_fresh_sources()
        result['vendor_origin_attested_this_run']=True
        source,rate,mark,event,years=load_source_arrays()
        close,high=pinned_training_frames(ROOT/'phase243_clean4_canonical')
        targets=compose_k(close,high)
        if tuple(targets)!=PATHS or tuple(FROZEN)!=PATHS:
            raise ValueError('K frozen five-path mismatch')
        for name,frame in targets.items():
            digest=hashlib.sha256(frame.to_csv(float_format='%.12g').encode()).hexdigest()
            if digest!=FROZEN[name]:raise ValueError('K target hash drift: '+name)
        result['source_receipts']={'ohlc':receipts['ohlc']['decision'],
                                   'mark':receipts['mark']['decision'],
                                   'funding_mark_sha256':receipts['bounds_csv_sha256']}
        # Only now may historical PnL be calculated. Every cell attempted.
        result['historical_pnl_computed']=True
        matrix=complete_matrix({k:v.to_numpy(float) for k,v in targets.items()},
                               {k:source[k] for k in ('open','high','low','close')},
                               source['quote_volume'],rate,mark,event,years)
        result['ledger_invocations']=matrix['cells_attempted']
        result['matrix']=matrix
        gate=growth_gate(matrix)
        result['growth_gate']=gate
        result['decision']=('PASS_K_TRAINING_ONLY_PENDING_SEPARATE_VALIDATION' if gate['passed']
                            else 'REJECT_K_TRAINING_NO_RESCUE')
    except Exception as exc:
        result['decision']='BLOCKED_AFTER_PNL_NO_PROMOTION' if result['historical_pnl_computed'] else 'BLOCKED_BEFORE_PNL'
        result['reason']=type(exc).__name__+': '+str(exc)[:350]
    (ROOT/'phase877_k_official_economic_result.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result.get(k) for k in ('decision','reason','ledger_invocations','historical_pnl_computed')},sort_keys=True))
    return result

if __name__=='__main__':
    r=run()
    raise SystemExit(0 if r['decision'].startswith('PASS_') else 2)
