#!/usr/bin/env python3
"""V98 Independent AG complete 180-cell synthetic structural gate, no historical PnL."""
from __future__ import annotations
import itertools,json,argparse
import numpy as np
import pandas as pd
from phase1227_ag_seven_slot_sources import (
    ASSETS,START,PATHS,causal_sources,AGStress,AGAllocator,BASE_CASH)
from phase1226_ag_atomic_portfolio import COSTS
from phase1228_ag_actual_ledger import ORDERS,execute_hour

CAPITAL={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}


def fixture(crisis=False,n=900):
    idx=pd.date_range(START,periods=n,freq='h')
    t=np.arange(n,dtype=float)
    trend=np.array([.0005,.0007,-.0003,.0004])
    close=100*np.exp(t[:,None]*trend+
        .006*np.sin(t[:,None]/np.array([11.,13.,17.,19.])))
    if crisis:
        close[810:]*=.55
        close[850:]*=1.80
    opening=np.vstack((close[0],close[:-1]))
    high=np.maximum(opening,close)*1.0001
    low=np.minimum(opening,close)*.9999
    quote=1e12*(1+.5*np.sin(t[:,None]/7+np.arange(4))**2)
    rate=np.zeros_like(close)
    event=np.zeros_like(close)
    event[::8]=1.
    rate[::8]=np.array([.0001,-.0001,.00015,-.00015])
    mark_low=close*.99
    mark_high=close*1.01
    return opening,high,low,close,quote,rate,event,mark_low,mark_high


def prior_risk(o,h,l,q,r,e):
    n=len(o)
    d=np.zeros((n,4))
    u=np.zeros((n,4))
    f=np.zeros((n,4))
    pq=np.zeros((n,4))
    qmin=np.zeros((n,4))
    for t in range(720,n):
        sl=slice(t-336,t)
        d[t]=np.maximum(.12,np.max(1-l[sl]/o[sl],axis=0))
        u[t]=np.maximum(.12,np.max(h[sl]/o[sl]-1,axis=0))
        f[t]=np.maximum(.0005,3*np.max(np.abs(r[t-720:t]*e[t-720:t]),axis=0))
        pq[t]=q[t-1]
        qmin[t]=np.min(q[sl],axis=0)
    return d,u,f,pq,qmin


def cell(path,mode,fee,order,frames,slots,risk,fixture_name):
    o,h,l,c,q,r,e,ml,mh=frames
    g,op,rv,router=slots
    d,u,f,pq,qmin=risk
    cash=CAPITAL[mode]
    units=np.zeros(4)
    nav=cash
    stress=AGStress()
    alloc=AGAllocator()
    mu=np.zeros(4)
    reserve=BASE_CASH
    turnover=fees=slippage=funding=0.
    executed=0
    min_nav=nav
    max_dd=0.
    peak=nav
    for t in range(len(c)):
        if t>=720:
            try:
                res=execute_hour(units,cash,o[t],h[t],l[t],c[t],mu,
                    reserve,d[t],u[t],f[t],pq[t],qmin[t],fee,
                    r[t],e[t],ml[t],mh[t],order,
                    scheduled_rebalance=(t==720 or (t-720)%24==0))
            except Exception as exc:
                raise ValueError('AG1229_T'+str(t)+'_'+str(exc)) from exc
            units,cash,nav=res['units'],res['cash'],res['nav']
            turnover+=res['turnover'];fees+=res['fees']
            slippage+=res['slippage'];funding+=res['funding']
            executed+=int(res['executed'])
            peak=max(peak,nav)
            max_dd=max(max_dd,1-nav/peak)
            min_nav=min(min_nav,nav)
            if cash<-1e-6 or np.any(units<0) or not np.isclose(
                nav,cash+units@c[t],atol=1e-6,rtol=0):
                raise ValueError('AG1229_NAV_RECONCILIATION')
        market=float(np.log(c[t]/c[t-1]).mean()) if t else 0.
        reserve=stress.step(nav,market)
        if t>=169:
            lr=np.log(c[t]/c[t-1])
            mu=alloc.step(lr,g[t],op[t],rv[t],router[t],reserve,path)
    return {'fixture':fixture_name,'path':path,'mode':mode,'fee':fee,
            'order':order,'passed':True,'synthetic_only':True,
            'historical_system_pnl_computed':False,
            'executed_hours':180,'rebalances':executed,
            'synthetic_final_nav':float(nav),'synthetic_min_nav':float(min_nav),
            'synthetic_max_dd':float(max_dd),'turnover':turnover,
            'fees':fees,'slippage':slippage,'funding':funding,
            'stress_active_hours':stress.active_hours,
            'active_sleeves':alloc.active.tolist()}


def run():
    cells=[]
    for crisis in (False,True):
        name='crisis' if crisis else 'benign'
        frames=fixture(crisis)
        slots=causal_sources(frames[3],frames[4])
        risk=prior_risk(*frames[:7])
        for path,mode,fee,order in itertools.product(
                PATHS,CAPITAL,COSTS,ORDERS):
            try:
                cells.append(cell(path,mode,fee,order,frames,slots,risk,name))
            except Exception as exc:
                cells.append({'fixture':name,'path':path,'mode':mode,
                    'fee':fee,'order':order,'passed':False,
                    'reason':type(exc).__name__+': '+str(exc),
                    'historical_system_pnl_computed':False})
    full=next((x for x in cells if x['fixture']=='crisis' and
        x['path']=='AG_full' and x['mode']=='immediate' and
        x['fee']=='base' and x['order']=='carried_before_fill'),{})
    passed=(len(cells)==180 and all(x['passed'] for x in cells) and
            full.get('stress_active_hours',0)>0)
    return {'phase':1229,'architecture':'AG','decision':
        'PASS_AG_180_SYNTHETIC_NOT_ECONOMIC' if passed else
        'REJECT_AG_180_SYNTHETIC_NO_HISTORICAL_PNL',
        'historical_system_pnl_computed':False,'validation_2025_read':False,
        'external_benchmarks_used':False,'cells':cells}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='ag_phase1229_receipt.json')
    args=parser.parse_args()
    result=run()
    with open(args.output,'w') as fp:
        json.dump(result,fp,sort_keys=True,indent=2)
    failures=[x for x in result['cells'] if not x['passed']]
    print(json.dumps({'decision':result['decision'],
        'passed':len(result['cells'])-len(failures),
        'failed':len(failures),'first_failures':failures[:8]},
        sort_keys=True))
    raise SystemExit(0 if not failures and result['decision'].startswith('PASS') else 2)
