#!/usr/bin/env python3
"""V98 Independent Q preregistered 90-cell gate, fail-closed before PnL.

Requires Phase1050 frozen code + canonical hashes and fresh same-run Clean-4
source. No 2025+, contaminated holdout or external benchmark access.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase1042_q_signed_sevenslot_source import ASSETS,PATHS,compose_q
from phase1043_q_source_auth_and_canonical import run as fresh_q_source,OUT as SOURCE_OUT,canonicalize,ROOT
from phase1044_q_funded_signed_ledger import simulate_q_hourly,FEE_TIERS,ORDERS,CAPITAL_MODES
from phase1048_q_signed_funding_bounds import signed_bounds

MANIFEST=ROOT/'phase1050_q_frozen_manifest.json'
OUT=ROOT/'phase1051_q_training_gate_receipt.json'


def verify_freeze():
    if not MANIFEST.exists():raise PermissionError('Q_FREEZE_MANIFEST_NOT_YET_REGISTERED')
    m=json.loads(MANIFEST.read_text())
    if m.get('decision')!='FROZEN_Q_PRE_ECONOMIC' or set(m.get('code_blob_sha1',{}))!={
        'phase1040_q_signed_margin_oracle.py','phase1042_q_signed_sevenslot_source.py',
        'phase1043_q_source_auth_and_canonical.py','phase1044_q_funded_signed_ledger.py',
        'phase1048_q_signed_funding_bounds.py','phase1051_q_training_gate.py'}:
        raise PermissionError('Q_INCOMPLETE_FROZEN_CODE_MANIFEST')
    if set(m.get('canonical_sha256',{}))!=set(PATHS) or m.get('path_order')!=list(PATHS):
        raise PermissionError('Q_FROZEN_FIVE_PATH_ORDER')
    for name,sha in m['code_blob_sha1'].items():
        raw=(ROOT/name).read_bytes();blob=b'blob '+str(len(raw)).encode()+b'\x00'+raw
        if hashlib.sha1(blob).hexdigest()!=sha:
            raise PermissionError('Q_FROZEN_CODE_DRIFT_'+name)
    return m


def authenticated_inputs():
    from phase1000_four_asset_source_policy import BOUNDS
    from phase866_k_sevenslot_source import START,END
    from phase877_k_official_economic_dispatch import load_source_arrays
    with tempfile.TemporaryDirectory(prefix='v98_q_frozen_source_') as tmp:
        sandbox=Path(tmp)
        (sandbox/'phase243_clean4_canonical').symlink_to((ROOT/'phase243_clean4_canonical').resolve(),target_is_directory=True)
        (sandbox/'phase797_conservative_training_funding_bounds.csv').symlink_to(BOUNDS.resolve())
        arrays,rate,legacy_mark,event,years=load_source_arrays(sandbox)
    idx=pd.date_range(START,END,freq='h')
    if len(idx)!=18288 or int(event.sum())!=9144:
        raise PermissionError('Q_INCOMPLETE_TRAINING_SOURCE')
    bounds,br,be=signed_bounds(BOUNDS,idx)
    if not np.array_equal(rate,br) or not np.array_equal(event,be):
        raise PermissionError('Q_SIGNED_NATIVE_FUNDING_EVENT_DRIFT')
    frames=[pd.DataFrame(arrays[k],index=idx,columns=ASSETS) for k in ('open','high','low','close','quote_volume')]
    frames.append(pd.DataFrame(rate,index=idx,columns=ASSETS))
    paths=compose_q(*frames)
    targets={k:canonicalize(v)[0].to_numpy(float) for k,v in paths.items()}
    o,h,l=(arrays[k] for k in ('open','high','low'))
    down=pd.DataFrame(1-l/o).rolling(1440,min_periods=1440).max().to_numpy()
    up=pd.DataFrame(h/o-1).rolling(1440,min_periods=1440).max().to_numpy()
    return targets,arrays,rate,bounds,event,years,down,up


def complete_matrix(targets,arrays,rate,mark,event,years,down,up):
    cases={};failures=[];count=0
    for name in PATHS:
        cases[name]={}
        for tier,fee in FEE_TIERS.items():
            cases[name][tier]={}
            for order in ORDERS:
                cases[name][tier][order]={}
                for mode in CAPITAL_MODES:
                    count+=1
                    try:
                        r=simulate_q_hourly(targets[name],arrays['open'],arrays['high'],arrays['low'],arrays['close'],arrays['quote_volume'],rate,mark,event,down,up,fee,order=order,mode=mode,years=years,require_full_sample=True)
                    except Exception as e:
                        r={'survived':False,'reason':type(e).__name__+': '+str(e)[:200],'breach_index':None}
                    cases[name][tier][order][mode]=r
                    if not r.get('survived',False):
                        failures.append({'path':name,'tier':tier,'order':order,'mode':mode,
                                         'reason':r.get('reason'),'breach_index':r.get('breach_index')})
    if count!=90:raise AssertionError('Q_INCOMPLETE_90_MATRIX')
    return {'cells_attempted':count,'cells_survived':count-len(failures),'failures':failures,'cases':cases}


def growth_gate(m):
    if m.get('cells_attempted')!=90 or m.get('failures'):
        return {'passed':False,'reason':'incomplete_or_failed_survival','failed_cells':len(m.get('failures',[]))}
    for name in PATHS:
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    f=m['cases'][name][tier][order][mode].get('folds',{})
                    if set(f)!={'2023','2024'} or f['2023'].get('days')!=365 or f['2024'].get('days')!=366:
                        return {'passed':False,'reason':'incomplete_chronological_folds'}
    failures=[]
    for year in ('2023','2024'):
        for tier in ('base','severe'):
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    full=m['cases']['Q_full'][tier][order][mode]['folds'][year]['log_wealth']
                    if not math.isfinite(full) or full<=0:
                        failures.append({'year':year,'tier':tier,'order':order,'mode':mode,'reason':'nonpositive_growth'})
                    for name in PATHS:
                        if name=='Q_full':continue
                        alt=m['cases'][name][tier][order][mode]['folds'][year]['log_wealth']
                        if not math.isfinite(alt) or full<=alt:
                            failures.append({'year':year,'tier':tier,'order':order,'mode':mode,'path':name,'reason':'nonpositive_marginal'})
    return {'passed':not failures,'reason':'training_only_pending_separate_validation' if not failures else 'failed_growth_or_marginal','failures':failures}


def run(execute=False):
    result={'phase':1051,'decision':'BLOCKED_BEFORE_PNL','historical_pnl_computed':False,
            'ledger_invocations':0,'promotion_eligible':False,'validation_2025_read':False,
            'holdout_accessed':False,'external_benchmarks_used':False}
    try:
        manifest=verify_freeze()
        if fresh_q_source()!=0:raise PermissionError('Q_FRESH_SOURCE_FAILED')
        receipt=json.loads(SOURCE_OUT.read_text())
        if receipt['canonical_sha256']!=manifest['canonical_sha256']:
            raise PermissionError('Q_CANONICAL_HASH_DRIFT')
        result['canonical_sha256']=receipt['canonical_sha256']
        if not execute:
            result['decision']='PASS_Q_FROZEN_SOURCE_ONLY_NO_ECONOMICS'
        else:
            targets,arrays,rate,mark,event,years,down,up=authenticated_inputs()
            matrix=complete_matrix(targets,arrays,rate,mark,event,years,down,up)
            result['historical_pnl_computed']=True
            result['ledger_invocations']=matrix['cells_attempted']
            result['matrix']=matrix
            result['growth_gate']=growth_gate(matrix)
            result['decision']='PASS_Q_TRAINING_PENDING_2025_VALIDATION' if result['growth_gate']['passed'] else 'REJECT_Q_TRAINING_NO_RESCUE'
    except Exception as e:
        result['decision']='BLOCKED_AFTER_PNL_NO_PROMOTION' if result['historical_pnl_computed'] else 'BLOCKED_BEFORE_PNL'
        result['reason']=type(e).__name__+': '+str(e)[:350]
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result.get(k) for k in ('phase','decision','reason','ledger_invocations')},sort_keys=True))
    return 0 if result['decision'].startswith('PASS_') else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true')
    raise SystemExit(run(parser.parse_args().execute))
