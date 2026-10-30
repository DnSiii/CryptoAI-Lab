#!/usr/bin/env python3
"""KB preregistered native funding-net binary state transition sources, 2023-24 training only."""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=168
GROSS={"NORMAL":.88,"STRESS":.70,"RECOVERY":.82}
PATHS=("KB_core_only","KB_full","KB_minus_opportunity","KB_minus_RV","KB_minus_stress")

def _entropy(p):
    p=np.clip(p,1e-12,1.-1e-12)
    return -(p*np.log2(p)+(1.-p)*np.log2(1.-p))

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(z.shape!=c.shape for z in (o,h,l,r,e,q)) or
        any(not np.isfinite(z).all() for z in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("KB_INVALID_NATIVE_SOURCE")
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
        # 672 observed completed funding-net returns, 671 actual transitions.
        state=(net[t-671:t+1]>0).astype(np.int8)
        prev=state[:-1]
        nxt=state[1:]
        p_uu=np.zeros(4);p_du=np.zeros(4);entropy=np.zeros(4)
        p_cond=np.zeros(4)
        for j in range(4):
            up_prev=prev[:,j]==1
            down_prev=~up_prev
            up_after_up=np.count_nonzero(nxt[up_prev,j])
            up_after_down=np.count_nonzero(nxt[down_prev,j])
            p_uu[j]=(1.+up_after_up)/(2.+np.count_nonzero(up_prev))
            p_du[j]=(1.+up_after_down)/(2.+np.count_nonzero(down_prev))
            entropy[j]=(np.count_nonzero(up_prev)*_entropy(p_uu[j])+
                        np.count_nonzero(down_prev)*_entropy(p_du[j]))/671.
            p_cond[j]=p_uu[j] if state[-1,j] else p_du[j]
        if np.any((p_cond<=0)|(p_cond>=1)) or np.any((entropy<0)|(entropy>1.+1e-12)):
            raise ValueError("KB_TRANSITION_PROBABILITY")
        m72=float(np.sum(market[t-71:t+1]))
        m24=float(np.sum(market[t-23:t+1]))
        mprev72=float(np.sum(market[t-95:t-23]))
        regime=("STRESS" if m72<-.025 else
                "RECOVERY" if m24>.012 and mprev72<0 else "NORMAL")
        score=np.maximum(p_cond-.5,0.)*np.maximum(1.-entropy,0.)*np.maximum(
            np.sum(net[t-71:t+1],axis=0),0.)
        if np.max(score)>0:
            experts[1,int(np.argmax(score))]=1.
            budgets[t,0]=.16
        if np.max(p_cond)-np.min(p_cond)>.015:
            long=int(np.argmax(p_cond));short=int(np.argmin(p_cond))
            if long!=short:
                experts[2,long]=.5;experts[2,short]=-.5
                budgets[t,1]=.12
        if regime in ("STRESS","RECOVERY"):
            chosen=int(np.argmax(p_du))
        else:
            chosen=int(np.argmax(p_cond*np.maximum(1.-entropy,0.)))
        experts[3,chosen]=1.
        budgets[t,2]=.12
        for path in range(5):
            b=budgets[t].copy()
            if path==0:b[:]=0.
            elif path>=2:b[path-2]=0.
            target=(1.-float(np.sum(b)))*core+b@experts[1:]
            if (not np.isfinite(target).all() or np.abs(target).sum()>1.+1e-10
                or np.sum(b)>.4+1e-12):
                raise ValueError("KB_GROSS_OR_FINITE")
            targets[t,path]=target
        regimes[t]=regime
        valid[t]=True
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
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("KB_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.+1e-10):
        raise ValueError("KB_GROSS")
    if not np.all(a[3][epochs]):
        raise ValueError("KB_VALIDITY")
    return True

if __name__=="__main__":
    assert static_check()
    print("KB_NATIVE_MARKOV_CAUSALITY_PASS")
