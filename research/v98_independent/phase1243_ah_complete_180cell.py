#!/usr/bin/env python3
"""V98 AH1243 complete seven-slot 180-cell SYNTHETIC gate. NO historical PnL."""
from __future__ import annotations
import argparse,itertools,json
import numpy as np
from phase1234_ah_signed_variation_margin import FEE_MODES,ORDERS,settle_hour
from phase1235_ah_signed_growth_core import ah_growth_source
from phase1236_ah_volatility_opportunity import ah_opportunity_source
from phase1237_ah_beta_neutral_rv import ah_relative_value_source
from phase1238_ah_actual_nav_stress_hedge import AHStressHedge
from phase1240_ah_regime_router import ah_regime_router
from phase1241_ah_online_growth_allocator import AHOnlineGrowthAllocator
from phase1242_ah_signed_governor import ah_governor_target

PATHS=('AH_core_only','AH_full','AH_minus_opportunity',
       'AH_minus_RV','AH_minus_stress')
CAPITAL={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}
HOURS=900
WARMUP=720

def fixture(crisis=False):
    t=np.arange(HOURS,dtype=float)
    # Synthetic prices fixed in preregistered code BEFORE evaluation.
    drift=np.array([.0007,.0011,-.0002,.0005])
    c=100*np.exp(t[:,None]*drift[None,:]+
        .018*np.sin(t[:,None]/np.array([11.,13.,17.,19.]))+
        .007*np.cos(t[:,None]/np.array([5.,7.,9.,11.])))
    if crisis:
        c[810:]*=.55
        c[850:]*=1.80
        c[870:,3]*=.40
    o=np.vstack((c[0],c[:-1]))
    if crisis:
        for k in (810,850,870):o[k]=c[k]
    h=np.maximum(o,c)*1.0001
    l=np.minimum(o,c)*.9999
    q=1e12*(1+.1*np.sin(t[:,None]/17.+np.arange(4))**2)
    rate=np.zeros_like(c)
    event=np.zeros_like(c)
    event[::8]=1.
    rate[::8]=np.array([.0001,-.0001,.00015,-.00015])
    ml=c*.99
    mh=c*1.01
    return (o,h,l,c,q,rate,event,ml,mh)

def prior_bounds(frames):
    o,h,l,c,q,r,e,ml,mh=frames
    n=len(c)
    down=np.zeros((n,4));up=np.zeros((n,4))
    f=np.zeros((n,4));qmin=np.zeros((n,4))
    for t in range(WARMUP,n):
        sl=slice(t-336,t)
        down[t]=np.maximum(.45,np.max(1-l[sl]/o[sl],axis=0))
        up[t]=np.maximum(.80,np.max(h[sl]/o[sl]-1,axis=0))
        f[t]=np.maximum(.0005,3*np.max(np.abs(r[t-WARMUP:t]*e[t-WARMUP:t]),axis=0))
        qmin[t]=np.min(q[sl],axis=0)
    return down,up,f,qmin

def source_bundle(frames):
    o,h,l,c,q,r,e,ml,mh=frames
    g=ah_growth_source(c,r,e)
    opportunity=ah_opportunity_source(c,h,l)
    rv,betas=ah_relative_value_source(c)
    regime=ah_regime_router(c,r,e)
    return g,opportunity,rv,regime

