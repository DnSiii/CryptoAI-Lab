#!/usr/bin/env python3
"""AD strict causal risk 180-cell structural audit; no historical PnL."""
from __future__ import annotations
import itertools
import json
import numpy as np
from phase1198_ad_complete_synthetic import fixture,source_slots,PATHS,MODES,FEES,ORDERS
from phase1200_ad_crisis_90cell import crisis_fixture
from phase1201_ad_causal_risk_inputs import causal_risk
from phase1193_ad_stateful_stress import StressMachine
from phase1195_ad_multiplicative_allocator import ADAllocator,sleeve_matrix
from phase1197_ad_actual_open_executor import execute_hour

def one_cell_causal(path,mode,fee,order,frames,marks,slots,risk):
    if path not in PATHS or mode not in MODES or fee not in FEES or order not in ORDERS:
        raise ValueError('AD1198_CELL_KEY')
    o,h,l,c,q,r,e=(f.to_numpy(float) for f in frames)
    mark_low,mark_high=marks
    core,router,opp,rv=slots
    capital=MODES[mode]
    cash=capital
    units=np.zeros(4)
    alloc=ADAllocator()
    stress=StressMachine()
    desired=np.zeros(4)
    nav=capital
    turnover=fees=funding=0.
    alphas=[]
    active={'growth':0,'opportunity':0,'relative_value':0,'stress':0}
    for t in range(len(c)):
        if t>=720:
            try:
                res=execute_hour(prior_close=c[t-1],opening=o[t],high=h[t],low=l[t],
                closing=c[t],cash=cash,old_units=units,desired_weights=desired,
                down=risk['down'][t],up=risk['up'][t],
                funding_bound=risk['funding_bound'][t],prior_quote=risk['prior_quote'][t],
                min_quote=risk['min_quote'][t],fee=fee,
                funding_rate=r[t],mark_low=mark_low[t],mark_high=mark_high[t],
                funding_event=e[t],order=order)
            except Exception as exc:
                raise ValueError('AD1202_T'+str(t)+'_'+str(exc)) from exc
            cash,units,nav=res['cash'],res['units'],res['equity']
            turnover+=res['turnover'];fees+=res['fees'];funding+=res['funding_cash_delta']
            alphas.append(res['alpha'])
            if not np.isclose(cash+units@c[t],nav,atol=1e-6,rtol=0):
                raise ValueError('AD1198_NAV_RECONCILIATION')
        hedge=stress.step(nav,float(np.log(c[t]).mean()))
        if t>=336:
            g=core[t]
            op=opp[t].astype(float)
            rel=rv[t].copy()
            if path=='AD_core_only':op[:]=0;rel[:]=0;hedge[:]=0
            if path=='AD_minus_opportunity':op[:]=0
            if path=='AD_minus_relative_value':rel[:]=0
            if path=='AD_minus_stress':hedge[:]=0
            matrix=sleeve_matrix(g,op,rel,hedge)
            for name,x in zip(active,matrix):
                active[name]+=int(np.any(x))
            prior_return=c[t]/c[t-1]-1
            desired,_=alloc.step(prior_return,r[t],e[t],matrix,router[t])
    return {'path':path,'mode':mode,'fee':fee,'order':order,
        'passed':True,'synthetic_only':True,'historical_system_pnl_computed':False,
        'hours_executed':len(alphas),'synthetic_final_nav':float(nav),
        'synthetic_turnover':turnover,'synthetic_fees':fees,
        'synthetic_funding':funding,'active_hours':active,
        'nonzero_execution_fraction':float(np.mean(np.asarray(alphas)>0))}


def run():
    cells=[]
    for name in ('benign','crisis'):
        if name=='benign':
            frames,*m=fixture(900);marks=tuple(m)
        else:
            frames,marks=crisis_fixture()
        slots=source_slots(frames)
        risk=causal_risk(*frames)
        for path,mode,fee,order in itertools.product(PATHS,MODES,FEES,ORDERS):
            try:
                cell=one_cell_causal(path,mode,fee,order,frames,marks,slots,risk)
                cell['fixture']=name
                cells.append(cell)
            except Exception as exc:
                cells.append({'fixture':name,'path':path,'mode':mode,'fee':fee,
                    'order':order,'passed':False,
                    'reason':type(exc).__name__+': '+str(exc),
                    'historical_system_pnl_computed':False})
    crisis=next((c for c in cells if c['fixture']=='crisis' and c['path']=='AD_full'
        and c['mode']=='immediate' and c['fee']=='base' and
        c['order']=='carried_before_fill'),{})
    passed=len(cells)==180 and all(c['passed'] for c in cells) and (
        crisis.get('active_hours',{}).get('stress',0)>0)
    return {'phase':1202,'decision':'PASS_AD_180_CAUSAL_RISK_SYNTHETIC_NOT_ECONOMIC'
        if passed else 'REJECT_AD_CAUSAL_RISK_SYNTHETIC_NO_PNL',
        'historical_system_pnl_computed':False,'validation_2025_read':False,
        'external_benchmarks_used':False,'cells':cells}


if __name__=='__main__':
    r=run()
    print(json.dumps({'decision':r['decision'],'passed':sum(c['passed'] for c in r['cells']),
        'failures':[{k:c[k] for k in ('fixture','path','mode','fee','order','reason')}
                    for c in r['cells'] if not c['passed']][:12]},sort_keys=True))
    raise SystemExit(0 if r['decision'].startswith('PASS_') else 2)
