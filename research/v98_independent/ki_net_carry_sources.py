#!/usr/bin/env python3
"""KI distinct preregistered net-carry dispersion, trend convexity seven-slot targets.
Source-only, completed 1h Clean-4; no trading PnL or future data."""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=168
GROSS={"NORMAL":.90,"STRESS":.70,"RECOVERY":.80}
PATHS=("KI_core_only","KI_full","KI_minus_opportunity","KI_minus_RV","KI_minus_stress")
CAPS=np.array([.16,.12,.10],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KI_INVALID_CANONICAL_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    market=net.mean(axis=1)
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    budgets=np.zeros((n,3),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        m336=net[t-335:t+1].sum(axis=0)
        m168=net[t-167:t+1].sum(axis=0)
        m72=net[t-71:t+1].sum(axis=0)
        m24=net[t-23:t+1].sum(axis=0)
        carry168=(r[t-167:t+1]*e[t-167:t+1]).sum(axis=0)
        down=np.sqrt(np.mean(np.minimum(net[t-335:t+1],0.)**2,axis=0))
        score=m336-.35*down*np.sqrt(168.)-.5*np.maximum(carry168,0.)
        leaders=np.argsort(-score,kind="stable")[:2]
        core=np.zeros(4)
        if np.any(m336[leaders]>0.):
            soft=np.exp((score[leaders]-max(score[leaders]))/.20)
            core[leaders]=soft/soft.sum()
        market168=float(market[t-167:t+1].sum())
        market24=float(market[t-23:t+1].sum())
        prior72=float(market[t-95:t-23].sum())
        regime=("STRESS" if market168<-.07 else
                "RECOVERY" if market24>.02 and prior72<0. else "NORMAL")
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        experts=np.zeros((3,4),dtype=float)
        active=np.zeros(3,dtype=bool)
        if good:
            previous=net[t-167:t+1].sum(axis=0)
            priorq=q[t-239:t-71].mean(axis=0)
            recentq=q[t-71:t+1].mean(axis=0)
            if np.any(priorq<=0):
                raise ValueError("KI_ZERO_PRIOR_QUOTE")
            acceleration=m72-previous*(72./168.)
            eligible=(m72>0)&(recentq>priorq)&(acceleration>0)
            if np.any(eligible):
                k=int(np.argmax(np.where(eligible,acceleration,-np.inf)))
                experts[0,k]=1.;active[0]=True
            spreadscore=m168-.75*carry168
            long=int(np.argmax(spreadscore));short=int(np.argmin(spreadscore))
            if (long!=short and spreadscore[long]>0 and
                spreadscore[short]<0 and
                spreadscore[long]-spreadscore[short]>.04):
                experts[1,long]=.5;experts[1,short]=-.5
                active[1]=True
            if regime=="STRESS" and float(np.min(m72))<0:
                experts[2,int(np.argmin(m72))]=-1.;active[2]=True
            elif regime=="RECOVERY" and float(np.max(m24))>0:
                experts[2,int(np.argmax(m24))]=1.;active[2]=True
            elif (regime=="NORMAL" and float(np.max(m24))>.025 and
                  market168>.04):
                experts[2,int(np.argmax(m24))]=1.;active[2]=True
        b=CAPS*active.astype(float)
        budgets[t]=b
        for path in range(5):
            bp=b.copy()
            if path==0:bp[:]=0.
            elif path>=2:bp[path-2]=0.
            weights=(1.-float(bp.sum()))*core+bp@experts
            if not np.isfinite(weights).all() or np.abs(weights).sum()>1.+1e-10:
                raise ValueError("KI_GROSS_OR_FINITE")
            targets[t,path]=weights
        if not good and not np.allclose(targets[t],targets[t,0]):
            raise ValueError("KI_INVALID_QUOTE_OPTIONAL_LEAK")
        regimes[t]=regime;updates[t]=True
    return targets,updates,regimes,valid,budgets

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .045*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.35*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("KI_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.+1e-10):
        raise ValueError("KI_GROSS")
    bad=q.copy();bad[700,2]=0.
    gap=bundle(o,h,l,c,r,e,bad)
    if gap[3][WARMUP] or not np.allclose(gap[0][WARMUP],gap[0][WARMUP,0]):
        raise ValueError("KI_NATIVE_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("KI_NET_CARRY_CAUSAL_SYNTHETIC_PASS")
