#!/usr/bin/env python3
"""V98 BA preregistered absolute trend plus ETH/BTC stationary-ratio reversion sources.
All decisions at completed close[t], next eligible execution at open[t+1].
"""
from __future__ import annotations
import numpy as np
WARMUP=2160
CORE_EPOCH=336

def source_bundle(close,quote,rate,event):
    c,q,r,e=(np.asarray(x,dtype=float) for x in (close,quote,rate,event))
    if (c.ndim!=2 or c.shape[1]!=4 or any(x.shape!=c.shape for x in (q,r,e))
        or any(not np.isfinite(x).all() for x in (c,q,r,e))
        or np.any(c<=0) or np.any(q<0) or not np.isin(e,(0.,1.)).all()):
        raise ValueError("BA_SOURCE_INPUT")
    n=len(c);lc=np.log(c)
    lr=np.diff(lc,axis=0,prepend=lc[:1])
    core=np.zeros_like(c);opp=np.zeros_like(c)
    rv=np.zeros_like(c);stress=np.zeros_like(c)
    states=np.full(n,"TRANSITION",dtype="<U12")
    cur_core=np.zeros(4);cur_rv=np.zeros(4)
    opp_asset=-1;opp_until=-1;opp_last=-1000000
    rv_until=-1;rv_last=-1000000
    stress_until=-1;stress_last=-1000000;stress_seen=-1000000
    for t in range(WARMUP,n):
        r24=lc[t]-lc[t-24]
        r72=lc[t]-lc[t-72]
        r168=lc[t]-lc[t-168]
        r336=lc[t]-lc[t-336]
        if (t-WARMUP)%CORE_EPOCH==0:
            r1008=lc[t]-lc[t-1008]
            down=np.sqrt(np.mean(np.minimum(lr[t-335:t+1],0.)**2,axis=0))
            eligible=(r336>0)&(r1008>0)
            inv=np.where(eligible,1./np.maximum(down,1e-5),0.)
            cur_core[:]=0.
            if inv.sum()>0:
                remaining=1.
                active=eligible.copy()
                for _ in range(4):
                    if not active.any() or remaining<=1e-12:break
                    alloc=remaining*inv[active]/inv[active].sum()
                    excess=alloc>.45
                    if not excess.any():
                        cur_core[active]=alloc
                        remaining=0.
                        break
                    indices=np.flatnonzero(active)
                    capped=indices[excess]
                    cur_core[capped]=.45
                    remaining-=.45*len(capped)
                    active[capped]=False
        core[t]=cur_core
        # One stationary ETH/BTC ratio event; fixed 96-hour hold, 168h cooldown.
        if t>=rv_until:
            cur_rv[:]=0.
            if t>=rv_last+168:
                ratio=lc[t-671:t+1,1]-lc[t-671:t+1,0]
                mu=float(ratio.mean())
                sd=float(ratio.std())
                if sd>1e-8:
                    z=float((ratio[-1]-mu)/sd)
                    reversal=float(r24[1]-r24[0])
                    confirmed=(z>1.8 and reversal<0) or (z< -1.8 and reversal>0)
                    eth=lr[t-671:t+1,1];btc=lr[t-671:t+1,0]
                    btcvar=float(np.var(btc))
                    beta=float(np.clip(np.cov(eth,btc,bias=True)[0,1]/
                                       max(btcvar,1e-12),.4,2.))
                    ev=e[t-335:t+1]
                    mf=np.sum(r[t-335:t+1]*ev,axis=0)/np.maximum(ev.sum(axis=0),1.)
                    carry=12.*abs(float(mf[1]-beta*mf[0]))
                    if confirmed and abs(z)*sd>.025+carry:
                        sign=1. if z<0 else -1.
                        cur_rv[1]=sign/(1.+beta)
                        cur_rv[0]=-sign*beta/(1.+beta)
                        rv_last=t;rv_until=t+96
        rv[t]=cur_rv
        if t>=opp_until:
            opp_asset=-1
            if t>=opp_last+336:
                prev_high=np.max(c[t-240:t],axis=0)
                median_q=np.median(q[t-168:t],axis=0)
                v72=np.std(lr[t-71:t+1],axis=0)
                v240=np.std(lr[t-311:t-71],axis=0)
                candidates=[j for j in range(4) if r72[j]>.04
                    and c[t,j]>prev_high[j]
                    and v72[j]<.8*max(float(v240[j]),1e-12)
                    and q[t,j]>1.25*max(float(median_q[j]),1e-8)]
                if candidates:
                    opp_asset=sorted(candidates,key=lambda j:
                        (-round(float(r72[j]),12),j))[0]
                    opp_last=t;opp_until=t+144
        if opp_asset>=0 and t<opp_until:opp[t,opp_asset]=1.
        if np.count_nonzero(r168<-.08)>=3:stress_seen=t
        if (t>=stress_until and t>=stress_last+336
            and t-stress_seen<=168 and np.count_nonzero(r24>0)>=3
            and float(np.median(r24))>.02):
            stress_last=t;stress_until=t+120
        if t<stress_until:
            stress[t,0]=.5;stress[t,1]=.5
        if np.count_nonzero(r336>0)>=3 and float(np.median(r168))>0:
            states[t]="EXPANSION"
        elif np.count_nonzero(r168<0)>=3 and float(np.median(r72))<-.04:
            states[t]="PANIC"
    return core,opp,rv,stress,{"state":states}

def causal_check():
    n=2750;t=np.arange(n,dtype=float)
    c=100.*np.exp(t[:,None]*np.array([[.0002,.0001,.0003,.0004]]))
    q=np.full_like(c,1e8);r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    a=source_bundle(c,q,r,e)
    changed=c.copy();changed[-40:]*=1.1
    b=source_bundle(changed,q,r,e)
    for x,y in zip(a[:4],b[:4]):
        assert np.array_equal(x[:-40],y[:-40])
        assert np.isfinite(x).all() and not np.any(x[:WARMUP])
    assert np.array_equal(a[4]["state"][:-40],b[4]["state"][:-40])
    assert np.all(np.sum(a[0],axis=1)<=1.+1e-10)
    assert np.all(np.abs(np.sum(a[2],axis=1))<=1.)
    return True
if __name__=="__main__":
    assert causal_check()
    print("BA_CAUSAL_SOURCE_PASS")
