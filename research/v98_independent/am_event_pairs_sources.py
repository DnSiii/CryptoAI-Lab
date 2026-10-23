#!/usr/bin/env python3
"""AM complete signed event-time trend, compression breakout and paired reversion."""
from __future__ import annotations
import numpy as np

WARMUP=2016

def source_bundle(close,high,low,funding_rate,funding_event,quote_volume):
    c,h,l,r,e,q=(np.asarray(x,dtype=np.float64) for x in
                  (close,high,low,funding_rate,funding_event,quote_volume))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (h,l,r,e,q))
        or any(not np.isfinite(x).all() for x in (c,h,l,r,e,q))
        or np.any(c<=0) or np.any(l<=0) or np.any(l>c) or np.any(h<c)
        or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("AM_CLEAN4_INPUT")
    n=len(c)
    logc=np.log(c)
    lr=np.diff(logc,axis=0,prepend=logc[:1])
    growth=np.zeros_like(c)
    opportunity=np.zeros_like(c)
    relative=np.zeros_like(c)
    stress=np.zeros_like(c)
    states=np.full(n,"CHOP",dtype="<U6")
    trend_position=np.zeros(4)
    trend_entry=np.full(4,-10**9,dtype=np.int64)
    opp_position=np.zeros(4)
    opp_until=np.zeros(4,dtype=np.int64)
    pair_state=np.zeros(2)
    crisis_until=-1
    last_crisis=-10**9
    recovery_until=-1
    recovered=True
    for t in range(WARMUP,n):
        upper=np.max(h[t-480:t],axis=0)
        lower=np.min(l[t-480:t],axis=0)
        exit_hi=np.max(h[t-240:t],axis=0)
        exit_lo=np.min(l[t-240:t],axis=0)
        for j in range(4):
            if trend_position[j]>0 and t-trend_entry[j]>=168 and c[t]<exit_lo[j]:
                trend_position[j]=0.
            elif trend_position[j]<0 and t-trend_entry[j]>=168 and c[t]>exit_hi[j]:
                trend_position[j]=0.
            if trend_position[j]==0:
                if c[t]>upper[j]:
                    trend_position[j]=1.
                    trend_entry[j]=t
                elif c[t]<lower[j]:
                    trend_position[j]=-1.
                    trend_entry[j]=t
        gross=float(np.abs(trend_position).sum())
        if gross:
            growth[t]=trend_position/gross
        # Compression window ends before the current 72h displacement.
        prior72=np.sqrt(np.mean(lr[t-144:t-72]**2,axis=0))
        prior504=np.sqrt(np.mean(lr[t-648:t-144]**2,axis=0))
        displacement=logc[t]-logc[t-72]
        compression=prior72<.70*np.maximum(prior504,1e-8)
        trigger=compression&(np.abs(displacement)>2.*np.maximum(prior72,1e-8)*np.sqrt(72.))
        for j in range(4):
            if t>=opp_until[j]:
                opp_position[j]=0.
                if trigger[j]:
                    opp_position[j]=np.sign(displacement[j])
                    opp_until[j]=t+96
        gross=float(np.abs(opp_position).sum())
        if gross:
            opportunity[t]=opp_position/gross
        # Signed beta-agnostic dollar-neutral ratio pairs; independent histories.
        for pair,(i,j) in enumerate(((0,1),(2,3))):
            ratio=logc[:,i]-logc[:,j]
            hist=ratio[t-504:t]
            mu=float(hist.mean())
            sigma=max(float(hist.std()),1e-5)
            z=(float(ratio[t])-mu)/sigma
            if pair_state[pair]!=0 and abs(z)<.50:
                pair_state[pair]=0.
            if pair_state[pair]==0 and abs(z)>1.75:
                pair_state[pair]=-float(np.sign(z))
            relative[t,i]=.25*pair_state[pair]
            relative[t,j]=-.25*pair_state[pair]
        r72=logc[t]-logc[t-72]
        r168=logc[t]-logc[t-168]
        r336=logc[t]-logc[t-336]
        market72=float(np.median(r72))
        market168=float(np.median(r168))
        market336=float(np.median(r336))
        breadth=int(np.count_nonzero(r168>0))
        if market72<-.10:
            crisis_until=t+72
            last_crisis=t
            recovery_until=-1
            recovered=False
        elif (not recovered and t-last_crisis<=336 and market72>.08):
            recovery_until=t+96
            recovered=True
        if t<crisis_until:
            stress[t]=-np.ones(4)/4.
        elif t<recovery_until:
            stress[t]=np.ones(4)/4.
        if market72<-.10:
            states[t]="STRESS"
        elif market336>.06 and breadth>=3:
            states[t]="BULL"
        elif market336<-.06 and breadth<=1:
            states[t]="BEAR"
    return growth,opportunity,relative,stress,{"state":states}

def causal_check():
    t=np.arange(2250,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0003,.0004,.0002,.0005]]))
    h,l=c*1.003,c*.997
    r=np.zeros_like(c);e=np.zeros_like(c);e[::8]=1.
    q=np.full_like(c,1e8)
    before=source_bundle(c,h,l,r,e,q)
    changed=c.copy();changed[-24:]*=1.2
    after=source_bundle(changed,np.maximum(h,changed),np.minimum(l,changed),r,e,q)
    for a,b in zip(before[:4],after[:4]):
        assert np.array_equal(a[:-24],b[:-24])
        assert np.isfinite(a).all()
        assert np.all(np.abs(a).sum(axis=1)<=1.+1e-12)
    assert np.array_equal(before[4]["state"][:-24],after[4]["state"][:-24])
    return True

if __name__=="__main__":
    assert causal_check()
    print("AM_SIGNED_CAUSAL_SOURCE_PASS")
