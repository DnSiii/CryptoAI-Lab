#!/usr/bin/env python3
"""KG preregistered causal prequential joint-capital auction; source-only, no PnL."""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=168
GROSS={"NORMAL":.85,"STRESS":.65,"RECOVERY":.75}
PATHS=("KG_core_only","KG_full","KG_minus_opportunity","KG_minus_RV","KG_minus_stress")
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
        raise ValueError("KG_INVALID_CANONICAL_SOURCE")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    market=net.mean(axis=1)
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    budgets=np.zeros((n,3),dtype=float)
    shadow=[[],[],[]]
    prev=None
    for t in range(WARMUP,n,CLOCK):
        if prev is not None:
            # Only the *previous* 168h completed after the prior signal.
            realized=net[t-167:t+1].sum(axis=0)
            oldcore,oldexperts,oldactive=prev
            for i in range(3):
                diff=oldexperts[i]-oldcore
                score=(float(diff@realized)-.002*float(np.abs(diff).sum())
                       if oldactive[i] else -.03)
                shadow[i].append(score)
                shadow[i]=shadow[i][-4:]
        downside=np.maximum(np.sqrt(np.mean(
            np.minimum(net[t-335:t+1],0.)**2,axis=0)),.002)
        r336=net[t-335:t+1].sum(axis=0)
        r672=net[t-671:t+1].sum(axis=0)
        rank=.65*r336+.35*r672-.5*downside*np.sqrt(168.)
        leaders=np.argsort(-rank,kind="stable")[:2]
        core=np.zeros(4)
        inverse=1./downside[leaders]
        core[leaders]=inverse/inverse.sum()
        m72=float(market[t-71:t+1].sum())
        m24=float(market[t-23:t+1].sum())
        prior72=float(market[t-95:t-23].sum())
        regime=("STRESS" if m72<-.035 else
                "RECOVERY" if m24>.015 and prior72<0 else "NORMAL")
        good=bool(np.all(q[t-671:t+1]>0))
        valid[t]=good
        experts=np.zeros((3,4),dtype=float)
        active=np.zeros(3,dtype=bool)
        if good:
            r72=net[t-71:t+1].sum(axis=0)
            rprev72=net[t-143:t-71].sum(axis=0)
            r24=net[t-23:t+1].sum(axis=0)
            prevq=q[t-407:t-71].mean(axis=0)
            nowq=q[t-71:t+1].mean(axis=0)
            if np.any(prevq<=0):raise ValueError("KG_ZERO_BASELINE_QUOTE")
            surprise=np.maximum(np.log(nowq/prevq),0.)
            opportunity=np.maximum(r72-rprev72,0.)*surprise
            eligible=(r72>0)&(opportunity>0)
            if np.any(eligible):
                k=int(np.argmax(np.where(eligible,opportunity,-np.inf)))
                experts[0,k]=1.;active[0]=True
            residual=r72-float(r72.mean())
            eligible=(r672>0)&(r24>0)&(residual<0)
            if np.any(eligible):
                k=int(np.argmin(np.where(eligible,residual,np.inf)))
                experts[1,k]=1.;active[1]=True
            if regime=="STRESS":
                experts[2,int(np.argmax(downside))]=-1.
                active[2]=True
            elif regime=="RECOVERY" and np.max(r24)>0:
                experts[2,int(np.argmax(r24))]=1.
                active[2]=True
        b=np.zeros(3)
        for i in range(3):
            if active[i]:
                adv=float(np.mean(shadow[i])) if shadow[i] else 0.
                b[i]=CAPS[i]*np.clip(.5+adv/.03,0.,1.)
        budgets[t]=b
        for path in range(5):
            bp=b.copy()
            if path==0:bp[:]=0.
            elif path>=2:bp[path-2]=0.
            weights=(1.-float(bp.sum()))*core+bp@experts
            if not np.isfinite(weights).all() or np.abs(weights).sum()>1.+1e-10:
                raise ValueError("KG_GROSS_OR_FINITE")
            targets[t,path]=weights
        if not good and not np.allclose(targets[t],targets[t,0]):
            raise ValueError("KG_INVALID_SOURCE_OPTIONAL_LEAK")
        prev=(core.copy(),experts.copy(),active.copy())
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
            raise ValueError("KG_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.+1e-10):
        raise ValueError("KG_GROSS")
    bad=q.copy();bad[700,2]=0.
    gap=bundle(o,h,l,c,r,e,bad)
    if gap[3][WARMUP] or not np.allclose(gap[0][WARMUP],gap[0][WARMUP,0]):
        raise ValueError("KG_NATIVE_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("KG_PREQUENTIAL_CAUSAL_SYNTHETIC_PASS")
