#!/usr/bin/env python3
"""V98 Independent S authenticated source-only cross-runner target/mark attestation.

No PnL, no 2025 validation, no benchmarks. Reacquires official Clean-4
OHLC/funding/mark on every invocation. Fails closed before freeze.
"""
from __future__ import annotations
import hashlib
import io
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase1069_s_sevenslot_source import (ASSETS, PATHS, ASSET_CAP, NET_CAP,
                                          GROSS_CAP, compose_s)
from phase1070_s_typed_native_mark import signed_mark_bounds

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'phase1071_s_authenticated_source_receipt.json'


def canonical_target(frame):
    x=frame.to_numpy(dtype=float)
    if x.ndim!=2 or x.shape[1]!=4 or not np.isfinite(x).all():
        raise ValueError('S_CANONICAL_NONFINITE_OR_GEOMETRY')
    if (np.abs(x).max()>ASSET_CAP+1e-10 or
        np.abs(x).sum(axis=1).max()>GROSS_CAP+1e-10 or
        np.abs(x.sum(axis=1)).max()>NET_CAP+1e-10):
        raise ValueError('S_CANONICAL_CAP_BREACH')
    if np.max(np.abs(x*1e6-np.round(x*1e6)))>1e-7:
        raise ValueError('S_CANONICAL_NONQUANTIZED')
    raw=frame.to_csv(float_format='%.6f',lineterminator='\n').encode('utf-8')
    parsed=pd.read_csv(io.BytesIO(raw),index_col=0).to_numpy(float)
    if not np.array_equal(parsed,x):raise ValueError('S_CANONICAL_SERIALIZATION_DRIFT')
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    raw=Path(path).read_bytes()
    return hashlib.sha256(raw).hexdigest()


def git_blob(path):
    raw=Path(path).read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()


def attest(arrays,rate,conservative,event,years,idx,bounds_csv,*,full=True):
    if tuple(arrays)!=('open','high','low','close','quote_volume'):
        raise ValueError('S_SOURCE_FIELDS')
    n=len(idx)
    if (any(np.asarray(v).shape!=(n,4) for v in arrays.values()) or
        np.asarray(rate).shape!=(n,4) or np.asarray(conservative).shape!=(n,4) or
        np.asarray(event).shape!=(n,4) or np.asarray(years).shape!=(n,)):
        raise ValueError('S_SOURCE_SHAPE')
    if full and (n!=18288 or idx[0]!=pd.Timestamp('2022-12-01T00:00:00Z') or
                 idx[-1]!=pd.Timestamp('2024-12-31T23:00:00Z') or
                 int(np.asarray(event).sum())!=9144):
        raise ValueError('S_OFFICIAL_CALENDAR_OR_EVENTS')
    if not np.isin(years,(2022,2023,2024)).all() or not np.array_equal(idx.year,years):
        raise ValueError('S_FUTURE_OR_YEAR_MISMATCH')
    if np.asarray(event).dtype!=bool:raise ValueError('S_EVENT_DTYPE')
    bounds=signed_mark_bounds(bounds_csv,idx,rate,event,conservative,require_full=full)
    if bounds.shape!=(n,4,2):raise ValueError('S_SIGNED_BOUNDS_GEOMETRY')
    frames=[pd.DataFrame(arrays[k],index=idx,columns=ASSETS) for k in arrays]
    frames.append(pd.DataFrame(rate,index=idx,columns=ASSETS))
    paths,diagnostics=compose_s(*frames,diagnostics=True)
    if tuple(paths)!=PATHS:raise ValueError('S_FIVE_PATHS_REQUIRED')
    hashes={k:canonical_target(paths[k]) for k in PATHS}
    if {k:canonical_target(v) for k,v in compose_s(*frames).items()}!=hashes:
        raise ValueError('S_NONDETERMINISTIC_TARGET')
    return {'canonical_sha256':hashes,'typed_mark_shape':list(bounds.shape),
            'typed_mark_csv_sha256':digest(bounds_csv),
            'native_funding_events':int(np.asarray(event).sum()),
            'official_hours':n,'diagnostics':diagnostics}


def run():
    receipt={'phase':1071,'decision':'BLOCKED_BEFORE_PNL','source_only':True,
             'historical_pnl_computed':False,'validation_2025_read':False,
             'holdout_accessed':False,'external_benchmarks_used':False,
             'promotion_eligible':False,'frozen':False}
    try:
        from phase803_training_ohlc_official_replay import run as official_ohlc
        from phase1000_four_asset_source_policy import run as official_funding, OUT as POLICY_OUT, BOUNDS
        from phase866_k_sevenslot_source import START,END,PINS
        from phase877_k_official_economic_dispatch import load_source_arrays,PASS_OHLC
        o=official_ohlc()
        if o.get('decision')!=PASS_OHLC or o.get('vendor_origin_attested') is not True:
            raise PermissionError('S_FRESH_OHLC_NOT_ATTESTED')
        for asset in ASSETS:
            item=o.get('assets',{}).get(asset,{})
            if (item.get('sha256')!=PINS[asset] or item.get('hours')!=18288 or
                item.get('monthly_archives')!=25):
                raise PermissionError('S_OFFICIAL_OHLC_PIN_'+asset)
        if official_funding()!=0:raise PermissionError('S_FRESH_MARK_FUNDING_NOT_ATTESTED')
        p=json.loads(POLICY_OUT.read_text())
        if (p.get('decision')!='PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY' or
            p.get('verified_asset_events')!=9144 or
            p.get('vendor_archive_checksum_attested') is not True or
            p.get('validation_2025_read') is not False or
            p.get('bounds_csv_sha256')!=digest(BOUNDS)):
            raise PermissionError('S_OFFICIAL_TYPED_MARK_PROVENANCE')
        with tempfile.TemporaryDirectory(prefix='v98_s_auth_') as tmp:
            sandbox=Path(tmp)
            (sandbox/'phase243_clean4_canonical').symlink_to((ROOT/'phase243_clean4_canonical').resolve(),target_is_directory=True)
            (sandbox/'phase797_conservative_training_funding_bounds.csv').symlink_to(BOUNDS.resolve())
            arrays,rate,mark,event,years=load_source_arrays(sandbox)
        idx=pd.date_range(START,END,freq='h')
        result=attest(arrays,rate,mark,event,years,idx,BOUNDS)
        receipt.update(result)
        receipt['official_source']={'ohlc':o['decision'],'funding_mark':p['decision']}
        receipt['source_code_git_blob_sha1']={name:git_blob(ROOT/name) for name in
            ('phase1069_s_sevenslot_source.py','phase1070_s_typed_native_mark.py',
             'phase1071_s_authenticated_source.py')}
        receipt['decision']='PASS_S_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN'
    except Exception as exc:
        receipt['reason']=type(exc).__name__+': '+str(exc)[:350]
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:receipt.get(k) for k in
                      ('phase','decision','reason','canonical_sha256','typed_mark_shape')},sort_keys=True))
    return 0 if receipt['decision'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(run())
