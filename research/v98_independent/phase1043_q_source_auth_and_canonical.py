#!/usr/bin/env python3
"""V98 Independent Q authenticated SOURCE-ONLY five-target canonicalization.

Fresh official Clean-4 2022-2024 OHLC + native funding/mark receipts.
No historical economic ledger, future validation, old holdout or benchmarks.
"""
from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase1042_q_signed_sevenslot_source import compose_q,PATHS

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'phase1043_q_source_only_receipt.json'
POLICY_PASS='PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY'


def canonicalize(frame):
    x=frame.to_numpy(float)
    if not np.isfinite(x).all() or x.shape[1]!=4:
        raise ValueError('Q_CANONICAL_INVALID')
    if np.max(np.abs(x))>.55+1e-10 or np.max(np.abs(x).sum(axis=1))>1.40+1e-10 or np.max(np.abs(x.sum(axis=1)))>.65+1e-10:
        raise ValueError('Q_SIGNED_CAP_BREACH')
    x=np.round(x,8)
    x[np.abs(x)<0.5e-8]=0.
    out=pd.DataFrame(x,index=frame.index,columns=frame.columns)
    raw=out.to_csv(float_format='%.8f').encode('utf-8')
    return out,hashlib.sha256(raw).hexdigest()


def fresh_source():
    from phase803_training_ohlc_official_replay import run as fresh_ohlc
    from phase1000_four_asset_source_policy import run as fresh_policy, OUT as POLICY_OUT, BOUNDS, MONTH_PINS
    from phase866_k_sevenslot_source import ASSETS,PINS
    from phase877_k_official_economic_dispatch import PASS_OHLC
    o=fresh_ohlc()
    if o.get('decision')!=PASS_OHLC or o.get('vendor_origin_attested') is not True:
        raise PermissionError('Q_OFFICIAL_OHLC_ATTESTATION_FAILED')
    for a in ASSETS:
        v=o.get('assets',{}).get(a,{})
        if v.get('sha256')!=PINS[a] or v.get('hours')!=18288 or v.get('monthly_archives')!=25:
            raise PermissionError('Q_OHLC_PIN_'+a)
    if fresh_policy()!=0:raise PermissionError('Q_MARK_FUNDING_ATTESTATION_FAILED')
    p=json.loads(POLICY_OUT.read_text())
    required={'decision':POLICY_PASS,'verified_mark_monthly_archives':100,
              'verified_mark_daily_archives':112,'verified_funding_monthly_archives':100,
              'verified_asset_events':9144,'vendor_archive_checksum_attested':True,
              'historical_pnl_computed':False,'economic_clearance':False,
              'validation_2025_read':False,'holdout_accessed':False,
              'external_benchmarks_used':False,'api_mark_attested':False}
    for k,v in required.items():
        if type(p.get(k)) is not type(v) or p[k]!=v:
            raise PermissionError('Q_POLICY_DRIFT_'+k)
    if hashlib.sha256(BOUNDS.read_bytes()).hexdigest()!=p.get('bounds_csv_sha256'):
        raise PermissionError('Q_FUNDING_BOUNDS_DIGEST')
    manifests=p.get('exception_manifests',{})
    if set(manifests)!=set(ASSETS):raise PermissionError('Q_MISSING_FEB_PROVENANCE')
    for a in ASSETS:
        m=manifests[a];ov=m.get('overlap',{})
        if (m.get('monthly_zip_sha256')!=MONTH_PINS[a] or len(m.get('daily_zip_sha256',{}))!=28 or
            m.get('monthly_rows')!=648 or m.get('daily_rows')!=672 or m.get('inserted_daily_rows')!=24 or
            ov.get('shared')!=648 or ov.get('missing_left')!=24 or ov.get('missing_right')!=0 or ov.get('different_rows')!=0):
            raise PermissionError('Q_FEB_SOURCE_CONFLICT_'+a)
    return {'ohlc':o['decision'],'funding_mark':p['decision'],'funding_bounds_sha256':p['bounds_csv_sha256']}


def run():
    receipt={'phase':1043,'decision':'BLOCKED_BEFORE_Q_TARGETS','historical_pnl_computed':False,
             'validation_2025_read':False,'holdout_accessed':False,'external_benchmarks_used':False,
             'economic_clearance':False,'ledger_invocations':0}
    try:
        from phase866_k_sevenslot_source import ASSETS,START,END
        from phase877_k_official_economic_dispatch import load_source_arrays
        receipt['official_source']=fresh_source()
        # Reuse strictly source transport, NEVER prior V98 alpha or ledger logic.
        from phase1000_four_asset_source_policy import BOUNDS
        with tempfile.TemporaryDirectory(prefix='v98_q_source_') as tmp:
            sandbox=Path(tmp)
            (sandbox/'phase243_clean4_canonical').symlink_to((ROOT/'phase243_clean4_canonical').resolve(),target_is_directory=True)
            (sandbox/'phase797_conservative_training_funding_bounds.csv').symlink_to(BOUNDS.resolve())
            source,rate,mark,event,years=load_source_arrays(sandbox)
        if len(years)!=18288 or not np.isin(years,(2022,2023,2024)).all() or int(event.sum())!=9144:
            raise PermissionError('Q_TRAINING_NATIVE_FUNDING_GEOMETRY')
        idx=pd.date_range(START,END,freq='h')
        if len(idx)!=18288:raise ValueError('Q_TRAINING_CALENDAR')
        frames=[pd.DataFrame(source[k],index=idx,columns=ASSETS) for k in ('open','high','low','close','quote_volume')]
        frames.append(pd.DataFrame(rate,index=idx,columns=ASSETS))
        paths,diag=compose_q(*frames,diagnostics=True)
        if tuple(paths)!=PATHS:raise ValueError('Q_FIVE_PATHS_INCOMPLETE')
        hashes={}
        for name,frame in paths.items():
            _,hashes[name]=canonicalize(frame)
        receipt.update({'decision':'PASS_Q_SOURCE_ONLY_NOT_ECONOMICALLY_APPROVED',
                        'canonical_sha256':hashes,'diagnostics':diag,
                        'code_blob_sha1':{},'official_ohlc_hours':len(idx)})
        for name in ('phase1040_q_signed_margin_oracle.py','phase1042_q_signed_sevenslot_source.py',
                     'phase1043_q_source_auth_and_canonical.py'):
            raw=(ROOT/name).read_bytes()
            receipt['code_blob_sha1'][name]=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()
    except Exception as e:
        receipt['reason']=type(e).__name__+': '+str(e)[:300]
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:receipt.get(k) for k in ('phase','decision','reason','canonical_sha256')},sort_keys=True))
    return 0 if receipt['decision'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(run())
