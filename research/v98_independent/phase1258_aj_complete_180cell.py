#!/usr/bin/env python3
"""V98 Independent AJ1258 complete seven-slot 180-cell SYNTHETIC gate."""
from __future__ import annotations
import argparse
import itertools
import json
import numpy as np
from phase1246_ai_two_stage_margin import settle_hour
from phase1255_aj_signed_sources import source_bundle
from phase1256_aj_wealth_allocator import AJWealthAllocator
from phase1257_aj_open_viability_governor import aj_governor,FEES,ORDERS

PATHS=('AJ_core_only','AJ_full','AJ_minus_opportunity',
       'AJ_minus_RV','AJ_minus_stress')
CAPITAL={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}
HOURS=900
WARMUP=720

def fixture(crisis=False):
    t=np.arange(HOURS,dtype=float)
    drift=np.array([.0007,.0011,-.0002,.0005])
    c=100*np.exp(t[:,None]*drift+
        .018*np.sin(t[:,None]/np.array([11.,13.,17.,19.]))+
        .007*np.cos(t[:,None]/np.array([5.,7.,9.,11.])))
    if crisis:
        c[810:]*=.55
        c[850:]*=1.80
        c[870:,3]*=.40
    o=np.vstack((c[0],c[:-1]))
    if crisis:
        for k in (810,850,870):
            o[k]=c[k]
    h=np.maximum(o,c)*1.0001
    l=np.minimum(o,c)*.9999
    q=1e12*(1+.1*np.sin(t[:,None]/17.+np.arange(4))**2)
    r=np.zeros_like(c)
    e=np.zeros_like(c)
    e[::8]=1.
    r[::8]=np.array([.0001,-.0001,.00015,-.00015])
    return o,h,l,c,q,r,e,c*.99,c*1.01

def prior_risk(frames):
    o,h,l,c,q,r,e,ml,mh=frames
    d=np.zeros((HOURS,4))
    u=np.zeros((HOURS,4))
    f=np.zeros((HOURS,4))
    qmin=np.zeros((HOURS,4))
    for t in range(WARMUP,HOURS):
        sl=slice(t-336,t)
        d[t]=np.maximum(.45,np.max(1-l[sl]/o[sl],axis=0))
        u[t]=np.maximum(.80,np.max(h[sl]/o[sl]-1,axis=0))
        f[t]=np.maximum(.0005,3*np.max(np.abs(
            r[t-WARMUP:t]*e[t-WARMUP:t]),axis=0))
        qmin[t]=np.min(q[sl],axis=0)
    return d,u,f,qmin

