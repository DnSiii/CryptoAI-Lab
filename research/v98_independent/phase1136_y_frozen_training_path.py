#!/usr/bin/env python3
"""Phase1136: immutable Y five-path x 18-cell authenticated chronological training.

NO historical PnL before Phase1137 complete code+source freeze. No 2025+.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase1125_y_sevenslot_source import ASSETS,PATHS,compose_y,hysteresis
from phase1130_y_authenticated_source import run as fresh_source,OUT as SOURCE_OUT,canonical_target,ROOT,digest
from phase1070_s_typed_native_mark import signed_mark_bounds
from phase1135_y_funded_training_simulator import simulate_y,FEE_TIERS,ORDERS,CAPITAL_MODES

MANIFEST=ROOT/'phase1137_y_full_pre_economic_freeze.json'
FROZEN_FILES=(
 'phase1123_y_continuous_feedback.py','phase1124_y_pretrade_growth.py',
 'phase1125_y_sevenslot_source.py','phase1126_y_hourly_ledger.py',
 'phase1127_y_synthetic_integration.py','phase1128_y_funding_reserve_audit.py',
 'phase1130_y_authenticated_source.py','phase1131_y_growth_metrics.py',
 'phase1132_y_closed_trade_accounting.py','phase1070_s_typed_native_mark.py',
 'phase1135_y_funded_training_simulator.py','phase1136_y_frozen_training_path.py',
 'phase1138_y_90cell_growth_audit.py')

def blob_sha(path):
    raw=Path(path).read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()

def verify_freeze():
    m=json.loads(MANIFEST.read_text())
    lock=json.loads((ROOT/'phase1133_y_source_and_structural_lock.json').read_text())
    if (m.get('decision')!='FROZEN_Y_FULL_PRE_ECONOMIC' or
        m.get('source_lock_phase')!=1133 or
        m.get('source_gate')!=lock.get('source_gate') or
        m.get('canonical_sha256')!=lock.get('canonical_sha256') or
        m.get('typed_mark_csv_sha256')!=lock.get('typed_mark_csv_sha256') or
        m.get('native_funding_events')!=9144 or
        m.get('typed_mark_shape')!=[18288,4,2] or
        m.get('path_order')!=list(PATHS) or
        m.get('fee_tiers')!=FEE_TIERS or m.get('orders')!=list(ORDERS) or
        m.get('capital_modes')!=CAPITAL_MODES or
        m.get('training_folds')!=[2023,2024] or
        set(m.get('code_blob_sha1',{}))!=set(FROZEN_FILES) or
        m.get('historical_pnl_computed') is not False or
        m.get('validation_2025_read') is not False):
        raise PermissionError('Y1136_FREEZE_INCOMPLETE_OR_DRIFT')
    for name,sha in m['code_blob_sha1'].items():
        if blob_sha(ROOT/name)!=sha:
            raise PermissionError('Y1136_FROZEN_CODE_DRIFT_'+name)
    return m

def authenticated_inputs(m):
    if fresh_source()!=0:raise PermissionError('Y1136_FRESH_SOURCE_FAILED')
    receipt=json.loads(SOURCE_OUT.read_text())
    if (receipt.get('decision')!='PASS_Y_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN' or
        receipt.get('canonical_sha256')!=m['canonical_sha256'] or
        receipt.get('typed_mark_csv_sha256')!=m['typed_mark_csv_sha256'] or
        receipt.get('native_funding_events')!=9144):
        raise PermissionError('Y1136_FROZEN_SOURCE_DRIFT')
    from phase1000_four_asset_source_policy import BOUNDS
    from phase866_k_sevenslot_source import START,END
    from phase877_k_official_economic_dispatch import load_source_arrays
    with tempfile.TemporaryDirectory(prefix='v98_y_economic_') as tmp:
        sandbox=Path(tmp)
        (sandbox/'phase243_clean4_canonical').symlink_to(
            (ROOT/'phase243_clean4_canonical').resolve(),target_is_directory=True)
        (sandbox/'phase797_conservative_training_funding_bounds.csv').symlink_to(BOUNDS.resolve())
        arrays,rate,mark,event,years=load_source_arrays(sandbox)
    idx=pd.date_range(START,END,freq='h')
    if (len(idx)!=18288 or int(event.sum())!=9144 or
        not np.isin(years,(2022,2023,2024)).all() or
        digest(BOUNDS)!=m['typed_mark_csv_sha256']):
        raise PermissionError('Y1136_SOURCE_GEOMETRY')
    signed=signed_mark_bounds(BOUNDS,idx,rate,event,mark,require_full=True)
    frames=[pd.DataFrame(arrays[k],index=idx,columns=ASSETS)
            for k in ('open','high','low','close','quote_volume')]
    frames.append(pd.DataFrame(rate,index=idx,columns=ASSETS))
    paths=compose_y(*frames)
    if {k:canonical_target(v) for k,v in paths.items()}!=m['canonical_sha256']:
        raise PermissionError('Y1136_TARGET_HASH_DRIFT')
    r=np.log(frames[3]).diff().fillna(0.)
    market=r.mean(axis=1);index=np.exp(market.cumsum())
    dd=index/index.rolling(336,min_periods=336).max()-1
    dd_base=dd.shift(1).rolling(336,min_periods=336).median()
    breadth144=((np.log(frames[3])-np.log(frames[3]).shift(144))>0).sum(axis=1)
    raw=np.where((dd<dd_base)&(breadth144<=1),0,
                 np.where((dd>dd_base)&(breadth144>=3),2,1))
    states=hysteresis(raw,48)
    return {k:v.to_numpy(float) for k,v in paths.items()},arrays,rate,signed,event,years,states

def run(path):
    if path not in PATHS:raise ValueError('Y1136_UNREGISTERED_PATH')
    out=ROOT/('phase1136_y_'+path+'_training_receipt.json')
    result={'phase':1136,'path':path,'decision':'BLOCKED_BEFORE_PNL',
        'historical_pnl_computed':False,'cells_attempted':0,'cells_survived':0,
        'cases':{},'failures':[],'validation_2025_read':False,
        'holdout_accessed':False,'external_benchmarks_used':False,
        'promotion_eligible':False}
    try:
        m=verify_freeze()
        targets,arrays,rate,signed,event,years,states=authenticated_inputs(m)
        result['canonical_sha256']=m['canonical_sha256'][path]
        result['decision']='IN_PROGRESS_NOT_APPROVED'
        for tier,fee in FEE_TIERS.items():
            result['cases'][tier]={}
            for order in ORDERS:
                result['cases'][tier][order]={}
                for mode in CAPITAL_MODES:
                    try:
                        cell=simulate_y(targets[path],arrays['open'],arrays['high'],
                            arrays['low'],arrays['close'],arrays['quote_volume'],
                            rate,signed,event,fee=fee,order=order,mode=mode,
                            years=years,regimes=states,strict=True)
                    except Exception as exc:
                        cell={'survived':False,
                            'reason':type(exc).__name__+': '+str(exc)[:200],
                            'breach_index':None,'preflight_failure':True}
                    result['cases'][tier][order][mode]=cell
                    result['cells_attempted']+=1
                    result['historical_pnl_computed']=True
                    if cell.get('survived'):result['cells_survived']+=1
                    else:result['failures'].append({'tier':tier,'order':order,
                        'mode':mode,'reason':cell.get('reason'),
                        'breach_index':cell.get('breach_index')})
                    out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
        if result['cells_attempted']!=18:
            raise AssertionError('Y1136_INCOMPLETE_PATH_MATRIX')
        result['decision']=('PASS_Y_PATH_SURVIVAL_PENDING_GROWTH_AUDIT'
            if result['cells_survived']==18 else 'REJECT_Y_PATH_TRAINING_NO_RESCUE')
    except Exception as exc:
        result['decision']=('BLOCKED_AFTER_PARTIAL_PNL'
            if result['historical_pnl_computed'] else 'BLOCKED_BEFORE_PNL')
        result['reason']=type(exc).__name__+': '+str(exc)[:350]
    out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result.get(k) for k in
        ('phase','path','decision','cells_attempted','cells_survived','reason')},sort_keys=True))
    return 0 if result['decision'].startswith('PASS_') else 2

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--path',required=True,choices=PATHS)
    raise SystemExit(run(p.parse_args().path))
