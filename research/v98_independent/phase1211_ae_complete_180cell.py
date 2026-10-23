#!/usr/bin/env python3
"""V98 AE full seven-slot 180-cell causal-risk SYNTHETIC integration; no historical PnL."""
from __future__ import annotations
import itertools
import json
import numpy as np
import pandas as pd
from phase1205_ae_breakout_source import ASSETS,START,ae_breakout_source
from phase1206_ae_stress_recovery import AEStressMachine
from phase1207_ae_growth_allocator import AEAllocator
from phase1209_ae_prior_risk_inputs import ae_prior_risk
from phase1210_ae_actual_open_executor import execute_hour,FEES,ORDERS

PATHS=('AE_core_only','AE_full','AE_minus_opportunity',
       'AE_minus_relative_value','AE_minus_stress')
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


def one_cell(path,mode,fee,order,frames,marks,slots,risk):
    if path not in PATHS or mode not in MODES or fee not in FEES or order not in ORDERS:
        raise ValueError('AE1211_CELL_KEY')
    o,h,l,c,q,r,e=(f.to_numpy(float) for f in frames)
    mark_low,mark_high=marks
    core,opportunity,rv,router=slots
    capital=MODES[mode]
    cash=capital
    units=np.zeros(4)
    nav=capital
    desired=np.zeros(4)
    alloc=AEAllocator()
    stress=AEStressMachine()
    turnover=fees=slippage=funding=0.
    fractions=[]
    active={'growth':0,'opportunity':0,'relative_value':0,'stress':0}
    for t in range(len(c)):
        if t>=720:
            try:
                result=execute_hour(
                    prior_close=c[t-1],opening=o[t],high=h[t],low=l[t],
                    closing=c[t],cash=cash,old_units=units,
                    desired_weights=desired,down=risk['down'][t],
                    up=risk['up'][t],funding_bound=risk['funding_bound'][t],
                    prior_quote=risk['prior_quote'][t],
                    min_quote=risk['min_quote'][t],fee=fee,
                    funding_rate=r[t],mark_low=mark_low[t],mark_high=mark_high[t],
                    funding_event=e[t],order=order)
            except Exception as exc:
                raise ValueError('AE1211_T'+str(t)+'_'+str(exc)) from exc
            cash,units,nav=result['cash'],result['units'],result['equity']
            turnover+=result['turnover']
            fees+=result['fees']
            slippage+=result['slippage']
            funding+=result['funding_cash_delta']
            fractions.append(result['fraction'])
            if not np.isclose(cash+units@c[t],nav,atol=1e-7,rtol=0):
                raise ValueError('AE1211_NAV_RECONCILIATION')
        market_log=float(np.log(c[t]/c[t-1]).mean()) if t else 0.
        hedge=stress.step(nav,market_log)
        if t>=240:
            g=core[t].copy()
            op=opportunity[t].copy()
            rel=rv[t].copy()
            if path=='AE_core_only':
                op[:]=0;rel[:]=0;hedge[:]=0
            if path=='AE_minus_opportunity':op[:]=0
            if path=='AE_minus_relative_value':rel[:]=0
            if path=='AE_minus_stress':hedge[:]=0
            matrix=np.vstack((g,op,rel,hedge))
            for name,x in zip(active,matrix):
                active[name]+=int(np.any(x))
            completed_ret=c[t]/c[t-1]-1
            desired,_=alloc.step(completed_ret,r[t],e[t],matrix,router[t])
    return {'fixture':'crisis' if np.any(c[810]/c[809]<.8) else 'benign',
        'path':path,'mode':mode,'fee':fee,'order':order,'passed':True,
        'synthetic_only':True,'historical_system_pnl_computed':False,
        'hours_executed':len(fractions),'synthetic_final_nav':float(nav),
        'synthetic_turnover':turnover,'synthetic_fees':fees,
        'synthetic_slippage':slippage,'synthetic_funding':funding,
        'active_hours':active,
        'nonzero_execution_fraction':float(np.mean(np.asarray(fractions)>0))}


def run():
    cells=[]
    for crisis in (False,True):
        frames,marks=fixture(crisis=crisis)
        slots=ae_breakout_source(*frames)
        risk=ae_prior_risk(*frames)
        for path,mode,fee,order in itertools.product(PATHS,MODES,FEES,ORDERS):
            try:
                cells.append(one_cell(path,mode,fee,order,frames,marks,slots,risk))
            except Exception as exc:
                cells.append({'fixture':'crisis' if crisis else 'benign',
                    'path':path,'mode':mode,'fee':fee,'order':order,'passed':False,
                    'reason':type(exc).__name__+': '+str(exc),
                    'historical_system_pnl_computed':False})
    full=next((x for x in cells if x['fixture']=='crisis' and
        x['path']=='AE_full' and x['mode']=='immediate' and
        x['fee']=='base' and x['order']=='carried_before_fill'),{})
    passed=(len(cells)==180 and all(x['passed'] for x in cells) and
            full.get('active_hours',{}).get('stress',0)>0)
    return {'phase':1211,'decision':'PASS_AE_180_CAUSAL_SYNTHETIC_NOT_ECONOMIC'
        if passed else 'REJECT_AE_180_CAUSAL_SYNTHETIC_NO_PNL',
        'historical_system_pnl_computed':False,'validation_2025_read':False,
        'external_benchmarks_used':False,'cells':cells}


if __name__=='__main__':
    r=run()
    print(json.dumps({'decision':r['decision'],
        'passed':sum(x['passed'] for x in r['cells']),
        'failed':[{k:x[k] for k in ('fixture','path','mode','fee','order','reason')}
                  for x in r['cells'] if not x['passed']][:10]},sort_keys=True))
    raise SystemExit(0 if r['decision'].startswith('PASS_') else 2)
