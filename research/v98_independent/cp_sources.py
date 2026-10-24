#!/usr/bin/env python3
"""CP seven-slot causal sources: volatility-conditioned trend, absorption rebound,
BTC-residual dispersion and systemic tail reacceleration. Completed close t -> t+1 open.
"""
from __future__ import annotations
import numpy as np

WARMUP=2160
GRID=168
BUDGETS={
 "RISK_ON":np.array([1.80,.40,.25,.20]),
 "MIXED":np.array([1.35,.40,.35,.35]),
 "RISK_OFF":np.array([.65,.30,.35,.55]),
}

def bundle(close,rate,event,quote):
    c=np.asarray(close,dtype=float)
    r=np.asarray(rate,dtype=float)
    e=np.asarray(event,dtype=float)
    q=np.asarray(quote,dtype=float)
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (r,e,q))
        or len(c)<=WARMUP or any(not np.isfinite(x).all() for x in (c,r,e,q))
        or np.any(c<=0) or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("CP_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c)
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8")
    for t in range(WARMUP,n,GRID):
        r168=lc[t]-lc[t-168]
        r48=lc[t]-lc[t-48]
        r672=lc[t]-lc[t-672]
        breadth_up=int(np.count_nonzero(r168>0))
        breadth_down=int(np.count_nonzero(r168<0))
        regimes[t]=("RISK_ON" if r168[0]>0 and breadth_up>=3 else
                    "RISK_OFF" if r168[0]<0 and breadth_down>=3 else "MIXED")
        returns672=np.diff(lc[t-672:t+1],axis=0)
        if (t-WARMUP)%336==0:
            vol=np.std(returns672,axis=0)
            quality=r672/(np.sqrt(672.)*np.maximum(vol,1e-12))
            eligible=[j for j in range(4) if r672[j]>0 and r168[j]>0 and quality[j]>.25]
            ranked=sorted(eligible,key=lambda j:(-quality[j],j))
            if len(ranked)==1:
                signals[t,0,ranked[0]]=1.
            elif len(ranked)>=2:
                signals[t,0,ranked[0]]=.60
                signals[t,0,ranked[1]]=.40
            updates[t,0]=True
        candidates=[]
        for j in (2,3):
            last=float(np.mean(q[t-47:t+1,j]))
            previous=float(np.mean(q[t-383:t-47,j]))
            if r168[j]<-.035 and r48[j]>0 and last>1.10*max(previous,1e-12):
                candidates.append(j)
        if candidates:
            chosen=sorted(candidates,key=lambda j:(-r48[j],j))[0]
            signals[t,1,chosen]=1.
        updates[t,1]=True
        btc=returns672[:,0]
        btc_var=float(np.dot(btc-btc.mean(),btc-btc.mean()))
        beta=((returns672-returns672.mean(axis=0)).T@(btc-btc.mean()))/max(btc_var,1e-12)
        residual=r168-beta*r168[0]
        recent=np.diff(lc[t-168:t+1],axis=0)
        correlations={}
        for j in (1,2,3):
            sd=float(np.std(recent[:,0])*np.std(recent[:,j]))
            correlations[j]=(float(np.mean((recent[:,0]-recent[:,0].mean())*
                                           (recent[:,j]-recent[:,j].mean())))/max(sd,1e-12))
        valid=[j for j in (1,2,3) if correlations[j]>.35]
        positives=[j for j in valid if residual[j]>0]
        negatives=[j for j in valid if residual[j]<0]
        if positives and negatives:
            best=sorted(positives,key=lambda j:(-residual[j],j))[0]
            worst=sorted(negatives,key=lambda j:(residual[j],j))[0]
            signals[t,2,best]=.5
            signals[t,2,worst]=-.5
        updates[t,2]=True
        drawdown=1.-c[t,0]/float(np.max(c[t-671:t+1,0]))
        if drawdown>.10 and float(np.mean(r48))>.025 and float(np.mean(r168))<0:
            signals[t,3,0]=.60
            signals[t,3,1]=.40
        updates[t,3]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("CP_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("CP_RV_NOT_DOLLAR_NEUTRAL")
    return signals,updates,regimes

def static_check():
    n=3500;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])
                 +.05*np.sin(t[:,None]/97.+np.arange(4)))
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    s,m,z=bundle(c,r,e,q)
    changed=c.copy();changed[2900:]*=1.9
    rates=r.copy();rates[2900:]*=-1.
    volumes=q.copy();volumes[2900:]*=4.
    s2,m2,z2=bundle(changed,rates,e,volumes)
    assert np.array_equal(s[:2900],s2[:2900])
    assert np.array_equal(m,m2)
    assert np.array_equal(z[:2900],z2[:2900])
    assert not s[:WARMUP].any()
    assert np.all(np.sum(abs(s),axis=2)<=1.+1e-12)
    assert np.allclose(s[:,2,:].sum(axis=1),0.)
    assert set(np.unique(z)).issubset(set(BUDGETS))
    return True

if __name__=="__main__":
    assert static_check()
    print("CP_CAUSAL_COVARIANCE_ABSORPTION_SOURCE_PASS")
