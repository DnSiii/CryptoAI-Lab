#!/usr/bin/env python3
"""GX independent seven-slot source: two-asset growth, quote-confirmed opportunity,
native funding relative value, cross-asset recovery overlay, risk-aware allocator.
Only completed-close t information; next-open execution belongs to gx_30cell.
"""
from __future__ import annotations
import numpy as np

WARMUP=744
CLOCK=168
GROSS={"TREND":2.00,"TRANSITION":1.60,"STRESS":1.25}
PRIOR=np.array([.60,.20,.20,0.],dtype=float)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                    (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("GX_INVALID_PINNED_SOURCE")
    n=len(c);lc=np.log(c)
    funding=np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"TRANSITION",dtype="<U12")
    budgets=np.zeros((n,4),dtype=float)
    def native(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])
    for t in range(WARMUP,n,CLOCK):
        net24,net72,net336,net672=(native(t,w) for w in (24,72,336,672))
        hourly=np.diff(lc[t-168:t+1],axis=0)
        vol=np.maximum(np.std(hourly,axis=0),.002)
        growth=np.argsort(-net672/vol,kind="stable")[:2]
        signals[t,0,growth[0]]=.65
        signals[t,0,growth[1]]=.35
        recent_q=np.mean(q[t-47:t+1],axis=0)
        prior_q=np.mean(q[t-95:t-47],axis=0)
        ratio=np.clip((recent_q+1.)/(prior_q+1.),.5,2.)
        signals[t,1,int(np.argmax(net24*ratio))]=1.
        burden=funding[t+1]-funding[t-167]
        signals[t,2,int(np.argmax(-burden/vol))]=1.
        path=c[t-168:t+1]
        drawdown=np.maximum(0.,1.-c[t]/np.max(path,axis=0))
        eligible=(net24>0)&(drawdown>=.08)
        if float(np.median(net72))<-.02 and np.any(eligible):
            score=np.where(eligible,net24+drawdown,-np.inf)
            signals[t,3,int(np.argmax(score))]=1.
        breadth=int(np.count_nonzero(net336>0))
        regimes[t]=("STRESS" if float(np.median(net72))<-.03 or breadth<=1 else
                    "TREND" if breadth>=3 else "TRANSITION")
        # Historical downside bounds exclude current candle; known before decision.
        down=np.maximum(.40,np.max(1.-l[t-336:t]/o[t-336:t],axis=0))
        risk=np.array([float(signals[t,i]@down) for i in range(3)])
        multiplier=np.clip(.40/risk,.70,1.30)
        budgets[t,:3]=PRIOR[:3]*multiplier
        updates[t]=True
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            np.any(signals[t]<0) or np.any(budgets[t,:3]<=0) or
            not np.allclose(signals[t,:3].sum(axis=1),1.,atol=1e-12) or
            signals[t,3].sum() not in (0.,1.)):
            raise ValueError("GX_INVALID_FINANCED_BOOK")
    return signals,updates,regimes,budgets

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):
        assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    ix=np.arange(WARMUP,n,CLOCK)
    assert np.all(a[1][ix].all(axis=1))
    assert np.allclose(a[0][ix,:3].sum(axis=2),1.)
    assert np.all(a[0][ix,0]>=(0.))
    assert np.all(a[3][ix,:3]>0)
    return True
if __name__=="__main__":
    assert static_check()
    print("GX_CAUSAL_MULTI_ASSET_GROWTH_RECOVERY_STATIC_PASS")
