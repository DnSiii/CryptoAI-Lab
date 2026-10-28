#!/usr/bin/env python3
"""KJ preregistered persistent inventory + pair dislocation seven-slot sources; no PnL."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
INVENTORY_CLOCK=672
GROSS={"NORMAL":.90,"STRESS":.70,"RECOVERY":.80}
PATHS=("KJ_core_only","KJ_full","KJ_minus_opportunity","KJ_minus_RV","KJ_minus_stress")
CAPS=np.array([.18,.12,.10],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KJ_INVALID_CANONICAL_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e;market=net.mean(axis=1)
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    budgets=np.zeros((n,3),dtype=float)
    core=np.zeros(4)
    for t in range(WARMUP,n,CLOCK):
        if (t-WARMUP)%INVENTORY_CLOCK==0:
            n672=net[t-671:t+1].sum(axis=0)
            downside=np.sqrt(np.mean(np.minimum(net[t-671:t+1],0.)**2,axis=0))
            score=n672-.5*downside*np.sqrt(168.)
            leader=int(np.argmax(score))
            if score[leader]<=0:
                core[:]=0.
            else:
                old=np.flatnonzero(core)
                if len(old)==1 and score[int(old[0])]>=score[leader]-.04:
                    leader=int(old[0])
                core[:]=0.;core[leader]=1.
        m24=net[t-23:t+1].sum(axis=0)
        m168=net[t-167:t+1].sum(axis=0)
        market24=float(market[t-23:t+1].sum())
        market168=float(market[t-167:t+1].sum())
        trajectory=np.r_[0.,np.cumsum(market[t-335:t+1])]
        drawdown=float(max(trajectory)-trajectory[-1])
        regime=("STRESS" if drawdown>.07 and market24<0 else
                "RECOVERY" if market24>.02 and market168<0 else "NORMAL")
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        experts=np.zeros((3,4),dtype=float)
        active=np.zeros(3,dtype=bool)
        if good:
            breakout=(c[t]>np.max(c[t-168:t],axis=0))
            recentq=q[t-23:t+1].mean(axis=0)
            priorq=q[t-191:t-23].mean(axis=0)
            eligible=breakout&(m24>0)&(recentq>priorq)
            if np.any(eligible):
                k=int(np.argmax(np.where(eligible,m24,-np.inf)))
                experts[0,k]=1.;active[0]=True
            candidates=[]
            for left,right in ((0,1),(2,3)):
                ratio=np.log(c[t-335:t+1,left]/c[t-335:t+1,right])
                sd=float(np.std(ratio))
                if sd>1e-12:
                    z=float((ratio[-1]-ratio.mean())/sd)
                    candidates.append((abs(z),left,right,z))
            if candidates:
                magnitude,left,right,z=max(candidates,key=lambda x:x[0])
                if magnitude>.8:
                    experts[1,left]=-.5 if z>0 else .5
                    experts[1,right]=.5 if z>0 else -.5
                    active[1]=True
            if regime=="STRESS":
                semivol=np.sqrt(np.mean(np.minimum(net[t-167:t+1],0.)**2,axis=0))
                experts[2,int(np.argmax(semivol))]=-1.;active[2]=True
            elif regime=="RECOVERY":
                experts[2,int(np.argmax(m24))]=1.;active[2]=True
        b=CAPS*active.astype(float)
        budgets[t]=b
        for path in range(5):
            bp=b.copy()
            if path==0:bp[:]=0.
            elif path>=2:bp[path-2]=0.
            weights=(1.-float(bp.sum()))*core+bp@experts
            if not np.isfinite(weights).all() or np.abs(weights).sum()>1.+1e-10:
                raise ValueError("KJ_GROSS_OR_FINITE")
            targets[t,path]=weights
        if not good and not np.allclose(targets[t],targets[t,0]):
            raise ValueError("KJ_INVALID_QUOTE_OPTIONAL_LEAK")
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
            raise ValueError("KJ_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.+1e-10):
        raise ValueError("KJ_GROSS")
    bad=q.copy();bad[700,2]=0.
    gap=bundle(o,h,l,c,r,e,bad)
    if gap[3][WARMUP] or not np.allclose(gap[0][WARMUP],gap[0][WARMUP,0]):
        raise ValueError("KJ_NATIVE_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("KJ_PERSISTENT_INVENTORY_CAUSAL_SYNTHETIC_PASS")
