#!/usr/bin/env python3
"""V98 AO net-carry preregistered two-OS 90-cell economic reconciliation; artifact-only."""
from __future__ import annotations
import argparse
import glob
import json
import math
from collections import defaultdict

PATHS = ('AO_core_only','AO_full','AO_minus_opportunity',
         'AO_minus_RV','AO_minus_stress')
MODES = ('immediate','capacity_1m','capacity_10m')
FEES = ('base','severe','supersevere')
ORDERS = ('carried_before_fill','new_after_fill')
GRID = {(m,f,o) for m in MODES for f in FEES for o in ORDERS}
MONEY = {'initial_nav','final_nav','min_nav','turnover','fees',
         'slippage','funding','start_nav','end_nav'}

def compare(a,b,path,deltas,failures):
    if type(a) is not type(b):
        failures.append((path,'type'));return
    if isinstance(a,dict):
        if set(a)!=set(b):
            failures.append((path,'keys',sorted(set(a)^set(b))));return
        for k in sorted(a):
            compare(a[k],b[k],path+'.'+k,deltas,failures)
    elif isinstance(a,list):
        if len(a)!=len(b):
            failures.append((path,'length'));return
        for i,(x,y) in enumerate(zip(a,b)):
            compare(x,y,path+'.'+str(i),deltas,failures)
    elif isinstance(a,float):
        key=path.rsplit('.',1)[-1]
        tolerance=(max(1e-8,1e-10*max(abs(a),abs(b),1.))
                   if key in MONEY else 1e-10)
        difference=abs(a-b)
        deltas.append((difference/tolerance,path,difference,tolerance))
        if not(math.isfinite(a) and math.isfinite(b)
               and difference<=tolerance):
            failures.append((path,'numeric',a,b,difference,tolerance))
    elif a!=b:
        failures.append((path,'value',a,b))

def run(root):
    files=sorted(glob.glob(root+'/*/*.json'))
    errors=[]
    groups=defaultdict(dict)
    for path in files:
        parts=path.split('/')
        artifact=parts[-2]
        os=('ubuntu-22.04' if 'ubuntu-22.04' in artifact else
            'ubuntu-24.04' if 'ubuntu-24.04' in artifact else '')
        receipt=json.load(open(path))
        name=receipt.get('path')
        if os not in ('ubuntu-22.04','ubuntu-24.04') or name not in PATHS or os in groups[name]:
            errors.append(('artifact',path))
        else:
            groups[name][os]=receipt
    if len(files)!=10 or set(groups)!=set(PATHS):
        errors.append(('inventory',len(files),sorted(groups)))
    deltas=[]
    representative={}
    for name in PATHS:
        g=groups.get(name,{})
        if set(g)!={'ubuntu-22.04','ubuntu-24.04'}:
            errors.append(('os',name,sorted(g)))
            continue
        a,b=g['ubuntu-22.04'],g['ubuntu-24.04']
        compare(a,b,name,deltas,errors)
        representative[name]=a
    cells={}
    for name,a in representative.items():
        raw=a['cells']
        mapping={(c['mode'],c['fee'],c['order']):c for c in raw}
        if len(raw)!=18 or set(mapping)!=GRID:
            errors.append(('grid',name,len(raw),len(mapping)))
        cells[name]=mapping
    total=sum(len(x) for x in cells.values())
    passed=sum(bool(c['passed']) for d in cells.values() for c in d.values())
    full=cells.get('AO_full',{})
    base=full.get(('immediate','base','carried_before_fill'),{})
    growth={}
    for fee in ('base','severe'):
        for order in ORDERS:
            key=('immediate',fee,order)
            c=full.get(key,{})
            growth['|'.join(key)]=bool(c.get('passed') and all(
                c['annual'][yr]['net_log_growth']>0 for yr in ('2023','2024')))
    marginal={}
    for sleeve,removed in (('Opportunity','AO_minus_opportunity'),
                            ('RV','AO_minus_RV'),('Stress','AO_minus_stress')):
        marginal[sleeve]={}
        for key,c in full.items():
            other=cells.get(removed,{}).get(key,{})
            if not c.get('passed') or not other.get('passed'):continue
            marginal[sleeve]['|'.join(key)]={yr:(
                c['annual'][yr]['net_log_growth']-
                other['annual'][yr]['net_log_growth'])
                for yr in ('2023','2024')}
    sleeve_gates={s:all(marginal[s].get(key,{}).get(yr,float('-inf'))>0
                         for key in growth for yr in ('2023','2024'))
                  for s in marginal}
    reproducible=not errors and len(representative)==5 and total==90
    if not reproducible:
        decision='BLOCKED_AO_CROSS_OS_REPRODUCIBILITY'
    elif passed!=90:
        decision='REJECT_AO_HISTORICAL_SURVIVAL'
    elif not all(growth.values()) or not all(sleeve_gates.values()):
        decision='REJECT_AO_HISTORICAL_GROWTH_OR_MARGINAL'
    else:
        decision='PASS_AO_MECHAOICAL_AOD_MINIMUM_GROWTH_NEEDS_INDEPENDENT_REVIEW'
    return {
        'architecture':'AO','historical_training_only':True,
        'validation_2025_read':False,'external_benchmarks_used':False,
        'source_manifest_sha256':representative.get('AO_full',{}).get('source_manifest_sha256'),
        'cross_os_reproducible':reproducible,
        'cross_os_errors':errors[:30],
        'max_normalized_numeric_deltas':sorted(deltas,reverse=True)[:20],
        'cells_total':total,'cells_survived':passed,
        'full_10k_base':base or None,
        'growth_gates_10k':growth,
        'marginal_log_growth':marginal,
        'sleeve_gates_10k':sleeve_gates,
        'decision':decision}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',default='receipts')
    p.add_argument('--output',default='ao_economic_summary.json')
    args=p.parse_args()
    result=run(args.root)
    with open(args.output,'w') as f:
        json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)
    print('AO90_CROSS_OS',result['cross_os_reproducible'],
          'max_deltas',result['max_normalized_numeric_deltas'][:5])
    print('AO90_SURVIVAL',result['cells_survived'],'/',result['cells_total'])
    if result['full_10k_base']:
        c=result['full_10k_base']
        print('AO90_FULL_10K_BASE',json.dumps({
            'two_year_cagr':c['two_year_cagr'],
            '2023_cagr':c['annual']['2023']['annualized_cagr'],
            '2024_cagr':c['annual']['2024']['annualized_cagr'],
            'max_dd':c['max_drawdown'],'fees':c['fees'],
            'slippage':c['slippage'],'funding':c['funding']},
            sort_keys=True))
    print('AO90_GROWTH_GATES',result['growth_gates_10k'])
    print('AO90_SLEEVE_GATES',result['sleeve_gates_10k'])
    print('AO90_DECISION',result['decision'])
    raise SystemExit(2 if not result['cross_os_reproducible'] else 0)
