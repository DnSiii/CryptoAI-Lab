#!/usr/bin/env python3
"""V98 AF full seven-slot 180-cell causal SYNTHETIC integration; no historical PnL."""
from __future__ import annotations
import itertools
import json
import numpy as np
import pandas as pd
from phase1214_af_dual_ewma_core import ASSETS,START,af_growth_source
from phase1215_af_synchronized_acceleration import af_opportunity_source
from phase1216_af_long_only_rv import af_relative_value_source
from phase1217_af_prefunded_cash import AFCashStress,NORMAL_CASH
from phase1218_af_breadth_router import af_router_source
from phase1219_af_robust_growth_allocator import AFGrowthAllocator
from phase1221_af_actual_ledger import execute_hour,FEES,ORDERS
from phase1222_af_prior_risk import af_prior_risk

PATHS=('AF_core_only','AF_full','AF_minus_opportunity',
       'AF_minus_relative_value','AF_minus_stress')
MODES={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}


def fixture(crisis=False,n=900):
    idx=pd.date_range(START,periods=n,freq='h')
    t=np.arange(n,dtype=float)
    trends=np.array([.00040,.00050,.00035,-.00040])
    close=100*np.exp(t[:,None]*trends[None,:]+
                      .002*np.sin(t[:,None]/np.array([17.,19.,23.,29.])))
    if crisis:
        close[810:]*=.55
        close[850:]*=1.80
    opening=np.vstack((close[0],close[:-1]))
    high=np.maximum(opening,close)*1.0001
    low=np.minimum(opening,close)*.9999
    quote=np.full_like(close,1e12)
    rate=np.zeros_like(close)
    event=np.zeros_like(close)
    event[::8]=1
    rate[::8]=np.array([.0001,-.0001,.00015,-.00015])
    frames=[pd.DataFrame(a,index=idx,columns=ASSETS)
            for a in (opening,high,low,close,quote,rate,event)]
    marks=(np.where(event!=0,close*.99,np.nan),
           np.where(event!=0,close*1.01,np.nan))
    return frames,marks


def one_cell(path,mode,fee,order,frames,marks,slots,risk,fixture_name):
    if path not in PATHS or mode not in MODES or fee not in FEES or order not in ORDERS:
        raise ValueError('AF1223_CELL_KEY')
    o,h,l,c,q,r,e=(f.to_numpy(float) for f in frames)
    mark_low,mark_high=marks
    growth,opportunity,rv,router=slots
    capital=MODES[mode]
    cash=capital
    units=np.zeros(4)
    nav=capital
    desired=np.zeros(4)
    alloc=AFGrowthAllocator()
    stress=AFCashStress()
    turnover=fees=slippage=funding=0.
    fractions=[]
    active={'growth':0,'opportunity':0,'relative_value':0,'stress_cash':0}
    for t in range(len(c)):
        if t>=720:
            try:
                res=execute_hour(prior_close=c[t-1],opening=o[t],high=h[t],
                    low=l[t],closing=c[t],cash=cash,old_units=units,
                    desired_weights=desired,down=risk['down'][t],
                    up=risk['up'][t],funding_bound=risk['funding_bound'][t],
                    prior_quote=risk['prior_quote'][t],
                    min_quote=risk['min_quote'][t],fee=fee,
                    funding_rate=r[t],mark_low=mark_low[t],mark_high=mark_high[t],
                    funding_event=e[t],order=order)
            except Exception as exc:
                raise ValueError('AF1223_T'+str(t)+'_'+str(exc)) from exc
            cash,units,nav=res['cash'],res['units'],res['equity']
            turnover+=res['turnover'];fees+=res['fees']
            slippage+=res['slippage'];funding+=res['funding_cash_delta']
            fractions.append(res['fraction'])
            if cash<-1e-9 or np.any(units<0) or not np.isclose(
                    cash+units@c[t],nav,atol=1e-7,rtol=0):
                raise ValueError('AF1223_CASH_NAV_RECONCILIATION')
        market_log=float(np.log(c[t]/c[t-1]).mean()) if t else 0.
        reserve=stress.step(nav,market_log)
        if t>=336:
            g=growth[t].copy()
            op=opportunity[t].copy()
            rel=rv[t].copy()
            if path=='AF_core_only':
                op[:]=0;rel[:]=0;reserve=NORMAL_CASH
            if path=='AF_minus_opportunity':op[:]=0
            if path=='AF_minus_relative_value':rel[:]=0
            if path=='AF_minus_stress':reserve=NORMAL_CASH
            matrix=np.vstack((g,op,rel))
            active['growth']+=int(np.any(g))
            active['opportunity']+=int(np.any(op))
            active['relative_value']+=int(np.any(rel))
            active['stress_cash']+=int(reserve>NORMAL_CASH)
            completed=c[t]/c[t-1]-1
            desired,_=alloc.step(completed,r[t],e[t],matrix,router[t],reserve)
    return {'fixture':fixture_name,'path':path,'mode':mode,'fee':fee,'order':order,
            'passed':True,'synthetic_only':True,
            'historical_system_pnl_computed':False,
            'hours_executed':len(fractions),
            'synthetic_final_nav':float(nav),'synthetic_turnover':turnover,
            'synthetic_fees':fees,'synthetic_slippage':slippage,
            'synthetic_funding':funding,'active_hours':active,
            'nonzero_execution_fraction':float(np.mean(np.asarray(fractions)>0))}


def run():
    cells=[]
    for crisis in (False,True):
        name='crisis' if crisis else 'benign'
        frames,marks=fixture(crisis=crisis)
        slots=(af_growth_source(*frames),af_opportunity_source(*frames),
               af_relative_value_source(*frames),af_router_source(*frames))
        risk=af_prior_risk(*frames)
        for path,mode,fee,order in itertools.product(PATHS,MODES,FEES,ORDERS):
            try:
                cells.append(one_cell(path,mode,fee,order,frames,marks,
                                      slots,risk,name))
            except Exception as exc:
                cells.append({'fixture':name,'path':path,'mode':mode,
                    'fee':fee,'order':order,'passed':False,
                    'reason':type(exc).__name__+': '+str(exc),
                    'historical_system_pnl_computed':False})
    full=next((x for x in cells if x['fixture']=='crisis' and
        x['path']=='AF_full' and x['mode']=='immediate' and
        x['fee']=='base' and x['order']=='carried_before_fill'),{})
    passed=(len(cells)==180 and all(x['passed'] for x in cells) and
            full.get('active_hours',{}).get('stress_cash',0)>0)
    return {'phase':1223,'decision':'PASS_AF_180_CAUSAL_SYNTHETIC_NOT_ECONOMIC'
        if passed else 'REJECT_AF_180_CAUSAL_SYNTHETIC_NO_PNL',
        'historical_system_pnl_computed':False,'validation_2025_read':False,
        'external_benchmarks_used':False,'cells':cells}


if __name__=='__main__':
    r=run()
    print(json.dumps({'decision':r['decision'],
        'passed':sum(x['passed'] for x in r['cells']),
        'failures':[{k:x[k] for k in ('fixture','path','mode','fee','order','reason')}
                    for x in r['cells'] if not x['passed']][:10]},sort_keys=True))
    raise SystemExit(0 if r['decision'].startswith('PASS_') else 2)
