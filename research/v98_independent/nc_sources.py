#!/usr/bin/env python3
"""V98 NC cross-sectional growth, path efficiency, residual momentum, BTC stress."""
import numpy as np
HOURS=18288;WARMUP=744
NAMES=('Opportunity','Relative_Value','Stress_Recovery')
MINIMUM=(12,12,4)
BOOKS={'NC_full':(0,1,2,3),'NC_core_only':(0,),
       'NC_minus_opportunity':(0,2,3),'NC_minus_RV':(0,1,3),
       'NC_minus_stress':(0,1,2)}
def bundle(o,h,l,c,q,rate,event):
    o,h,l,c,q,rate,event=[np.asarray(z) for z in (o,h,l,c,q,rate,event)]
    if any(z.shape!=(HOURS,4) for z in (o,h,l,c,q,rate,event)):raise ValueError('NC_SHAPE')
    if any(not np.isfinite(z).all() for z in (o,h,l,c,q,rate)):raise ValueError('NC_NONFINITE')
    if np.any(l<=0) or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(q<0):
        raise ValueError('NC_OHLC')
    if not np.all(event[::8]) or np.any(event[np.arange(HOURS)%8!=0]):
        raise ValueError('NC_FUNDING_CALENDAR')
    p=np.log(c);r=np.diff(p,axis=0,prepend=p[:1])
    target=np.zeros((HOURS,4,4));updates=np.zeros((HOURS,4),bool)
    active=np.zeros((HOURS,3),bool);valid=np.zeros(HOURS,bool)
    state=np.zeros((4,4));prev=np.zeros((4,4));mult=np.ones(3)
    for t in range(WARMUP,HOURS):
        k=t-WARMUP;good=bool(np.all(q[t]>0));valid[t]=good
        if k%672==0:
            if not good:raise ValueError('NC_CORE_ZERO_SCHEDULED_QUOTE_'+str(t))
            ret336=p[t]-p[t-336]
            ranking=np.argsort(-ret336,kind='stable')
            state[0]=0.
            if np.count_nonzero(ret336>0)>=2:
                state[0,int(ranking[0])]=.48
                state[0,int(ranking[1])]=.18
            else:
                state[0,0]=.32;state[0,1]=.08
        if k%168==0:
            if not good:raise ValueError('NC_WEEKLY_ZERO_VOLUME_'+str(t))
            ret336=p[t]-p[t-336];ret168=p[t]-p[t-168]
            ret72=p[t]-p[t-72];ret24=p[t]-p[t-24]
            state[1:]=0.
            # Path efficiency is high when directional motion exceeds oscillation.
            path=np.sum(np.abs(r[t-71:t+1,1:]),axis=0)
            eff=np.abs(ret72[1:])/np.maximum(path,1e-10)
            eligible=np.flatnonzero((ret168[1:]>0)&(ret72[1:]>0)&(eff>.16))
            if len(eligible):
                j=int(1+eligible[np.argmax(eff[eligible])])
                state[1,j]=.12
            # Momentum in BTC-beta residuals, two simultaneous USD-neutral legs.
            rb=r[t-335:t+1,0];xb=rb-rb.mean()
            vb=max(float(np.mean(xb*xb)),1e-12)
            xa=r[t-335:t+1,1:]
            beta=np.clip(np.mean((xa-xa.mean(axis=0))*xb[:,None],axis=0)/vb,0.,3.)
            residual=ret168[1:]-beta*ret168[0]
            top=1+int(np.argmax(residual));bottom=1+int(np.argmin(residual))
            if top!=bottom and float(np.max(residual)-np.min(residual))>.030:
                state[2,top]=.06;state[2,bottom]=-.06
            breadth=int(np.count_nonzero(ret72<0))
            if breadth>=2 and ret72[0]<0:
                state[3,0]=-.12
            elif breadth>=2 and ret24[0]>0:
                state[3,0]=.12
            constructive=ret336[0]>0 and np.count_nonzero(ret168>0)>=2
            mult[:]=[1.,.85,.70] if constructive else [.75,1.,1.]
            ratio=float(np.std(r[t-71:t+1,0])/max(np.std(r[t-335:t+1,0]),1e-8))
            if ratio>1.5:mult[0]*=.5;mult[2]=1.
            active[t]=np.abs(state[1:]).sum(axis=1)>1e-12
        w=state.copy();w[1:]*=mult[:,None]
        room=.84-float(np.abs(w[0]).sum())
        if room<0:raise ValueError('NC_CORE_GROSS')
        optional=float(np.abs(w[1:]).sum())
        if optional>room and optional>0:w[1:]*=room/optional
        if np.abs(w).sum()>.84+1e-10:raise ValueError('NC_GROSS')
        updates[t]=np.any(np.abs(w-prev)>1e-12,axis=1)
        if k%672==0:updates[t,0]=True
        target[t]=w;prev=w
    return target,updates,active,valid
def synthetic_causality():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00008*t*(1+j/4)+.10*np.sin(t/40+j))
    o=c*(1-.001*np.sin(t/11+j));h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=np.full_like(c,1e6);rate=np.tile(np.array([[.0001,.0002,.0003,.0004]]),(HOURS,1))
    event=np.zeros_like(c,dtype=bool);event[::8]=True
    a=bundle(o,h,l,c,q,rate,event)
    changed=[z.copy() for z in (o,h,l,c,q,rate)]
    for z in changed[:4]:z[14000:]*=1.7
    changed[4][14000:]*=3;changed[5][14000:]*=-1
    b=bundle(*changed,event)
    if any(not np.array_equal(x[:14000],y[:14000]) for x,y in zip(a,b)):
        raise ValueError('NC_FUTURE_LEAK')
    silent=(np.abs(np.diff(a[0],axis=0)).sum(axis=2)>1e-12)&~a[1][1:]
    if np.any(silent):raise ValueError('NC_SILENT_WEIGHT_CHANGE')
    if not np.all(a[1][WARMUP::672,0]):raise ValueError('NC_MISSING_FORCED_CORE_REFRESH')
    return True
if __name__=='__main__':
    assert synthetic_causality()
    print('NC_SYNTHETIC_CAUSALITY_AND_FORCED_CORE_REFRESH_PASS')
