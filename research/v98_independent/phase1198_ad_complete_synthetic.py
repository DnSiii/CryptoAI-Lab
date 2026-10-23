#!/usr/bin/env python3
"""AD complete seven-slot 90-cell synthetic integration, NOT historical PnL."""
from __future__ import annotations
import itertools
import json
import numpy as np
import pandas as pd
from phase1189_ad_online_core_router import ASSETS,online_core_router
from phase1191_ad_funding_event_opportunity import opportunity_intents
from phase1192_ad_covariance_neutral_rv import relative_value_intents
from phase1193_ad_stateful_stress import StressMachine
from phase1195_ad_multiplicative_allocator import ADAllocator,sleeve_matrix
from phase1197_ad_actual_open_executor import execute_hour,FEES,ORDERS

PATHS=('AD_core_only','AD_full','AD_minus_opportunity',
       'AD_minus_relative_value','AD_minus_stress')
MODES={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}


def fixture(n=860):
    idx=pd.date_range('2022-12-01T00:00:00Z',periods=n,freq='h')
    t=np.arange(n,dtype=float)
    close=np.column_stack([100*np.exp((.00010+.00004*j)*t+
        .009*np.sin(t/(17+4*j))) for j in range(4)])
    close[800:,0]*=1.04
    opening=np.vstack([close[0],close[:-1]])
    high=np.maximum(opening,close)*1.003
    low=np.minimum(opening,close)*.997
    quote=np.full_like(close,1e12)
    rate=np.zeros_like(close)
    event=np.zeros_like(close)
    event[::8]=1
    rate[::8]=.0001
    rate[800,0]=.005
    frames=[pd.DataFrame(a,index=idx,columns=ASSETS)
            for a in (opening,high,low,close,quote,rate,event)]
    mark_low=np.where(event!=0,close*.99,np.nan)
    mark_high=np.where(event!=0,close*1.01,np.nan)
    return frames,mark_low,mark_high


def source_slots(frames):
    core,router=online_core_router(*frames)
    opportunity=opportunity_intents(*frames)
    rv=relative_value_intents(*frames)
    return core,router,opportunity,rv


def one_cell(path,mode,fee,order,frames,marks,slots):
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
            res=execute_hour(prior_close=c[t-1],opening=o[t],high=h[t],low=l[t],
                closing=c[t],cash=cash,old_units=units,desired_weights=desired,
                down=np.full(4,.25),up=np.full(4,.30),
                funding_bound=np.full(4,.005),prior_quote=q[t-1],
                min_quote=q[t-336:t].min(axis=0),fee=fee,
                funding_rate=r[t],mark_low=mark_low[t],mark_high=mark_high[t],
                funding_event=e[t],order=order)
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
    frames,*marks=fixture()
    slots=source_slots(frames)
    cells=[]
    for path,mode,fee,order in itertools.product(PATHS,MODES,FEES,ORDERS):
        try:
            cells.append(one_cell(path,mode,fee,order,frames,marks,slots))
        except Exception as exc:
            cells.append({'path':path,'mode':mode,'fee':fee,'order':order,
                          'passed':False,'reason':type(exc).__name__+': '+str(exc),
                          'historical_system_pnl_computed':False})
    receipt={'phase':1198,'decision':'PASS_AD_90_SYNTHETIC_CELLS_NOT_ECONOMIC'
             if len(cells)==90 and all(x['passed'] for x in cells)
             else 'REJECT_AD_SYNTHETIC_INTEGRATION_NO_PNL',
             'historical_system_pnl_computed':False,'validation_2025_read':False,
             'external_benchmarks_used':False,'cells':cells}
    return receipt


if __name__=='__main__':
    receipt=run()
    print(json.dumps({'decision':receipt['decision'],
        'passed':sum(c['passed'] for c in receipt['cells']),
        'failed':[{k:c[k] for k in ('path','mode','fee','order','reason')}
                  for c in receipt['cells'] if not c['passed']][:6]},sort_keys=True))
    raise SystemExit(0 if receipt['decision'].startswith('PASS_') else 2)
