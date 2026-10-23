#!/usr/bin/env python3
"""V98 Z authenticated source-only 15-hash receipt. No historical PnL."""
from __future__ import annotations
import hashlib,json,tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase1143_z_sevenslot_source import ASSETS,PATHS,CAPITAL,compose_z,canonical_hash
from phase1070_s_typed_native_mark import signed_mark_bounds

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'phase1145_z_authenticated_source_receipt.json'
START=pd.Timestamp('2022-12-01T00:00:00Z')
END=pd.Timestamp('2024-12-31T23:00:00Z')

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def attest(arrays,rate,mark,event,years,bounds_csv):
    idx=pd.date_range(START,END,freq='h');n=len(idx)
    if (n!=18288 or any(np.asarray(v).shape!=(n,4) for v in arrays.values())
        or np.asarray(rate).shape!=(n,4) or np.asarray(event).shape!=(n,4)
        or np.asarray(mark).shape!=(n,4) or np.asarray(years).shape!=(n,)
        or np.asarray(event).dtype!=bool or int(event.sum())!=9144
        or not np.array_equal(idx.year,years) or not np.isin(years,(2022,2023,2024)).all()
        or any(int(event[:,j].sum())!=2286 for j in range(4))):
        raise ValueError('Z1145_SOURCE_GEOMETRY_OR_FUTURE')
    signed=signed_mark_bounds(bounds_csv,idx,rate,event,mark,require_full=True)
    if signed.shape!=(n,4,2):raise ValueError('Z1145_SIGNED_MARK_GEOMETRY')
    frames=[pd.DataFrame(arrays[k],index=idx,columns=ASSETS)
        for k in ('open','high','low','close','quote_volume')]
    frames.append(pd.DataFrame(rate,index=idx,columns=ASSETS))
    paths,diag=compose_z(*frames,diagnostics=True)
    expected={(p,m) for p in PATHS for m in CAPITAL}
    if set(paths)!=expected:raise ValueError('Z1145_15_TARGET_GEOMETRY')
    hashes={p+'__'+m:canonical_hash(paths[p,m]) for p,m in expected}
    if len(set(hashes.values()))<2:raise ValueError('Z1145_DEGENERATE_TARGETS')
    return {'canonical_sha256':dict(sorted(hashes.items())),
        'official_hours':n,'native_funding_events':int(event.sum()),
        'typed_mark_shape':list(signed.shape),'typed_mark_csv_sha256':digest(bounds_csv),
        'diagnostics':{k:v for k,v in diag.items() if k!='governor_calls'},
        'governor_calls':{p+'__'+m:int(v) for (p,m),v in diag['governor_calls'].items()}}

def run():
    receipt={'phase':1145,'decision':'BLOCKED_BEFORE_PNL','source_only':True,
        'historical_pnl_computed':False,'validation_2025_read':False,
        'holdout_accessed':False,'external_benchmarks_used':False,
        'promotion_eligible':False,'frozen':False}
    try:
        from phase803_training_ohlc_official_replay import run as official_ohlc
        from phase1000_four_asset_source_policy import run as official_funding,OUT as POLICY_OUT,BOUNDS
        from phase866_k_sevenslot_source import PINS
        from phase877_k_official_economic_dispatch import load_source_arrays,PASS_OHLC
        o=official_ohlc()
        if o.get('decision')!=PASS_OHLC or o.get('vendor_origin_attested') is not True:
            raise PermissionError('Z1145_OHLC_NOT_ATTESTED')
        for asset in ASSETS:
            a=o.get('assets',{}).get(asset,{})
            if a.get('sha256')!=PINS[asset] or a.get('hours')!=18288 or a.get('monthly_archives')!=25:
                raise PermissionError('Z1145_OHLC_PIN_'+asset)
        if official_funding()!=0:raise PermissionError('Z1145_MARK_FUNDING_NOT_ATTESTED')
        p=json.loads(POLICY_OUT.read_text())
        if (p.get('decision')!='PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY'
            or p.get('verified_asset_events')!=9144
            or p.get('vendor_archive_checksum_attested') is not True
            or p.get('validation_2025_read') is not False
            or p.get('bounds_csv_sha256')!=digest(BOUNDS)):
            raise PermissionError('Z1145_SIGNED_VENDOR_PROVENANCE')
        with tempfile.TemporaryDirectory(prefix='v98_z_auth_') as tmp:
            sandbox=Path(tmp)
            (sandbox/'phase243_clean4_canonical').symlink_to(
                (ROOT/'phase243_clean4_canonical').resolve(),target_is_directory=True)
            (sandbox/'phase797_conservative_training_funding_bounds.csv').symlink_to(BOUNDS.resolve())
            arrays,rate,mark,event,years=load_source_arrays(sandbox)
        receipt.update(attest(arrays,rate,mark,event,years,BOUNDS))
        receipt['official_source']={'ohlc':o['decision'],'funding_mark':p['decision']}
        receipt['decision']='PASS_Z_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN'
    except Exception as exc:
        receipt['reason']=type(exc).__name__+': '+str(exc)[:350]
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:receipt.get(k) for k in ('phase','decision','reason','official_hours',
        'native_funding_events','canonical_sha256')},sort_keys=True))
    return 0 if receipt['decision'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(run())
