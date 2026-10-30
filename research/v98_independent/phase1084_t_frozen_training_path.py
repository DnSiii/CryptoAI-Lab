#!/usr/bin/env python3
"""V98 T frozen 18-cell per-path chronological training; no 2025+ or benchmarks.
Requires four independent fresh authenticated source receipts before freeze.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase1081_t_sevenslot_source import ASSETS,PATHS,compose_t,regime
from phase1082_t_authenticated_source import run as fresh_source,OUT as SOURCE_OUT,canonical_target,ROOT,digest
from phase1070_s_typed_native_mark import signed_mark_bounds
from phase1083_t_event_driven_ledger import simulate_t,prior_shocks,FEE_TIERS,ORDERS,CAPITAL_MODES

MANIFEST=ROOT/'phase1084_t_frozen_manifest.json'
FROZEN_FILES=('phase1081_t_sevenslot_source.py','phase1082_t_authenticated_source.py',
              'phase1083_t_event_driven_ledger.py','phase1084_t_frozen_training_path.py',
              'phase1070_s_typed_native_mark.py','phase1073_s_signed_execution.py',
              'phase1074_s_funded_ledger.py')

def verify_freeze():
    m=json.loads(MANIFEST.read_text())
    if (m.get('decision')!='FROZEN_T_PRE_ECONOMIC' or
        m.get('source_gate')!='PASS_T_FOUR_INDEPENDENT_FRESH_SOURCE_RECOMPOSITIONS_NOT_FROZEN' or
        set(m.get('code_blob_sha1',{}))!=set(FROZEN_FILES) or
        set(m.get('canonical_sha256',{}))!=set(PATHS) or
        m.get('path_order')!=list(PATHS) or m.get('typed_mark_shape')!=[18288,4,2] or
        m.get('native_funding_events')!=9144 or m.get('training_folds')!=[2023,2024] or
        m.get('fee_tiers')!=FEE_TIERS or m.get('orders')!=list(ORDERS) or
        m.get('capital_modes')!=CAPITAL_MODES):
        raise PermissionError('T_FROZEN_MANIFEST_INCOMPLETE')
    for name,sha in m['code_blob_sha1'].items():
        raw=(ROOT/name).read_bytes()
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()!=sha:
            raise PermissionError('T_FROZEN_CODE_DRIFT_'+name)
    return m

def authenticated_inputs(m):
    if fresh_source()!=0:raise PermissionError('T_FRESH_AUTHENTICATED_SOURCE_FAILED')
    r=json.loads(SOURCE_OUT.read_text())
    if (r.get('canonical_sha256')!=m['canonical_sha256'] or
        r.get('typed_mark_csv_sha256')!=m['typed_mark_csv_sha256'] or
        r.get('native_funding_events')!=9144 or
        r.get('decision')!='PASS_T_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN'):
        raise PermissionError('T_FROZEN_SOURCE_OR_TARGET_HASH_DRIFT')
    from phase1000_four_asset_source_policy import BOUNDS
    from phase866_k_sevenslot_source import START,END
    from phase877_k_official_economic_dispatch import load_source_arrays
    with tempfile.TemporaryDirectory(prefix='v98_t_econ_') as tmp:
        sandbox=Path(tmp)
        (sandbox/'phase243_clean4_canonical').symlink_to((ROOT/'phase243_clean4_canonical').resolve(),target_is_directory=True)
        (sandbox/'phase797_conservative_training_funding_bounds.csv').symlink_to(BOUNDS.resolve())
        arrays,rate,mark,event,years=load_source_arrays(sandbox)
    idx=pd.date_range(START,END,freq='h')
    if (len(idx)!=18288 or not np.isin(years,(2022,2023,2024)).all() or
        int(event.sum())!=9144 or digest(BOUNDS)!=m['typed_mark_csv_sha256']):
        raise PermissionError('T_AUTHENTICATED_TRAINING_GEOMETRY')
    signed=signed_mark_bounds(BOUNDS,idx,rate,event,mark,require_full=True)
    frames=[pd.DataFrame(arrays[k],index=idx,columns=ASSETS)
            for k in ('open','high','low','close','quote_volume')]
    frames.append(pd.DataFrame(rate,index=idx,columns=ASSETS))
    paths=compose_t(*frames)
    if {k:canonical_target(v) for k,v in paths.items()}!=m['canonical_sha256']:
        raise PermissionError('T_RECOMPOSED_TARGET_DRIFT')
    ret=np.log(frames[3]).diff().fillna(0)
    market=ret.mean(axis=1);vol=market.rolling(168,min_periods=168).std(ddof=0)
    states=regime(market,vol)
    down,up=prior_shocks(arrays['open'],arrays['high'],arrays['low'])
    return {k:v.to_numpy(float) for k,v in paths.items()},arrays,rate,signed,event,years,down,up,states

def run(path):
    if path not in PATHS:raise ValueError('T_UNKNOWN_PREREGISTERED_PATH')
    out=ROOT/('phase1084_t_'+path+'_training_receipt.json')
    result={'phase':1084,'path':path,'decision':'BLOCKED_BEFORE_PNL',
            'historical_pnl_computed':False,'cells_attempted':0,'cells_survived':0,
            'cases':{},'failures':[],'validation_2025_read':False,
            'holdout_accessed':False,'external_benchmarks_used':False,
            'promotion_eligible':False}
    try:
        m=verify_freeze()
        targets,arrays,rate,signed,event,years,down,up,states=authenticated_inputs(m)
        result['canonical_sha256']=m['canonical_sha256'][path]
        result['decision']='IN_PROGRESS_NOT_APPROVED'
        for tier,fee in FEE_TIERS.items():
            result['cases'][tier]={}
            for order in ORDERS:
                result['cases'][tier][order]={}
                for mode in CAPITAL_MODES:
                    try:
                        cell=simulate_t(targets[path],arrays['open'],arrays['high'],arrays['low'],
                            arrays['close'],arrays['quote_volume'],rate,signed,event,down,up,
                            fee,order=order,mode=mode,years=years,regimes=states)
                    except Exception as exc:
                        cell={'survived':False,'reason':type(exc).__name__+': '+str(exc)[:200],
                              'breach_index':None,'preflight_failure':True}
                    result['cases'][tier][order][mode]=cell
                    result['cells_attempted']+=1
                    result['historical_pnl_computed']=True
                    if cell.get('survived'):result['cells_survived']+=1
                    else:result['failures'].append({'tier':tier,'order':order,'mode':mode,
                          'reason':cell.get('reason'),'breach_index':cell.get('breach_index')})
                    out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
        if result['cells_attempted']!=18:raise AssertionError('T_INCOMPLETE_PATH_MATRIX')
        result['decision']='PASS_T_PATH_SURVIVAL_PENDING_90CELL_GROWTH' if result['cells_survived']==18 else 'REJECT_T_PATH_TRAINING_NO_RESCUE'
    except Exception as exc:
        result['decision']='BLOCKED_AFTER_PARTIAL_PNL' if result['historical_pnl_computed'] else 'BLOCKED_BEFORE_PNL'
        result['reason']=type(exc).__name__+': '+str(exc)[:350]
    out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result.get(k) for k in
        ('phase','path','decision','cells_attempted','cells_survived','reason')},sort_keys=True))
    return 0 if result['decision'].startswith('PASS_') else 2

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--path',required=True,choices=PATHS)
    raise SystemExit(run(p.parse_args().path))
