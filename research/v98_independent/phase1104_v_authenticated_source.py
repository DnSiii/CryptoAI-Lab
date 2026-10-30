#!/usr/bin/env python3
"""V98 V fresh official source-only attestation; no PnL, no 2025 or benchmarks.

Reuses V98 read-only DATA provenance utilities; never prior alpha or PnL.
"""
from __future__ import annotations
import hashlib,io,json,tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase1103_v_sevenslot_source import ASSETS,PATHS,compose_v
from phase1101_v_robust_governor import ASSET_CAP,NET_CAP,GROSS_CAP
from phase1070_s_typed_native_mark import signed_mark_bounds

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'phase1104_v_authenticated_source_receipt.json'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def canonical_target(frame):
    x=frame.to_numpy(dtype=float)
    if x.ndim!=2 or x.shape[1]!=4 or not np.isfinite(x).all():
        raise ValueError('V_CANONICAL_GEOMETRY')
    if (np.abs(x).max()>ASSET_CAP+1e-10 or
        np.abs(x).sum(axis=1).max()>GROSS_CAP+1e-10 or
        np.abs(x.sum(axis=1)).max()>NET_CAP+1e-10):
        raise ValueError('V_CANONICAL_CAP')
    if np.max(np.abs(x*1e6-np.round(x*1e6)))>1e-7:
        raise ValueError('V_CANONICAL_NONQUANTIZED')
    raw=frame.to_csv(float_format='%.6f',lineterminator='\n').encode()
    parsed=pd.read_csv(io.BytesIO(raw),index_col=0).to_numpy(float)
    if not np.array_equal(parsed,x):
        raise ValueError('V_CANONICAL_SERIALIZATION_DRIFT')
    return hashlib.sha256(raw).hexdigest()

def attest(arrays,rate,mark,event,years,idx,bounds_csv):
    n=len(idx)
    if (n!=18288 or idx[0]!=pd.Timestamp('2022-12-01T00:00:00Z') or
        idx[-1]!=pd.Timestamp('2024-12-31T23:00:00Z') or
        any(np.asarray(v).shape!=(n,4) for v in arrays.values()) or
        np.asarray(rate).shape!=(n,4) or np.asarray(event).shape!=(n,4) or
        np.asarray(mark).shape!=(n,4) or np.asarray(years).shape!=(n,) or
        not np.array_equal(idx.year,years) or
        not np.isin(years,(2022,2023,2024)).all() or
        np.asarray(event).dtype!=bool or int(event.sum())!=9144):
        raise ValueError('V_SOURCE_GEOMETRY_OR_FUTURE')
    signed=signed_mark_bounds(bounds_csv,idx,rate,event,mark,require_full=True)
    if signed.shape!=(n,4,2):
        raise ValueError('V_SIGNED_MARK_GEOMETRY')
    frames=[pd.DataFrame(arrays[k],index=idx,columns=ASSETS)
            for k in ('open','high','low','close','quote_volume')]
    frames.append(pd.DataFrame(rate,index=idx,columns=ASSETS))
    paths,diag=compose_v(*frames,diagnostics=True)
    if tuple(paths)!=PATHS:raise ValueError('V_PATHS_MISMATCH')
    hashes={k:canonical_target(paths[k]) for k in PATHS}
    if {k:canonical_target(v) for k,v in compose_v(*frames).items()}!=hashes:
        raise ValueError('V_SAME_RUN_NONDETERMINISM')
    return {'canonical_sha256':hashes,'typed_mark_shape':list(signed.shape),
            'typed_mark_csv_sha256':digest(bounds_csv),
            'native_funding_events':int(event.sum()),'official_hours':n,'diagnostics':diag}

def run():
    receipt={'phase':1104,'decision':'BLOCKED_BEFORE_PNL','source_only':True,
             'historical_pnl_computed':False,'validation_2025_read':False,
             'holdout_accessed':False,'external_benchmarks_used':False,
             'promotion_eligible':False,'frozen':False}
    try:
        from phase803_training_ohlc_official_replay import run as official_ohlc
        from phase1000_four_asset_source_policy import run as official_funding,OUT as POLICY_OUT,BOUNDS
        from phase866_k_sevenslot_source import START,END,PINS
        from phase877_k_official_economic_dispatch import load_source_arrays,PASS_OHLC
        o=official_ohlc()
        if o.get('decision')!=PASS_OHLC or o.get('vendor_origin_attested') is not True:
            raise PermissionError('V_FRESH_OHLC_NOT_ATTESTED')
        for asset in ASSETS:
            a=o.get('assets',{}).get(asset,{})
            if a.get('sha256')!=PINS[asset] or a.get('hours')!=18288 or a.get('monthly_archives')!=25:
                raise PermissionError('V_OHLC_PIN_'+asset)
        if official_funding()!=0:raise PermissionError('V_FRESH_MARK_FUNDING_NOT_ATTESTED')
        p=json.loads(POLICY_OUT.read_text())
        if (p.get('decision')!='PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY' or
            p.get('verified_asset_events')!=9144 or p.get('vendor_archive_checksum_attested') is not True or
            p.get('validation_2025_read') is not False or p.get('bounds_csv_sha256')!=digest(BOUNDS)):
            raise PermissionError('V_SIGNED_VENDOR_PROVENANCE')
        with tempfile.TemporaryDirectory(prefix='v98_v_auth_') as tmp:
            sandbox=Path(tmp)
            (sandbox/'phase243_clean4_canonical').symlink_to(
                (ROOT/'phase243_clean4_canonical').resolve(),target_is_directory=True)
            (sandbox/'phase797_conservative_training_funding_bounds.csv').symlink_to(BOUNDS.resolve())
            arrays,rate,mark,event,years=load_source_arrays(sandbox)
        result=attest(arrays,rate,mark,event,years,pd.date_range(START,END,freq='h'),BOUNDS)
        receipt.update(result)
        receipt['official_source']={'ohlc':o['decision'],'funding_mark':p['decision']}
        receipt['decision']='PASS_V_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN'
    except Exception as exc:
        receipt['reason']=type(exc).__name__+': '+str(exc)[:350]
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:receipt.get(k) for k in
        ('phase','decision','reason','canonical_sha256','typed_mark_shape')},sort_keys=True))
    return 0 if receipt['decision'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(run())