def cell(path,mode,fee,order,frames,slots,risk,name):
    o,h,l,c,q,r,e,ml,mh=frames
    growth,op,rv,stress,router=slots
    d,u,f,qmin=risk
    cash=CAPITAL[mode]
    nav=cash
    old=np.zeros(4)
    pending=np.zeros(4)
    components=np.zeros((4,4))
    allocator=AJWealthAllocator()
    turnover=fees=slippage=funding=0.
    rebalances=0
    peak=cash
    min_nav=cash
    max_dd=0.
    active=np.zeros(4,dtype=int)
    marginal=np.zeros(4,dtype=int)
    audit=(name=='crisis' and path=='AJ_full' and mode=='immediate'
           and fee=='base' and order=='carried_before_fill')
    for t in range(HOURS):
        if t>=WARMUP:
            try:
                kw=dict(cash_previous=cash,old_units=old,
                    prior_close=c[t-1],opening=o[t],
                    prior_down=d[t],prior_up=u[t],
                    funding_bound=f[t],prior_quote=q[t-1],
                    min_quote=qmin[t],fee_mode=fee,
                    funding_order=order)
                target=aj_governor(signed_target=pending,**kw)
                if audit:
                    for k in (1,2,3):
                        if np.max(np.abs(components[k]))<=1e-12:
                            continue
                        cf=aj_governor(signed_target=pending-components[k],**kw)
                        marginal[k]+=int(np.max(np.abs(
                            target['units']-cf['units']))>1e-9)
                out=settle_hour(cash,old,c[t-1],o[t],h[t],l[t],c[t],
                    target['units'],r[t],e[t],ml[t],mh[t],
                    fee_mode=fee,funding_order=order)
            except Exception as exc:
                raise ValueError('AJ1258_T'+str(t)+'_'+str(exc)) from exc
            cash=out['cash']
            old=out['units']
            nav=out['equity']
            turnover+=out['turnover']
            fees+=out['fees']
            slippage+=out['slippage']
            funding+=out['funding']
            rebalances+=int(out['turnover']>1e-10)
            if (out['hidden_borrow'] or not out['cash_settled'] or
                not np.isclose(nav,cash,atol=1e-7,rtol=0)):
                raise ValueError('AJ1258_NAV_RECONCILIATION')
            peak=max(peak,nav)
            min_nav=min(min_nav,nav)
            max_dd=max(max_dd,1-nav/peak)
        s=np.stack((growth[t],op[t],rv[t],stress[t]))
        if path=='AJ_core_only':
            s[1:]=0.
        if path=='AJ_minus_opportunity':
            s[1]=0.
        if path=='AJ_minus_RV':
            s[2]=0.
        if path=='AJ_minus_stress':
            s[3]=0.
        if t>=WARMUP:
            active+=(np.abs(s).sum(axis=1)>1e-10).astype(int)
        lr=np.log(c[t]/c[t-1]) if t else np.zeros(4)
        allocator.observe(lr,r[t],e[t])
        decision=allocator.decide(s,str(router['state'][t]))
        pending=decision['signed_target']
        components=decision['growth_scale']*decision['weights'][:,None]*s
    return {'fixture':name,'path':path,'mode':mode,'fee':fee,'order':order,
            'passed':True,'synthetic_only':True,
            'historical_system_pnl_computed':False,
            'executed_hours':HOURS-WARMUP,
            'rebalances':rebalances,
            'synthetic_final_nav':float(nav),
            'synthetic_min_nav':float(min_nav),
            'synthetic_max_dd':float(max_dd),
            'turnover':float(turnover),'fees':float(fees),
            'slippage':float(slippage),'funding':float(funding),
            'active_sleeves':active.tolist(),
            'marginal_executable_hours':marginal.tolist(),
            'allocator_observations':allocator.observations}

def run():
    cells=[]
    for crisis in (False,True):
        name='crisis' if crisis else 'benign'
        frames=fixture(crisis)
        slots=source_bundle(frames[3],frames[1],frames[2],
                            frames[5],frames[6])
        risk=prior_risk(frames)
        for path,mode,fee,order in itertools.product(
                PATHS,CAPITAL,FEES,ORDERS):
            try:
                cells.append(cell(path,mode,fee,order,
                                  frames,slots,risk,name))
            except Exception as exc:
                cells.append({'fixture':name,'path':path,'mode':mode,
                    'fee':fee,'order':order,'passed':False,
                    'reason':type(exc).__name__+': '+str(exc),
                    'historical_system_pnl_computed':False})
    full=next((x for x in cells if x['fixture']=='crisis' and
        x['path']=='AJ_full' and x['mode']=='immediate' and
        x['fee']=='base' and x['order']=='carried_before_fill'),{})
    active=full.get('active_sleeves',[0,0,0,0])
    marginal=full.get('marginal_executable_hours',[0,0,0,0])
    excited=bool(full.get('rebalances',0)>0 and
        all(x>0 for x in active) and all(x>0 for x in marginal[1:]))
    complete=len(cells)==180 and all(x['passed'] for x in cells)
    return {'phase':1258,'architecture':'AJ',
        'decision':('PASS_AJ_180_SYNTHETIC_NOT_ECONOMIC'
                    if complete and excited else
                    'REJECT_AJ_180_SYNTHETIC_NO_HISTORICAL_PNL'),
        'complete_survival':complete,'mandatory_slots_excited':excited,
        'historical_system_pnl_computed':False,
        'validation_2025_read':False,'external_benchmarks_used':False,
        'cells':cells}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='aj1258_receipt.json')
    args=parser.parse_args()
    result=run()
    with open(args.output,'w') as f:
        json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
    failed=[x for x in result['cells'] if not x['passed']]
    print(json.dumps({'decision':result['decision'],
        'passed':len(result['cells'])-len(failed),
        'failed':len(failed),'mandatory_slots_excited':
        result['mandatory_slots_excited'],'first_failures':failed[:8]},
        sort_keys=True))
    raise SystemExit(0 if result['decision'].startswith('PASS') else 2)
