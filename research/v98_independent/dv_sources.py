#!/usr/bin/env python3
"""DV independent cash-first net-carry rotation; 7 slots; TRAINING only."""
import numpy as np
WARMUP=1440
GRID=168
BUDGETS={"RISK_ON":(3.2,.20,.16,.16),
         "MIXED":(2.6,.16,.18,.22),
         "RISK_OFF":(.7,.12,.18,.40)}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DV_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8");budgets=np.zeros((n,4))
    for t in range(WARMUP,n,GRID):
        ret6=lc[t]-lc[t-6]
        ret24=lc[t]-lc[t-24]
        ret72=lc[t]-lc[t-72]
        net336=lc[t]-lc[t-336]-native[t-335:t+1].sum(axis=0)
        positive=[j for j in range(4) if net336[j]>0]
        breadth=len(positive)
        regime=("RISK_ON" if net336[0]>0 and breadth>=2 else
                "RISK_OFF" if net336[0]<-.03 and breadth<=1 else "MIXED")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        # Cash-first native net-growth leadership; not DU's signed market basket.
        ranked=sorted(positive,key=lambda j:(-float(net336[j]),j))
        if len(ranked)>=2:
            signals[t,0,ranked[0]]=.6
            signals[t,0,ranked[1]]=.4
        elif len(ranked)==1:
            signals[t,0,ranked[0]]=1.
        # Pullback recovery inside established positive native-net trend.
        candidates=[]
        for j in positive:
            qr=float(q[t-71:t+1,j].mean()/max(q[t-312:t-72,j].mean(),1.))
            edge=-.5*float(ret24[j])-.003
            if ret24[j]<-.005 and ret6[j]>.001 and qr>.75 and edge>0:
                candidates.append((float(net336[j]),j))
        if candidates:
            _,j=max(candidates,key=lambda z:(z[0],-z[1]))
            signals[t,1,j]=1.
        # Funding carry only; no ex-post sign, price ranking or price-spread rescue.
        fund64=native[t-63:t+1].sum(axis=0)
        cheap=min(range(4),key=lambda j:(float(fund64[j]),j))
        dear=max(range(4),key=lambda j:(float(fund64[j]),-j))
        projected=(float(fund64[dear])-float(fund64[cheap]))*168./64.
        if cheap!=dear and projected>.0008:
            signals[t,2,cheap]=.5
            signals[t,2,dear]=-.5
        # Symmetric stress/recovery insurance, independent of core leader.
        if ret72[0]<-.025 and ret6[0]<0:
            signals[t,3,0]=-.5;signals[t,3,3]=-.5
        elif ret72[0]<-.01 and ret6[0]>.005:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        updates[t,:]=True
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DV_SOURCE_GROSS")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DV_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DV_BUDGET_INVALID")
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
    for i in range(4):
        assert np.array_equal(a[i][:3200],b[i][:3200]),i
    assert not a[0][:WARMUP].any()
    assert np.all(np.sum(abs(a[0]),axis=2)<=1.+1e-12)
    return True
if __name__=="__main__":
    assert static_check()
    print("DV_CASH_FIRST_NET_CARRY_STATIC_PASS")
