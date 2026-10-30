#!/usr/bin/env python3
"""DR independent causal leadership / catch-up / native carry / crash-recovery seven-slot source.
Preregistered 2023-2024 training only; no rejected engine imports or 2025+.
"""
import numpy as np

WARMUP=1440
GRID=168
BUDGETS={"RISK_ON":(2.8,.30,.14,.18),
         "MIXED":(2.4,.28,.18,.20),
         "RISK_OFF":(1.1,.12,.22,.30)}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DR_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8");budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        ret24=lc[t]-lc[t-24]
        ret72=lc[t]-lc[t-72]
        ret168=lc[t]-lc[t-168]
        ret672=lc[t]-lc[t-672]
        carry168=native[t-167:t+1].sum(axis=0)
        carry672=native[t-671:t+1].sum(axis=0)
        net168=ret168-carry168
        net672=ret672-carry672
        breadth=int(np.count_nonzero(net168>0))
        regime=("RISK_ON" if net168[0]>.02 and breadth>=3 else
                "RISK_OFF" if net168[0]<-.06 and breadth<=1 else "MIXED")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        # Growth: two strongest causal net-carry multiweek leaders; rank is
        # fixed from completed historical returns, never 2023/24 annual winners.
        score=.65*net672+.35*net168
        order=sorted(range(4),key=lambda j:(-float(score[j]),j))
        if regime!="RISK_OFF":
            signals[t,0,order[0]]=.75
            signals[t,0,order[1]]=.25
        elif score[order[0]]>0:
            signals[t,0,order[0]]=1.
        # Opportunity: a laggard's catch-up acceleration inside a still
        # functioning BTC liquidity regime. Not range-breakout or momentum leader.
        eligible=[]
        median=float(np.median(net168))
        for j in range(4):
            qr=float(q[t-71:t+1,j].mean()/max(q[t-312:t-72,j].mean(),1.))
            if (net168[j]<median and ret24[j]>.008 and
                ret72[j]>.01 and net168[0]>-.02 and qr>.85):
                eligible.append((float(ret24[j]-.25*ret168[j]),j))
        if eligible:
            _,j=max(eligible,key=lambda z:(z[0],-z[1]))
            signals[t,1,j]=1.
        # RV: native perpetual carry dispersion, not price-spread reversion
        # nor strongest-minus-weakest price momentum. Funding-cheap long,
        # funding-rich short only when recent relative price is not collapsing.
        cheap=int(np.argmin(carry168));rich=int(np.argmax(carry168))
        if (cheap!=rich and carry168[rich]-carry168[cheap]>.0005 and
            net168[cheap]>net168[rich]-.04):
            signals[t,2,cheap]=.5;signals[t,2,rich]=-.5
        # Stress/recovery: a small conditional crash continuation hedge
        # followed by distinct reversal participation, not permanent beta.
        if ret168[0]<-.04 and ret24[0]<-.005:
            signals[t,3,0]=-.5;signals[t,3,3]=-.5
        elif ret168[0]<-.03 and ret24[0]>.01:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        elif ret72[0]<-.035 and ret24[0]>.01:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DR_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DR_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DR_BUDGET_NONFINITE")
    return signals,updates,regimes,budgets

def static_check():
    n=4300;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2=c.copy();o2=o.copy();h2=h.copy();l2=l.copy()
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2=q.copy();q2[3200:]*=4.
    r2=r.copy();r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(4):assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.all(np.sum(abs(a[0]),axis=2)<=1.+1e-12)
    return True

if __name__=="__main__":
    assert static_check()
    print("DR_NET_LEADERSHIP_CATCHUP_NATIVE_CARRY_STATIC_PASS")
