#!/usr/bin/env python3
"""KD causal seven-slot native trade-size fragmentation composition, no PnL imports."""
from __future__ import annotations
import numpy as np
WARMUP=744
CLOCK=168
GROSS={"NORMAL":.88,"STRESS":.70,"RECOVERY":.82}
PATHS=("KD_core_only","KD_full","KD_minus_opportunity","KD_minus_RV","KD_minus_stress")

def bundle(opening,high,low,close,rate,event,quote,trade_count):
    o,h,l,c,r,e,q,k=[np.asarray(x,dtype=float) for x in
                      (opening,high,low,close,rate,event,quote,trade_count)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q,k)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q,k)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any(k<0) or np.any(k!=np.floor(k)) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("KD_INVALID_NATIVE_TRADE_COUNT_OR_OHLC")
    n=len(c)
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    market=np.mean(net,axis=1)
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    budgets=np.zeros((n,3),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        downside=np.maximum(np.sqrt(np.mean(np.minimum(net[t-335:t+1],0.)**2,axis=0)),.002)
        mom672=np.sum(net[t-671:t+1],axis=0)
        leaders=np.argsort(-(mom672/downside),kind="stable")[:2]
        core=np.zeros(4)
        inv=1./downside[leaders];core[leaders]=inv/inv.sum()
        experts=np.zeros((4,4))
        m72=float(np.sum(market[t-71:t+1]))
        m24=float(np.sum(market[t-23:t+1]))
        mprev72=float(np.sum(market[t-95:t-23]))
        regime=("STRESS" if m72<-.04 else
                "RECOVERY" if m24>.015 and mprev72<0 else "NORMAL")
        good=bool(np.all(k[t-671:t+1]>0) and np.all(q[t-671:t+1]>0))
        valid[t]=good
        if good:
            tickets=q[t-671:t+1]/k[t-671:t+1]
            baseline=np.median(tickets[:624],axis=0)
            short=np.mean(tickets[624:],axis=0)
            good=bool(np.all(baseline>0) and np.isfinite(baseline).all() and
                      np.all(short>0) and np.isfinite(short).all())
            valid[t]=good
        if good:
            shock=np.log(short/baseline)
            r48=np.sum(net[t-47:t+1],axis=0)
            opp=np.maximum(shock,0.)*np.maximum(r48,0.)
            if np.max(opp)>0:
                experts[1,int(np.argmax(opp))]=1.
                budgets[t,0]=.18
            if np.max(shock)-np.min(shock)>.10:
                top=int(np.argmax(shock));bottom=int(np.argmin(shock))
                experts[2,top]=.5;experts[2,bottom]=-.5
                budgets[t,1]=.12
            if regime=="STRESS":choose=int(np.argmax(shock))
            elif regime=="RECOVERY":choose=int(np.argmin(shock))
            else:
                r168=np.abs(np.sum(net[t-167:t+1],axis=0))
                choose=int(np.argmax(shock-.25*r168))
            experts[3,choose]=1.
            budgets[t,2]=.10
        for path in range(5):
            b=budgets[t].copy()
            if path==0:b[:]=0.
            elif path>=2:b[path-2]=0.
            target=(1.-float(np.sum(b)))*core+b@experts[1:]
            if not np.isfinite(target).all() or np.abs(target).sum()>1.+1e-10 or np.sum(b)>.4+1e-12:
                raise ValueError("KD_GROSS_OR_FINITE")
            targets[t,path]=target
        if not good and not np.allclose(targets[t],targets[t,0]):
            raise ValueError("KD_SOURCE_QUARANTINE_LEAK")
        regimes[t]=regime;updates[t]=True
    return targets,updates,regimes,valid,budgets

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    k=1000+np.floor(100*np.sin(t[:,None]/41.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q,k)
    cc,oo,hh,ll,qq,rr,kk=[z.copy() for z in (c,o,h,l,q,r,k)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.;kk[3200:]*=3.
    b=bundle(oo,hh,ll,cc,rr,e,qq,kk)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("KD_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if np.any(np.abs(a[0][epochs]).sum(axis=2)>1.+1e-10):
        raise ValueError("KD_GROSS")
    bad=k.copy();bad[700,2]=0.
    gap=bundle(o,h,l,c,r,e,q,bad)
    if gap[3][WARMUP] or not np.allclose(gap[0][WARMUP],gap[0][WARMUP,0]):
        raise ValueError("KD_NATIVE_ZERO_TRADE_QUARANTINE")
    if not np.all(a[3][epochs]):
        raise ValueError("KD_SYNTHETIC_COVERAGE")
    return True

if __name__=="__main__":
    assert static_check()
    print("KD_CAUSAL_NATIVE_TRADE_SIZE_AND_ZERO_TRADE_MASK_PASS")
