#!/usr/bin/env python3
"""V98 JB causal regime-conditioned multiplicative wealth-regret seven-slot source. Training only."""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=168
GROSS={"NORMAL":1.0,"STRESS":.85,"RECOVERY":.95}
PATHS=("JB_core_only","JB_full","JB_minus_opportunity","JB_minus_RV","JB_minus_stress")
PRIOR=np.array([.70,.12,.10,.08],dtype=float)
FLOOR=.04
FORGET=.85
TEMPERATURE=3.
SHADOW_TURNOVER_COST=.0008

def _normalize(v):
    v=np.asarray(v,dtype=float)
    if not np.isfinite(v).all():raise ValueError("JB_NONFINITE_TARGET")
    gross=float(np.abs(v).sum())
    return v/gross if gross>1e-12 else np.zeros(4)

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(z,dtype=float) for z in
                    (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(z.shape!=c.shape or not np.isfinite(z).all()
            for z in (o,h,l,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JB_INVALID_NATIVE_SOURCE")
    n=len(c)
    ret=np.zeros_like(c)
    ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    forecasts=np.zeros((n,4,4),dtype=float)
    score=np.zeros(4,dtype=float)
    prev_epoch=None
    for t in range(WARMUP,n,CLOCK):
        x672=net[t-671:t+1]
        x168=net[t-167:t+1]
        x48=net[t-47:t+1]
        vol672=np.maximum(np.std(x672,axis=0),.002)
        vol168=np.maximum(np.std(x168,axis=0),.002)
        slow=x672.sum(axis=0)
        short=x48.sum(axis=0)
        medium=x168.sum(axis=0)
        dd=np.log(c[t]/np.max(c[t-167:t+1],axis=0))
        raw=np.maximum(slow,0.)/vol672
        if raw.sum()<1e-12:raw=1./vol672
        core=raw/raw.sum()
        corr=np.corrcoef(x168,rowvar=False)
        off=corr[np.triu_indices(4,1)]
        avgcorr=float(np.mean(off)) if np.isfinite(off).all() else 0.
        regime=("STRESS" if np.median(medium)<0 and avgcorr>.55 else
                "RECOVERY" if np.median(short)>0 and np.median(dd)<-.07 else "NORMAL")
        regimes[t]=regime
        safe=np.all(q[t-167:t+1]>0,axis=0)
        good=bool(np.all(safe))
        valid[t]=good
        if good:
            participation=np.clip(np.mean(q[t-47:t+1],axis=0)/
                                  np.maximum(np.mean(q[t-167:t+1],axis=0),1e-12),
                                  .5,1.5)
            opportunity=(short/48.)/vol168*participation
            opp=np.zeros(4);opp[int(np.argmax(opportunity))]=1.
            residual=medium-np.median(medium)
            rv=np.zeros(4)
            hi=int(np.argmax(residual));lo=int(np.argmin(residual))
            if hi!=lo:rv[hi]=.5;rv[lo]=-.5
            else:rv[0]=.5;rv[1]=-.5
            downside=np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0))
            stress=np.zeros(4)
            if regime=="RECOVERY":
                choice=int(np.argmax(short-dd))
            else:
                choice=int(np.argmin(downside))
            stress[choice]=1.
            experts=np.array([core,opp,rv,stress])
            forecasts[t]=experts
            if prev_epoch is not None:
                # Only previous completed-epoch targets receive strictly subsequent
                # realized native funding-adjusted price increments, never current target.
                realized=net[prev_epoch+1:t+1]
                simple=np.expm1(realized)
                shadow_hour=np.clip(1.+simple@forecasts[prev_epoch].T,.05,None)
                utility=np.log(shadow_hour).sum(axis=0)
                turnover=np.abs(experts-forecasts[prev_epoch]).sum(axis=1)
                score=FORGET*score+utility-SHADOW_TURNOVER_COST*turnover
            logits=np.log(PRIOR)+TEMPERATURE*np.clip(score,-.15,.15)
            weight=np.exp(logits-np.max(logits))
            weight/=weight.sum()
            weight=np.maximum(weight,FLOOR)
            weight/=weight.sum()
            for i in range(5):
                active=np.ones(4)
                if i==0:active[1:]=0.
                elif i>=2:active[i-1]=0.
                w=weight*active
                w/=w.sum()
                targets[t,i]=_normalize(w@experts)
            prev_epoch=t
        else:
            # No financed optional sleeve with any missing quote in 168h.
            fallback=_normalize(core*safe)
            targets[t]=fallback
            forecasts[t,0]=fallback
            prev_epoch=None
        updates[t]=True
        if (not np.isfinite(targets[t]).all() or
            not np.all(np.isclose(np.abs(targets[t]).sum(axis=1),1.,atol=1e-10)|
                       np.isclose(np.abs(targets[t]).sum(axis=1),0.,atol=1e-10)) or
            np.any(np.abs(targets[t])>1.0000000001)):
            raise ValueError("JB_BUDGET_OR_QUARANTINE")
    return targets,updates,regimes,valid,forecasts

def static_check():
    n=4000
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);r[:,2]=-.0001
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("JB_FUTURE_MUTATION_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.allclose(np.abs(a[0][epochs]).sum(axis=2),1.,atol=1e-10):
        raise ValueError("JB_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    gap=bundle(o,h,l,c,r,e,qgap)
    if gap[3][WARMUP] or np.any(gap[0][WARMUP,:,2]) or not np.allclose(
        gap[0][WARMUP],gap[0][WARMUP,0]):
        raise ValueError("JB_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("JB_CAUSAL_WEALTH_REGRET_AND_QUARANTINE_PASS")
