#!/usr/bin/env python3
"""BL independent artifact-only arithmetic and economic gate auditor.
Does not import BL engine, allocator, reconciliation, or source code.
Checks 10 original receipts, annual/total wealth identities, costs and gates.
Native funding-event arithmetic requires trade-level cashflow receipts and is
NOT independently rederived here; provenance is pinned by official loader.
"""
from __future__ import annotations
import argparse,glob,json,math
from pathlib import Path
PATHS=('BL_core_only','BL_full','BL_minus_opportunity','BL_minus_RV','BL_minus_stress')
OS=('ubuntu-22.04','ubuntu-24.04')
CAPITAL={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}
FEES={'base':(.0005,.0005),'severe':(.002,.003),'supersevere':(.005,.010)}
ORDERS=('carried_before_fill','new_after_fill')
def close(a,b):
    return math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-5)
def audit(root):
    receipts={};errors=[]
    for file in glob.glob(str(Path(root)/'*'/'*.json')):
        a=json.load(open(file))
        name=a.get('path')
        os=next((s for s in OS if s in str(file)),'')
        if name not in PATHS or not os or (name,os) in receipts:
            errors.append(('BAD_RECEIPT',str(file)));continue
        receipts[name,os]=a
    if set(receipts)!={(p,o) for p in PATHS for o in OS}:
        errors.append(('INCOMPLETE',len(receipts)))
    manifest={a.get('source_manifest_sha256') for a in receipts.values()}
    if len(manifest)!=1 or None in manifest:errors.append(('MANIFEST_MISMATCH',))
    count=0;survival=0;cells={}
    for (name,os),a in receipts.items():
        for c in a.get('cells',[]):
            count+=1;survival+=bool(c.get('passed'))
            key=(name,os,c.get('mode'),c.get('fee'),c.get('order'))
            if key in cells:errors.append(('DUPLICATE_CELL',key))
            cells[key]=c
            if not c.get('passed'):continue
            mode,fee,order=key[2:]
            if mode not in CAPITAL or fee not in FEES or order not in ORDERS:
                errors.append(('BAD_GRID',key));continue
            if not close(c['initial_nav'],CAPITAL[mode]):
                errors.append(('CAPITAL',key))
            if not close(c['final_nav'],c['annual']['2024']['end_nav']):
                errors.append(('FINAL_NAV',key))
            if not close(c['annual']['2023']['end_nav'],c['annual']['2024']['start_nav']):
                errors.append(('YEAR_BOUNDARY',key))
            if not close(c['annual']['2023']['start_nav'],c['initial_nav']):
                errors.append(('YEAR_START',key))
            if not close(c['net_log_growth'],math.log(c['final_nav']/c['initial_nav'])):
                errors.append(('LOG_IDENTITY',key))
            if not close(c['two_year_cagr'],(c['final_nav']/c['initial_nav'])**(365.25/731)-1):
                errors.append(('CAGR_IDENTITY',key))
            if not close(c['net_total_return'],c['final_nav']/c['initial_nav']-1):
                errors.append(('RETURN_IDENTITY',key))
            for y,duration in (('2023',365),('2024',366)):
                x=c['annual'][y]
                if not close(x['net_log_growth'],math.log(x['end_nav']/x['start_nav'])):
                    errors.append(('ANNUAL_LOG',key,y))
                if not close(x['annualized_cagr'],(x['end_nav']/x['start_nav'])**(365.25/duration)-1):
                    errors.append(('ANNUAL_CAGR',key,y))
                if x['total_utc_days']!=duration or not 0<=x['positive_utc_days']<=duration:
                    errors.append(('UTC_DAYS',key,y))
            if not close(c['fees'],c['turnover']*FEES[fee][0]):
                errors.append(('FEE_IDENTITY',key))
            if not close(c['slippage'],c['turnover']*FEES[fee][1]):
                errors.append(('SLIPPAGE_IDENTITY',key))
            if not 0<=c['max_drawdown']<1 or c['min_nav']<=0:
                errors.append(('EQUITY_BOUNDS',key))
    expected={(p,o,m,f,d) for p in PATHS for o in OS for m in CAPITAL for f in FEES for d in ORDERS}
    if set(cells)!=expected:errors.append(('MISSING_CELLS',len(expected-set(cells))))
    growth={};marginal={}
    for os in OS:
        for fee in ('base','severe'):
            for order in ORDERS:
                key=(os,'immediate',fee,order)
                full=cells.get(('BL_full',)+key,{})
                growth[str(key)]=bool(full.get('passed') and all(
                    full['annual'][y]['net_log_growth']>0 for y in ('2023','2024')))
                for sleeve,minus in (('opportunity','BL_minus_opportunity'),
                                     ('relative_value','BL_minus_RV'),
                                     ('stress_recovery','BL_minus_stress')):
                    other=cells.get((minus,)+key,{})
                    if full.get('passed') and other.get('passed'):
                        for y in ('2023','2024'):
                            marginal[str((sleeve,)+key+(y,))]=(
                                full['annual'][y]['net_log_growth']-
                                other['annual'][y]['net_log_growth'])
    marg_pass=bool(len(marginal)==3*2*2*2*2 and all(v>0 for v in marginal.values()))
    gate=(not errors and count==180 and survival==180 and
          all(growth.values()) and marg_pass)
    return {'architecture':'BL','original_receipts':len(receipts),
            'cross_os_cells_checked':count,'cross_os_survival':survival,
            'source_manifest_sha256':next(iter(manifest)) if len(manifest)==1 else None,
            'independent_arithmetic_errors':errors[:30],
            'annual_growth_gates':growth,'marginal_log_growth':marginal,
            'marginal_pass':marg_pass,
            'decision':('PASS_BL_TRAINING_ONLY_NEEDS_SEPARATE_VALIDATION' if gate
                        else 'REJECT_OR_BLOCK_BL_TRAINING'),
            'native_funding_independently_rederived':False,
            'validation_2025_read':False,'external_benchmarks_used':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',default='receipts')
    p.add_argument('--output',default='bg90_independent_arithmetic.json')
    a=p.parse_args()
    result=audit(a.root)
    Path(a.output).write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))
    print('BL_INDEPENDENT_AUDIT',result['decision'],result['cross_os_survival'],
          '/',result['cross_os_cells_checked'],result['independent_arithmetic_errors'][:5])
    raise SystemExit(2 if result['independent_arithmetic_errors'] else 0)
