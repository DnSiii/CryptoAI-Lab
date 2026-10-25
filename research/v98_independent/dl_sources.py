#!/usr/bin/env python3
"""DL independent core-priority residual-capacity seven-slot source. Training only."""
import numpy as np
WARMUP=1440
GRID=168
BUDGETS={"RISK_ON":(3.4,.30,.24,.20),"MIXED":(2.4,.36,.30,.30),
         "RISK_OFF":(.75,.30,.32,.48)}
def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(q<0) or
        np.any((e!=0)&(e!=1))):
        raise ValueError("DL_INVALID_NATIVE_SOURCE")
    n=len(c);lc=np.log(c);native=r*e
    hourly=np.zeros_like(c);hourly[1:]=np.diff(lc,axis=0)
    signals=np.zeros((n,4,4));updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"MIXED",dtype="<U8");budgets=np.zeros((n,4))
    shadow=np.zeros((n,4));prev=np.zeros((4,4));pending=np.zeros(4)
    pair=lc[:,0]-lc[:,1]
    for t in range(1,n):
        shadow[t]=prev@(hourly[t]-native[t])-pending
        pending[:]=0.
        if t<WARMUP or (t-WARMUP)%GRID:continue
        net1008=lc[t]-lc[t-1008]-native[t-1007:t+1].sum(axis=0)
        net336=lc[t]-lc[t-336]-native[t-335:t+1].sum(axis=0)
        net168=lc[t]-lc[t-168]-native[t-167:t+1].sum(axis=0)
        ret72=lc[t]-lc[t-72];ret24=lc[t]-lc[t-24]
        hourly336=hourly[t-335:t+1]
        downside=np.sqrt(np.sum(np.minimum(hourly336,0.)**2,axis=0))
        score=np.where((net1008>0)&(net336>0),net1008/(.04+downside),0.)
        chosen=sorted((j for j in range(4) if score[j]>0),
                      key=lambda j:(-float(score[j]),j))[:2]
        if chosen:
            signals[t,0,chosen]=score[chosen]/score[chosen].sum()
        opportunities=[]
        for j in range(4):
            past_hi=float(h[t-312:t-72,j].max())
            new_q=float(q[t-71:t+1,j].mean())
            old_q=float(q[t-312:t-72,j].mean())
            if (c[t,j]>past_hi and ret72[j]>0 and net168[j]>0
                and new_q>1.05*old_q):
                opportunities.append((float((c[t,j]-past_hi)/past_hi),j))
        if opportunities:
            _,j=max(opportunities,key=lambda x:(x[0],-x[1]))
            signals[t,1,j]=1.
        baseline=pair[t-672:t-24]
        sd=float(baseline.std())
        z=float((pair[t]-baseline.mean())/sd) if sd>1e-6 else 0.
        turn=float(pair[t]-pair[t-24])
        funding_diff=float((native[t-167:t+1,0]-native[t-167:t+1,1]).sum())
        if abs(z)>1.0 and z*turn<0:
            direction=-float(np.sign(z))
            if direction*funding_diff<=.003:
                signals[t,2,0]=.5*direction
                signals[t,2,1]=-.5*direction
        recent_vol=float(np.sqrt(np.mean(hourly[t-71:t+1,0]**2)))
        old_vol=float(np.sqrt(np.mean(hourly[t-575:t-72,0]**2)))
        breadth_neg=int(np.count_nonzero(net168<0))
        if breadth_neg>=3 and net168[0]<-.035 and recent_vol>old_vol:
            signals[t,3,0]=-.5;signals[t,3,3]=-.5
        elif breadth_neg>=3 and np.count_nonzero(ret24>0)>=3:
            signals[t,3,0]=.5;signals[t,3,3]=.5
        breadth_pos=int(np.count_nonzero(net336>0))
        regime=("RISK_ON" if breadth_pos>=3 and net168[0]>0 else
                "RISK_OFF" if breadth_pos<=1 and net168[0]<0 else "MIXED")
        regimes[t]=regime;budgets[t]=BUDGETS[regime]
        if t>=WARMUP+504:
            trailing=shadow[t-503:t+1].sum(axis=0)
            for i in (1,2,3):
                if trailing[i]<=0:budgets[t,i]*=.25
        core=signals[t,0]
        for i in (1,2,3):
            if np.sum(np.maximum(signals[t,i]*core,0.))>.45:
                budgets[t,i]*=.5
        updates[t,:]=True
        for i in range(4):
            pending[i]=.0025*np.sum(np.abs(signals[t,i]-prev[i]))
            prev[i]=signals[t,i].copy()
    if np.any(np.sum(abs(signals),axis=2)>1.+1e-12):
        raise ValueError("DL_GROSS_SOURCE")
    if not np.allclose(signals[:,2,:].sum(axis=1),0.,atol=1e-12):
        raise ValueError("DL_RV_NOT_NEUTRAL")
    if not np.isfinite(budgets).all() or np.any(budgets<0):
        raise ValueError("DL_BUDGET_NONFINITE")
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
    print("DL_CAUSAL_RESIDUAL_CAPACITY_SOURCE_STATIC_PASS")
