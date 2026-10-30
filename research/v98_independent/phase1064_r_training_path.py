#!/usr/bin/env python3
"""V98 Independent R frozen single-path 18-cell authenticated economic gate.

Run each of five frozen paths independently (matrix=90); 2023/2024 only.
Fail closed and checkpoint every cell. Never access 2025 or benchmarks.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase1059_r_sevenslot_source import ASSETS,PATHS,compose_r,regime
from phase1060_r_source_auth import run as fresh_source,OUT as SOURCE_OUT,canonicalize,ROOT
from phase1062_r_funded_ledger import simulate,FEE_TIERS,ORDERS,CAPITAL_MODES

MANIFEST=ROOT/'phase1063_r_frozen_manifest.json'


def verify_freeze():
    m=json.loads(MANIFEST.read_text())
    names=('phase1059_r_sevenslot_source.py','phase1060_r_source_auth.py',
           'phase1061_r_signed_margin_oracle.py','phase1062_r_funded_ledger.py',
           'phase1064_r_training_path.py')
    if m.get('decision')!='FROZEN_R_PRE_ECONOMIC' or set(m.get('code_blob_sha1',{}))!=set(names) or set(m.get('canonical_sha256',{}))!=set(PATHS) or m.get('path_order')!=list(PATHS):
        raise PermissionError('R_FROZEN_MANIFEST_INCOMPLETE')
    for name,sha in m['code_blob_sha1'].items():
        raw=(ROOT/name).read_bytes()
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()!=sha:
            raise PermissionError('R_FROZEN_CODE_DRIFT_'+name)
    if m.get('fee_tiers')!=FEE_TIERS or m.get('orders')!=list(ORDERS) or m.get('capital_modes')!=CAPITAL_MODES:
        raise PermissionError('R_FROZEN_ECONOMIC_GRID_DRIFT')
    return m


def authenticated_inputs(manifest):
    if fresh_source()!=0:raise PermissionError('R_FRESH_AUTHENTICATED_SOURCE_FAILED')
    r=json.loads(SOURCE_OUT.read_text())
    if r.get('canonical_sha256')!=manifest['canonical_sha256'] or r.get('native_funding_events')!=9144:
        raise PermissionError('R_SOURCE_OR_TARGET_HASH_DRIFT')
    from phase1000_four_asset_source_policy import BOUNDS
    from phase866_k_sevenslot_source import START,END
    from phase877_k_official_economic_dispatch import load_source_arrays
    with tempfile.TemporaryDirectory(prefix='v98_r_econ_') as tmp:
        sandbox=Path(tmp)
        (sandbox/'phase243_clean4_canonical').symlink_to((ROOT/'phase243_clean4_canonical').resolve(),target_is_directory=True)
        (sandbox/'phase797_conservative_training_funding_bounds.csv').symlink_to(BOUNDS.resolve())
        arrays,rate,mark,event,years=load_source_arrays(sandbox)
    idx=pd.date_range(START,END,freq='h')
    if len(idx)!=18288 or not np.isin(years,(2022,2023,2024)).all() or int(event.sum())!=9144:
        raise PermissionError('R_AUTHENTICATED_TRAINING_GEOMETRY')
    frames=[pd.DataFrame(arrays[k],index=idx,columns=ASSETS) for k in ('open','high','low','close','quote_volume')]
    frames.append(pd.DataFrame(rate,index=idx,columns=ASSETS))
    paths=compose_r(*frames)
    if {k:canonicalize(v) for k,v in paths.items()}!=manifest['canonical_sha256']:
        raise PermissionError('R_RECOMPOSED_TARGET_DRIFT')
    targets={k:v.to_numpy(float) for k,v in paths.items()}
    o,h,l=(arrays[k] for k in ('open','high','low'))
    down=pd.DataFrame(1-l/o).rolling(1440,min_periods=1440).max().to_numpy()
    up=pd.DataFrame(h/o-1).rolling(1440,min_periods=1440).max().to_numpy()
    states=regime(np.log(frames[3]).diff().mean(axis=1))
    return targets,arrays,rate,mark,event,years,down,up,states


def run(path):
    if path not in PATHS:raise ValueError('R_UNKNOWN_PREREGISTERED_PATH')
    out=ROOT/('phase1064_r_'+path+'_training_receipt.json')
    result={'phase':1064,'path':path,'decision':'BLOCKED_BEFORE_PNL',
            'historical_pnl_computed':False,'cells_attempted':0,'cells_survived':0,
            'cases':{},'failures':[],'validation_2025_read':False,
            'holdout_accessed':False,'external_benchmarks_used':False,
            'promotion_eligible':False}
    try:
        m=verify_freeze()
        targets,arrays,rate,mark,event,years,down,up,states=authenticated_inputs(m)
        result['canonical_sha256']=m['canonical_sha256'][path]
        result['decision']='IN_PROGRESS_NOT_APPROVED'
        for tier,fee in FEE_TIERS.items():
            result['cases'][tier]={}
            for order in ORDERS:
                result['cases'][tier][order]={}
                for mode in CAPITAL_MODES:
                    try:
                        cell=simulate(targets[path],arrays['open'],arrays['high'],arrays['low'],arrays['close'],arrays['quote_volume'],rate,mark,event,down,up,fee,order=order,mode=mode,years=years,regimes=states,require_full_sample=True)
                    except Exception as e:
                        cell={'survived':False,'reason':type(e).__name__+': '+str(e)[:200],'breach_index':None,'preflight_failure':True}
                    result['cases'][tier][order][mode]=cell
                    result['cells_attempted']+=1
                    result['historical_pnl_computed']=True
                    if cell.get('survived'):
                        result['cells_survived']+=1
                    else:
                        result['failures'].append({'tier':tier,'order':order,'mode':mode,
                                                   'reason':cell.get('reason'),'breach_index':cell.get('breach_index')})
                    out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
        if result['cells_attempted']!=18:raise AssertionError('R_INCOMPLETE_PATH_MATRIX')
        result['decision']='PASS_R_PATH_SURVIVAL_PENDING_90CELL_GROWTH' if result['cells_survived']==18 else 'REJECT_R_PATH_TRAINING_NO_RESCUE'
    except Exception as e:
        result['decision']='BLOCKED_AFTER_PARTIAL_PNL' if result['historical_pnl_computed'] else 'BLOCKED_BEFORE_PNL'
        result['reason']=type(e).__name__+': '+str(e)[:350]
    out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result.get(k) for k in ('phase','path','decision','cells_attempted','cells_survived','reason')},sort_keys=True))
    return 0 if result['decision'].startswith('PASS_') else 2

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--path',required=True,choices=PATHS)
    raise SystemExit(run(p.parse_args().path))
