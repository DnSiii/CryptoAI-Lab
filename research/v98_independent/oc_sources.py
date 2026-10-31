#!/usr/bin/env python3
"""V98 OC new orthogonal efficiency, expansion, beta-residual, crash-convexity sources. Training only."""
import numpy as np
HOURS=18288;WARMUP=744;STEP=168;CORE_STEP=672
NAMES=("Opportunity","Relative_Value","Stress_Recovery")
BOOKS={"OC_full":(0,1,2,3),"OC_core_only":(0,),
       "OC_minus_opportunity":(0,2,3),"OC_minus_RV":(0,1,3),
       "OC_minus_stress":(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(x) for x in (o,h,l,c,q,rate,event)]
    if any(x.shape!=(HOURS,4) for x in (o,h,l,c,q,rate,event)):
        raise ValueError("OC_SOURCE_SHAPE")
    if any(not np.isfinite(x).all() for x in (o,h,l,c,q,rate)):
        raise ValueError("OC_SOURCE_NONFINITE")
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError("OC_SOURCE_OHLC")
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError("OC_FUNDING_CALENDAR")
    p=np.log(c);r=np.diff(p,axis=0,prepend=p[:1])
    raw=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool);held=np.zeros((4,4))
    for t in range(WARMUP,HOURS):
        if (t-WARMUP)%STEP==0:
            if t%8 or np.any(q[t]<=0) or not np.all(event[t]):
                raise ValueError("OC_DECISION_CALENDAR_"+str(t))
            r672=p[t]-p[t-672];r336=p[t]-p[t-336]
            r168=p[t]-p[t-168];r72=p[t]-p[t-72];r24=p[t]-p[t-24]
            if (t-WARMUP)%CORE_STEP==0:
                held[0]=0.
                annual=np.std(r[t-167:t+1],axis=0)*np.sqrt(24*365)
                eligible=[j for j in range(4) if r672[j]>0 and r168[j]>0]
                eligible.sort(key=lambda j:(-r672[j]/(1+4*annual[j]),j))
                if eligible:
                    held[0,eligible[0]]=.52
                    if len(eligible)>1:held[0,eligible[1]]=.12
                elif r168[0]<0 and np.count_nonzero(r168<0)>=3:
                    held[0,0]=-.38
                updates[t,0]=True
            held[1:]=0.
            expansion=np.median(np.abs(r[t-23:t+1]),axis=0)/np.maximum(
                np.median(np.abs(r[t-167:t-23]),axis=0),1e-12)
            volume=np.sum(q[t-167:t+1],axis=0)/np.maximum(np.sum(q[t-335:t-167],axis=0),1e-12)
            choices=[j for j in range(4) if expansion[j]>1.6 and abs(r24[j])>.025 and volume[j]>1.]
            if choices:
                j=min(choices,key=lambda k:(-abs(r24[k])*expansion[k],k))
                held[1,j]=.12 if r24[j]>0 else -.12
            btc=r[t-335:t+1,0]
            var=float(np.var(btc))
            if var>1e-12:
                betas={j:float(np.clip(np.mean((r[t-335:t+1,j]-np.mean(r[t-335:t+1,j]))*(btc-np.mean(btc)))/var,.2,2.)) for j in (1,2,3)}
                residual={j:float(r168[j]-betas[j]*r168[0]) for j in betas}
                j=min((1,2,3),key=lambda k:(-abs(residual[k]),k))
                if abs(residual[j])>.06:
                    sign=1 if residual[j]>0 else -1
                    held[2,j]=-.075*sign
                    held[2,0]=.075*sign*min(betas[j],1.)
            if r72[0]<-.07 and np.count_nonzero(r72<0)>=3:
                held[3,0]=-.14
            elif r168[0]<-.10 and r24[0]>.025 and np.count_nonzero(r24[1:]>0)>=2:
                held[3,0]=.14
            risk_on=bool(r336[0]>0 and np.count_nonzero(r168>0)>=3)
            held[1:]*=np.array([1.,.75,.5] if risk_on else [.75,1.,1.])[:,None]
            if np.any(np.abs(held).sum(axis=1)>.84+1e-10):
                raise ValueError("OC_RAW_MODULE_BUDGET")
            updates[t,1:]=True
            active[t]=np.any(np.abs(held[1:])>1e-12,axis=1)
        raw[t]=held
    return raw,updates,active
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00004*t*(1+j/8)+.07*np.sin(t/41+j))
    o=c*(1-.001*np.sin(t/13+j))
    h=np.maximum(o,c)*1.005;l=np.minimum(o,c)*.995
    q=np.ones_like(c)*1e6
    rate=np.tile(np.array([[.0001,.0002,-.0001,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=2.;changed[5][14000:]*=-1.
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError("OC_FUTURE_LEAK")
    if np.any((np.abs(np.diff(a[0],axis=0)).sum(axis=(1,2))>1e-12)&~np.any(a[1][1:],axis=1)):
        raise ValueError("OC_SILENT_TARGET_CHANGE")
    if int(a[1][:,0].sum())!=27 or int(a[1][:,1].sum())!=105:
        raise ValueError("OC_CLOCK_COUNT")
    return True
if __name__=="__main__":
    assert synthetic_causality()
    print("OC_CAUSAL_SYNTHETIC_PASS_NOT_PNL")
