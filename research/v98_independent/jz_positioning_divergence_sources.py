#!/usr/bin/env python3
"""JZ prospective OI/price positioning-divergence seven-slot causal sources.
2023-24 TRAINING only; 2025+, XRP, other engines, Frozen, paper prohibited.
"""
from __future__ import annotations
import numpy as np
from ic_oi_crowding_sources import load_oi

WARMUP=744
CLOCK=168
GROSS={"NORMAL":.88,"STRESS":.72,"RECOVERY":.84}
PATHS=("JZ_core_only","JZ_full","JZ_minus_opportunity","JZ_minus_RV","JZ_minus_stress")

def bundle(opening,high,low,close,rate,event,quote,oi):
    o,h,l,c,r,e,q,v=[np.asarray(x,dtype=float) for x in
                     (opening,high,low,close,rate,event,quote,oi)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(z.shape!=c.shape for z in (o,h,l,r,e,q,v)) or
        any(not np.isfinite(z).all() for z in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1)) or
        np.any(v[np.isfinite(v)]<=0)):
        raise ValueError("JZ_INVALID_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c)
    ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    market=np.mean(net,axis=1)
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    budgets=np.zeros((n,3),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        past=net[t-335:t+1]
        downside=np.maximum(np.sqrt(np.mean(np.minimum(past,0.)**2,axis=0)),.002)
        mom672=np.sum(net[t-671:t+1],axis=0)
        leaders=np.argsort(-(mom672/downside),kind="stable")[:2]
        core=np.zeros(4)
        inv=1./downside[leaders]
        core[leaders]=inv/inv.sum()
        experts=np.zeros((4,4))
        experts[0]=core
        # Every vendor 5m OI observation is deliberately lagged at least
        # one COMPLETE 1h bar; quarantined day never leaks through a fill.
        good=bool(np.isfinite(v[t-337:t]).all() and
                  np.all(q[t-168:t+1]>0))
        valid[t]=good
        regime="NORMAL"
        if good:
            oi48=np.log(v[t-1]/v[t-49])
            oi72=np.log(v[t-1]/v[t-73])
            oi168=np.log(v[t-1]/v[t-169])
            p48=np.sum(net[t-47:t+1],axis=0)
            p168=np.sum(net[t-167:t+1],axis=0)
            m72=float(np.sum(market[t-71:t+1]))
            m24=float(np.sum(market[t-23:t+1]))
            mprev72=float(np.sum(market[t-95:t-23]))
            regime=("STRESS" if m72<-.03 and np.count_nonzero(oi72<0)>=3
                    else "RECOVERY" if m24>.015 and mprev72<0
                    else "NORMAL")
            # Optional 1: OI-confirmed new price high, not short-covering.
            qualify=(oi48>0)&(p168>0)&(c[t]>np.max(c[t-168:t],axis=0))
            if np.any(qualify):
                score=np.where(qualify,oi48*p168,-np.inf)
                experts[1,int(np.argmax(score))]=1.
                budgets[t,0]=.04+.08*min(1.,float(np.max(oi48[qualify]))/.10)
            # Optional 2: positioning/price cross-sectional divergence.
            score=(p168-.5*oi168)/downside
            long=int(np.argmax(score));short=int(np.argmin(score))
            if long!=short and score[long]>score[short]:
                experts[2,long]=.5;experts[2,short]=-.5
                budgets[t,1]=.04+.08*min(1.,float(np.max(oi168)-np.min(oi168))/.20)
            # Optional 3: three-state OI-exhaustion / rebound engine.
            if regime=="STRESS":
                stressed=(oi48>0)&(p48<0)
                if np.any(stressed):
                    chosen=int(np.argmax(np.where(stressed,oi48,-np.inf)))
                    experts[3,chosen]=-1.
                else:
                    experts[3,int(np.argmax(p48))]=1.
            elif regime=="RECOVERY":
                eligible=(oi72<0)&(p48>0)
                chosen=int(np.argmax(np.where(eligible,p48,-np.inf))) if np.any(eligible) else int(np.argmax(p48))
                experts[3,chosen]=1.
            else:
                eligible=p168>0
                if np.any(eligible):
                    chosen=int(np.argmin(np.where(eligible,oi168,np.inf)))
                    experts[3,chosen]=1.
            if np.any(experts[3]):
                budgets[t,2]=.04+.08*min(1.,abs(m72)/.08)
        regimes[t]=regime
        if np.sum(budgets[t])>.36+1e-12:
            raise ValueError("JZ_OPTIONAL_CAP")
        for path in range(5):
            b=budgets[t].copy()
            if path==0:b[:]=0.
            elif path>=2:b[path-2]=0.
            target=(1.-float(np.sum(b)))*core+b@experts[1:]
            if not np.isfinite(target).all() or np.abs(target).sum()>1.+1e-10:
                raise ValueError("JZ_GROSS_OR_FINITE")
            targets[t,path]=target
        if not good and not np.allclose(targets[t],targets[t,0]):
            raise ValueError("JZ_QUARANTINE_LEAK")
        updates[t]=True
    return targets,updates,regimes,valid,budgets

def static_check():
    n=3800
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    v=1e5*np.exp(t[:,None]*np.array([[.00001,.00002,.00003,.00004]])+
                 .1*np.sin(t[:,None]/79.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q,v)
    cc,oo,hh,ll,qq,rr,vv=[z.copy() for z in (c,o,h,l,q,r,v)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.;vv[3200:]*=2.
    b=bundle(oo,hh,ll,cc,rr,e,qq,vv)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("JZ_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.+1e-10):
        raise ValueError("JZ_GROSS")
    bad=v.copy();bad[700,2]=np.nan
    gap=bundle(o,h,l,c,r,e,q,bad)
    if gap[3][WARMUP] or not np.allclose(gap[0][WARMUP],gap[0][WARMUP,0]):
        raise ValueError("JZ_OI_QUARANTINE")
    # At t=744, OI[t] must not affect the decision; OI[t-1] may.
    mutation=v.copy();mutation[WARMUP]*=100.
    delayed=bundle(o,h,l,c,r,e,q,mutation)
    if not np.array_equal(a[0][WARMUP],delayed[0][WARMUP]):
        raise ValueError("JZ_OI_PUBLICATION_LAG")
    return True

if __name__=="__main__":
    assert static_check()
    print("JZ_CAUSAL_OI_LAG_AND_QUARANTINE_PASS")