def cell(path,mode,fee,order,frames,slots,bounds,fixture_name):
    o,h,l,c,q,r,e,ml,mh=frames
    growth,opportunity,rv,regime=slots
    down,up,f,qmin=bounds
    cash=CAPITAL[mode]
    nav=cash
    old=np.zeros(4)
    pending=np.zeros(4)
    pending_components=np.zeros((4,4))
    marginal_exec=np.zeros(4,dtype=int)
    audit_marginal=(path=='AH_full' and mode=='immediate' and
        fee=='base' and order=='carried_before_fill' and fixture_name=='crisis')
    stress=AHStressHedge()
    allocator=AHOnlineGrowthAllocator()
    turnovers=fees=slippage=funding=0.
    active_exec=0
    peak=cash;max_dd=0.
    min_nav=cash
    active_sleeves=np.zeros(4,dtype=int)
    stress_source_hours=0
    opportunity_source_hours=0
    rv_source_hours=0
    for t in range(HOURS):
        if t>=WARMUP:
            try:
                target=ah_governor_target(cash,old,c[t-1],o[t],
                    pending,down[t],up[t],f[t],q[t-1],qmin[t],
                    fee_mode=fee,order=order)
                if audit_marginal:
                    for k in (1,2,3):
                        if np.max(np.abs(pending_components[k]))<=1e-12:
                            continue
                        cf=ah_governor_target(cash,old,c[t-1],o[t],
                            pending-pending_components[k],down[t],up[t],
                            f[t],q[t-1],qmin[t],fee_mode=fee,order=order)
                        marginal_exec[k]+=int(np.max(np.abs(
                            target['units']-cf['units']))>1e-9)
                out=settle_hour(cash,old,c[t-1],o[t],h[t],l[t],c[t],
                    target['units'],q[t-1],qmin[t],down[t],up[t],
                    f[t],r[t],e[t],ml[t],mh[t],fee_mode=fee,order=order)
            except Exception as exc:
                raise ValueError('AH1243_T'+str(t)+'_'+str(exc)) from exc
            cash=out['cash'];old=out['units'];nav=out['equity']
            turnovers+=out['turnover'];fees+=out['fees']
            slippage+=out['slippage'];funding+=out['funding']
            active_exec+=int(out['turnover']>1e-10)
            if not np.isclose(nav,cash,atol=1e-7,rtol=0):
                raise ValueError('AH1243_NAV_CASH_RECONCILIATION')
            if out['hidden_borrow'] or not out['cash_settled']:
                raise ValueError('AH1243_HIDDEN_LEVERAGE')
            peak=max(peak,nav)
            min_nav=min(min_nav,nav)
            max_dd=max(max_dd,1-nav/peak)
        market=float(np.mean(np.log(c[t]/c[t-1]))) if t else 0.
        hedge=stress.step(nav,market)
        s=np.stack((growth[t],opportunity[t],rv[t],hedge))
        if path=='AH_core_only':s[1:]=0.
        if path=='AH_minus_opportunity':s[1]=0.
        if path=='AH_minus_RV':s[2]=0.
        if path=='AH_minus_stress':s[3]=0.
        if t>=WARMUP:
            active_sleeves+=(np.abs(s).sum(axis=1)>1e-10).astype(int)
            stress_source_hours+=int(np.abs(s[3]).sum()>0)
            opportunity_source_hours+=int(np.abs(s[1]).sum()>0)
            rv_source_hours+=int(np.abs(s[2]).sum()>0)
        log_return=np.log(c[t]/c[t-1]) if t else np.zeros(4)
        allocator.observe(log_return,r[t],e[t])
        proposal=allocator.decide(s,str(regime['state'][t]))
        pending=proposal['signed_target']
        pending_components=(proposal['growth_scale']*
            proposal['sleeve_weights'][:,None]*s)
    return {'fixture':fixture_name,'path':path,'mode':mode,
            'fee':fee,'order':order,'passed':True,'synthetic_only':True,
            'historical_system_pnl_computed':False,
            'executed_hours':HOURS-WARMUP,'rebalances':active_exec,
            'synthetic_final_nav':float(nav),'synthetic_min_nav':float(min_nav),
            'synthetic_max_dd':float(max_dd),'turnover':float(turnovers),
            'fees':float(fees),'slippage':float(slippage),
            'funding':float(funding),
            'stress_source_hours':stress_source_hours,
            'opportunity_source_hours':opportunity_source_hours,
            'rv_source_hours':rv_source_hours,
            'active_sleeves':active_sleeves.tolist(),
            'marginal_executable_hours':marginal_exec.tolist(),
            'allocator_observations':allocator.observations}

def run():
    cells=[]
    for crisis in (False,True):
        name='crisis' if crisis else 'benign'
        frames=fixture(crisis)
        slots=source_bundle(frames)
        bounds=prior_bounds(frames)
        for path,mode,fee,order in itertools.product(
                PATHS,CAPITAL,FEE_MODES,ORDERS):
            try:
                cells.append(cell(path,mode,fee,order,frames,slots,bounds,name))
            except Exception as exc:
                cells.append({'fixture':name,'path':path,'mode':mode,
                    'fee':fee,'order':order,'passed':False,
                    'reason':type(exc).__name__+': '+str(exc),
                    'historical_system_pnl_computed':False})
    full=next((x for x in cells if x['fixture']=='crisis' and
        x['path']=='AH_full' and x['mode']=='immediate' and
        x['fee']=='base' and x['order']=='carried_before_fill'),{})
    complete=len(cells)==180 and all(x['passed'] for x in cells)
    excited=bool(full.get('rebalances',0)>0 and
        full.get('opportunity_source_hours',0)>0 and
        full.get('rv_source_hours',0)>0 and
        full.get('stress_source_hours',0)>0 and
        all(x>0 for x in full.get('marginal_executable_hours',[0,0,0,0])[1:]))
    passed=complete and excited
    return {'phase':1243,'architecture':'AH',
        'decision':('PASS_AH_180_SYNTHETIC_NOT_ECONOMIC' if passed
                    else 'REJECT_AH_180_SYNTHETIC_NO_HISTORICAL_PNL'),
        'complete_survival':complete,'mandatory_slots_excited':excited,
        'historical_system_pnl_computed':False,'validation_2025_read':False,
        'external_benchmarks_used':False,'cells':cells}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='ah_phase1243_receipt.json')
    args=parser.parse_args()
    result=run()
    with open(args.output,'w') as fp:
        json.dump(result,fp,sort_keys=True,indent=2)
    failed=[x for x in result['cells'] if not x['passed']]
    print(json.dumps({'decision':result['decision'],
        'passed':len(result['cells'])-len(failed),
        'failed':len(failed),'mandatory_slots_excited':
        result['mandatory_slots_excited'],
        'first_failures':failed[:8]},sort_keys=True))
    raise SystemExit(0 if result['decision'].startswith('PASS') else 2)
