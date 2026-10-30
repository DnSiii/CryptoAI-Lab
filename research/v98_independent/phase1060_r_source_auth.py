#!/usr/bin/env python3
"""V98 Independent R authenticated Clean-4 source-only five-path hash gate.

Fresh official 2022-2024 OHLC/mark/native funding. No PnL or future data.
"""
from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase1059_r_sevenslot_source import compose_r,ASSETS,PATHS,ASSET_CAP,NET_CAP,GROSS_CAP

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'phase1060_r_source_auth_receipt.json'


def canonicalize(frame):
    x=frame.to_numpy(float)
    if x.ndim!=2 or x.shape[1]!=4 or not np.isfinite(x).all():
        raise ValueError('R_NONFINITE_CANONICAL_TARGET')
    if np.abs(x).max()>ASSET_CAP+1e-10 or np.abs(x).sum(axis=1).max()>GROSS_CAP+1e-10 or np.abs(x.sum(axis=1)).max()>NET_CAP+1e-10:
        raise ValueError('R_PRE_CANONICAL_CAP_BREACH')
    if np.max(np.abs(x*1e8-np.round(x*1e8)))>1e-6:
        raise ValueError('R_NONCANONICAL_PRECISION')
    # Target composer has already conservatively quantized inward.
    out=pd.DataFrame(x,index=frame.index,columns=frame.columns)
    raw=out.to_csv(float_format='%.8f').encode('utf-8')
    parsed=pd.read_csv(__import__('io').BytesIO(raw),index_col=0).to_numpy(float)
    if not np.array_equal(parsed,x):
        raise ValueError('R_SERIALIZATION_DRIFT')
    if np.abs(parsed).max()>ASSET_CAP+1e-10 or np.abs(parsed).sum(axis=1).max()>GROSS_CAP+1e-10 or np.abs(parsed.sum(axis=1)).max()>NET_CAP+1e-10:
        raise ValueError('R_POST_SERIALIZATION_CAP_BREACH')
    return hashlib.sha256(raw).hexdigest()


def run():
    receipt={'phase':1060,'decision':'BLOCKED_BEFORE_PNL','historical_pnl_computed':False,
             'validation_2025_read':False,'holdout_accessed':False,'external_benchmarks_used':False,
             'promotion_eligible':False}
    try:
        from phase803_training_ohlc_official_replay import run as official_ohlc
        from phase1000_four_asset_source_policy import run as official_funding, OUT as POLICY_OUT, BOUNDS
        from phase866_k_sevenslot_source import START,END,PINS
        from phase877_k_official_economic_dispatch import load_source_arrays,PASS_OHLC
        o=official_ohlc()
        if o.get('decision')!=PASS_OHLC or o.get('vendor_origin_attested') is not True:
            raise PermissionError('R_OHLC_SOURCE_NOT_ATTESTED')
        for asset in ASSETS:
            p=o.get('assets',{}).get(asset,{})
            if p.get('sha256')!=PINS[asset] or p.get('hours')!=18288 or p.get('monthly_archives')!=25:
                raise PermissionError('R_OHLC_PIN_DRIFT_'+asset)
        if official_funding()!=0:raise PermissionError('R_NATIVE_FUNDING_MARK_SOURCE_FAILED')
        p=json.loads(POLICY_OUT.read_text())
        if p.get('decision')!='PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY' or p.get('verified_asset_events')!=9144 or p.get('vendor_archive_checksum_attested') is not True or p.get('validation_2025_read') is not False:
            raise PermissionError('R_FUNDING_MARK_PROVENANCE_FAILED')
        with tempfile.TemporaryDirectory(prefix='v98_r_source_') as tmp:
            sandbox=Path(tmp)
            (sandbox/'phase243_clean4_canonical').symlink_to((ROOT/'phase243_clean4_canonical').resolve(),target_is_directory=True)
            (sandbox/'phase797_conservative_training_funding_bounds.csv').symlink_to(BOUNDS.resolve())
            arrays,rate,mark,event,years=load_source_arrays(sandbox)
        idx=pd.date_range(START,END,freq='h')
        if len(idx)!=18288 or not np.isin(years,(2022,2023,2024)).all() or int(event.sum())!=9144:
            raise PermissionError('R_TRAINING_SOURCE_GEOMETRY')
        frames=[pd.DataFrame(arrays[k],index=idx,columns=ASSETS) for k in ('open','high','low','close','quote_volume')]
        frames.append(pd.DataFrame(rate,index=idx,columns=ASSETS))
        paths,diagnostics=compose_r(*frames,diagnostics=True)
        if tuple(paths)!=PATHS:raise ValueError('R_INCOMPLETE_FIVE_PATHS')
        hashes={k:canonicalize(v) for k,v in paths.items()}
        second=compose_r(*frames)
        if {k:canonicalize(v) for k,v in second.items()}!=hashes:
            raise ValueError('R_NONDETERMINISTIC_HASHES')
        receipt.update({'decision':'PASS_R_SOURCE_ONLY_NOT_ECONOMICALLY_APPROVED',
                        'canonical_sha256':hashes,'diagnostics':diagnostics,
                        'official_source':{'ohlc':o['decision'],'funding_mark':p['decision']},
                        'official_hours':len(idx),'native_funding_events':int(event.sum()),
                        'source_code_git_blob_sha1':{}})
        for name in ('phase1059_r_sevenslot_source.py','phase1060_r_source_auth.py'):
            raw=(ROOT/name).read_bytes()
            receipt['source_code_git_blob_sha1'][name]=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()
    except Exception as e:
        receipt['reason']=type(e).__name__+': '+str(e)[:350]
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:receipt.get(k) for k in ('phase','decision','reason','canonical_sha256')},sort_keys=True))
    return 0 if receipt['decision'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(run())
