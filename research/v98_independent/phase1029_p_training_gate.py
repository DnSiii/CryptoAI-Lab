#!/usr/bin/env python3
"""V98 Independent P preregistered 90-cell training-only economic gate.

Explicit --preflight NEVER calls PnL. --execute allowed only after source,
code blob pins and canonical five-target SHA256 hashes match. 2025+ forbidden.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path
from phase803_training_ohlc_official_replay import run as fresh_ohlc
from phase1000_four_asset_source_policy import run as fresh_policy, OUT as POLICY_OUT, BOUNDS, MONTH_PINS
from phase866_k_sevenslot_source import ASSETS,PINS
from phase877_k_official_economic_dispatch import load_source_arrays, PASS_OHLC
from phase876_k_funded_ledger import FEE_TIERS,ORDERS,CAPITAL_MODES
from phase1024_p_sevenslot_source import ROOT,PATHS,pinned_p_bars,p_shocks
from phase1026_p_canonical_transport import canonical_p_paths
from phase1027_p_funded_ledger_hourly import simulate_p_hourly

FROZEN_CODE_BLOBS={
    'phase1024_p_sevenslot_source.py':'bcaffb8cfc5331841b885b13cb64ba78eff9751e',
    'phase1025_p_state_aware_governor.py':'c588ac85666b617dff76e9fca8ef2a68e4e1ee4b',
    'phase1026_p_canonical_transport.py':'e2b4c2d0873b68f99f23e776a5abb19d85e5be5f',
    'phase1027_p_funded_ledger_hourly.py':'ee9640b3849848ef1e137c1a96daa78ee4790769',
}
FROZEN_P={
    'P_core_only':'1cec522d2bc11f9cfec08680d99efa9e96aa1db842bdee62cd93a170a584d342',
    'P_full':'f8f0004f96c3a20a2ed12e4eafa54e45e5575f66e22166c55067cb5976d87a41',
    'P_minus_opportunity':'9dc6f4f5666016549e3335f1a22e154747988e04da4b8811265bebe68dfc2db7',
    'P_minus_relative_value':'87704b441218b03ee09cf7c5db9ca2a75cb437eae9eca6cf54c57738800507a6',
    'P_minus_recovery':'4c60fcd2135309dc57caa14a8b9edab1e672cb0230d537c9dbe59b88f50b032a',
}
PASS_POLICY='PASS_100_MARK_100_FUNDING_FOUR_FEB24_DAILY_GAPS_SOURCE_ONLY'
OUT=ROOT/'phase1029_p_training_gate_result.json'


def verify_p_code():
    for name,expected in FROZEN_CODE_BLOBS.items():
        raw=(ROOT/name).read_bytes()
        blob=b'blob '+str(len(raw)).encode()+b'\x00'+raw
        if hashlib.sha1(blob).hexdigest()!=expected:
            raise PermissionError('P_FROZEN_CODE_BLOB_DRIFT_'+name)
    return True


def source_gate():
    verify_p_code()
    o=fresh_ohlc()
    if o.get('decision')!=PASS_OHLC or o.get('vendor_origin_attested') is not True:
        raise PermissionError('P_FRESH_100_OHLC_NOT_ATTESTED')
    for a in ASSETS:
        x=o.get('assets',{}).get(a,{})
        if x.get('sha256')!=PINS[a] or x.get('monthly_archives')!=25 or x.get('hours')!=18288:
            raise PermissionError('P_OHLC_PIN_DRIFT_'+a)
    if fresh_policy()!=0:raise PermissionError('P_MARK_FUNDING_SOURCE_FAILED')
    p=json.loads(POLICY_OUT.read_text())
    expected={'decision':PASS_POLICY,'verified_mark_monthly_archives':100,
              'verified_mark_daily_archives':112,'verified_funding_monthly_archives':100,
              'verified_asset_events':9144,'vendor_archive_checksum_attested':True,
              'historical_pnl_computed':False,'economic_clearance':False,
              'validation_2025_read':False,'holdout_accessed':False,
              'external_benchmarks_used':False,'api_mark_attested':False}
    for k,v in expected.items():
        if type(p.get(k)) is not type(v) or p[k]!=v:
            raise PermissionError('P_SOURCE_POLICY_DRIFT_'+k)
    manifests=p.get('exception_manifests',{})
    if set(manifests)!=set(ASSETS):raise PermissionError('P_MISSING_FEB_MANIFEST')
    for a in ASSETS:
        m=manifests[a];ov=m.get('overlap',{})
        if (m.get('monthly_zip_sha256')!=MONTH_PINS[a] or
            len(m.get('daily_zip_sha256',{}))!=28 or m.get('monthly_rows')!=648 or
            m.get('daily_rows')!=672 or m.get('inserted_daily_rows')!=24 or
            ov.get('shared')!=648 or ov.get('missing_left')!=24 or
            ov.get('missing_right')!=0 or ov.get('different_rows')!=0):
            raise PermissionError('P_FEB_SOURCE_MANIFEST_DRIFT_'+a)
    bounds_sha=hashlib.sha256(BOUNDS.read_bytes()).hexdigest()
    if bounds_sha!=p.get('bounds_csv_sha256'):
        raise PermissionError('P_BOUNDS_SOURCE_DRIFT')
    return {'ohlc':o['decision'],'mark_funding':p['decision'],'bounds_sha256':bounds_sha}


def isolated_arrays():
    with tempfile.TemporaryDirectory(prefix='v98_p_source_') as tmp:
        root=Path(tmp)
        (root/'phase243_clean4_canonical').symlink_to((ROOT/'phase243_clean4_canonical').resolve(),target_is_directory=True)
        (root/'phase797_conservative_training_funding_bounds.csv').symlink_to(BOUNDS.resolve())
        return load_source_arrays(root)


def complete_matrix(paths,arrays,rate,mark,event,years,down,up):
    if tuple(paths)!=PATHS or tuple(FROZEN_P)!=PATHS:raise PermissionError('P_PATH_ORDER_DRIFT')
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
                        r=simulate_p_hourly(paths[name],arrays['open'],arrays['high'],arrays['low'],arrays['close'],
                                            arrays['quote_volume'],rate,mark,event,down,up,fee,
                                            order=order,mode=mode,years=years,require_full_sample=True)
                    except Exception as exc:
                        r={'survived':False,'reason':type(exc).__name__+': '+str(exc)[:200]}
                    cases[name][tier][order][mode]=r
                    if not r.get('survived',False):
                        failures.append({'path':name,'fee_tier':tier,'order':order,'mode':mode,
                                         'reason':r.get('reason'),'breach_index':r.get('breach_index')})
    if count!=90:raise AssertionError('P_INCOMPLETE_90_CELL_MATRIX')
    return {'cells_attempted':count,'cells_survived':count-len(failures),'failures':failures,'cases':cases}


def growth_gate(matrix):
    if matrix['cells_attempted']!=90 or matrix['failures']:
        return {'passed':False,'reason':'incomplete_or_failed_survival','failed_cells':len(matrix['failures'])}
    for name in PATHS:
        for tier in FEE_TIERS:
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    f=matrix['cases'][name][tier][order][mode].get('folds',{})
                    if set(f)!={'2023','2024'} or f['2023'].get('days')!=365 or f['2024'].get('days')!=366:
                        return {'passed':False,'reason':'incomplete_chronological_folds'}
    failures=[];edges={}
    for year in ('2023','2024'):
        for tier in ('base','severe'):
            for order in ORDERS:
                for mode in CAPITAL_MODES:
                    key='/'.join((year,tier,order,mode))
                    full=matrix['cases']['P_full'][tier][order][mode]['folds'][year]['log_wealth']
                    if not math.isfinite(full) or full<=0:
                        failures.append({'cell':key,'reason':'nonpositive_full_growth','value':full})
                    marginal={}
                    for name in PATHS:
                        if name=='P_full':continue
                        alt=matrix['cases'][name][tier][order][mode]['folds'][year]['log_wealth']
                        diff=full-alt
                        marginal[name]=diff
                        if not math.isfinite(diff) or diff<=0:
                            failures.append({'cell':key,'reason':'nonpositive_marginal','path':name,'value':diff})
                    edges[key]={'P_full_log_wealth':full,'marginal':marginal}
    return {'passed':not failures,'reason':'training_only_pending_separate_validation' if not failures else 'failed_growth_or_marginal',
            'failures':failures,'edges':edges}


def run(execute=False):
    out={'phase':1029,'decision':'BLOCKED_BEFORE_PNL','historical_pnl_computed':False,
         'ledger_invocations':0,'promotion_eligible':False,'validation_2025_read':False,
         'holdout_accessed':False,'external_benchmarks_used':False}
    try:
        out['source_receipts']=source_gate()
        paths,receipt=canonical_p_paths()
        if receipt['paths_sha256']!=FROZEN_P:raise PermissionError('P_FIVE_CANONICAL_TARGET_HASH_DRIFT')
        out['canonical_target_sha256']=receipt['paths_sha256']
        if not execute:
            out['decision']='PASS_P_SOURCE_ONLY_PREFLIGHT_NO_ECONOMICS'
        else:
            arrays,rate,mark,event,years=isolated_arrays()
            op,hi,lo,cl,_=pinned_p_bars(ROOT/'phase243_clean4_canonical')
            down,up=p_shocks(op,hi,lo)
            matrix=complete_matrix({k:v.to_numpy(float) for k,v in paths.items()},arrays,rate,mark,event,years,down,up)
            out['historical_pnl_computed']=True
            out['ledger_invocations']=matrix['cells_attempted']
            out['matrix']=matrix
            out['growth_gate']=growth_gate(matrix)
            out['decision']='PASS_P_TRAINING_PENDING_2025_VALIDATION' if out['growth_gate']['passed'] else 'REJECT_P_TRAINING_NO_RESCUE'
    except Exception as exc:
        out['decision']='BLOCKED_AFTER_PNL_NO_PROMOTION' if out['historical_pnl_computed'] else 'BLOCKED_BEFORE_PNL'
        out['reason']=type(exc).__name__+': '+str(exc)[:350]
    OUT.write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'phase':1029,'decision':out['decision'],'historical_pnl_computed':out['historical_pnl_computed'],
                      'ledger_invocations':out['ledger_invocations'],'cells_survived':out.get('matrix',{}).get('cells_survived'),
                      'reason':out.get('reason')},sort_keys=True))
    return 0 if out['decision'].startswith('PASS_') else 2


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true')
    args=p.parse_args()
    raise SystemExit(run(args.execute))
