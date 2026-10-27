#!/usr/bin/env python3
"""HR preregistered COMPLETE seven-slot spot-participation signal construction.

Only training 2023/24 and completed t information; no economic PnL here.
The source arrays are preauthenticated by the HQ masked feature gate.
"""
from __future__ import annotations
import numpy as np

WARMUP = 744
CLOCK = 168
GROSS = {"TREND": .74, "TRANSITION": .72, "STRESS": .66}
PRIOR = {"TREND": np.array([.42, .32, .16, .10]),
         "TRANSITION": np.array([.48, .22, .18, .12]),
         "STRESS": np.array([.46, .12, .14, .28])}


def bundle(opening, high, low, close, rate, event, quote,
           spot_quote, spot_eligible):
    o,h,l,c,r,e,q,s,mask = [np.asarray(x) for x in
                            (opening,high,low,close,rate,event,quote,spot_quote,spot_eligible)]
    o,h,l,c,r,e,q,s = [np.asarray(x,dtype=float) for x in (o,h,l,c,r,e,q,s)]
    if (c.ndim != 2 or c.shape[1] != 4 or len(c) <= WARMUP or
            any(x.shape != c.shape for x in (o,h,l,r,e,q,s,mask)) or
            mask.dtype != np.bool_ or
            any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
            np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
            np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
            np.any(q<0) or np.any((e!=0)&(e!=1)) or
            np.any(~np.isfinite(s[mask])) or np.any(s[mask]<0)):
        raise ValueError("HR_INVALID_NATIVE_OR_MASKED_SOURCE")
    n = len(c)
    lc = np.log(c)
    funding = np.vstack((np.zeros((1,4)),np.cumsum(r*e,axis=0)))
    bad = np.vstack((np.zeros((1,4),dtype=int),np.cumsum(~mask,axis=0)))
    signals = np.zeros((n,4,4),dtype=float)
    updates = np.zeros((n,4),dtype=bool)
    regimes = np.full(n,"TRANSITION",dtype="<U12")
    budgets = np.zeros((n,4),dtype=float)
    validity = np.zeros((n,4),dtype=bool)

    def net(t,w):
        return lc[t]-lc[t-w]-(funding[t+1]-funding[t-w+1])

    for t in range(WARMUP,n,CLOCK):
        n24,n72,n336 = (net(t,w) for w in (24,72,336))
        hourly168 = np.diff(lc[t-168:t+1],axis=0)
        semivol = np.maximum(np.sqrt(np.mean(np.minimum(hourly168,0.)**2,axis=0)),.002)
        leaders = np.argsort(-n336/semivol,kind="stable")[:3]
        signals[t,0,leaders] = [.50,.30,.20]
        liquidity = np.argsort(-q[t-335:t+1].sum(axis=0),kind="stable")[:3]
        burden = funding[t+1]-funding[t-335]
        signals[t,2,int(liquidity[np.argmin(burden[liquidity])])] = 1.

        valid = (bad[t+1]-bad[t-335] == 0)
        validity[t] = valid
        displacement = np.full(4,np.nan)
        for a in np.flatnonzero(valid):
            spot48 = s[t-47:t+1,a].sum()
            spot336 = s[t-335:t+1,a].sum()
            perp48 = q[t-47:t+1,a].sum()
            perp336 = q[t-335:t+1,a].sum()
            if min(spot48,spot336,perp48,perp336) <= 0:
                valid[a] = False
                validity[t,a] = False
                continue
            displacement[a] = (spot48/perp48)/(spot336/perp336)
        if np.any(valid):
            score = displacement * np.exp(np.clip(n72,-.2,.2))
            score[~valid] = -np.inf
            signals[t,1,int(np.argmax(score))] = 1.

        stress = float(np.median(n72)) < -.06
        if stress:
            recover = valid & (n24>0) & (displacement>1.)
            if np.any(recover):
                scores = np.where(recover,n24*displacement,-np.inf)
                signals[t,3,int(np.argmax(scores))] = 1.
        elif np.any(valid):
            scores = np.where(valid,n72*displacement,-np.inf)
            signals[t,3,int(np.argmax(scores))] = 1.
        trend = (np.count_nonzero(n336>0)>=3 and np.any(valid) and
                 float(np.median(displacement[valid]))>1.)
        regime = "STRESS" if stress else "TREND" if trend else "TRANSITION"
        regimes[t] = regime
        budgets[t] = PRIOR[regime]
        updates[t] = True
        for i in (0,2):
            if not np.isclose(signals[t,i].sum(),1.,atol=1e-12):
                raise ValueError("HR_CORE_OR_RV_UNFINANCED")
        if (not np.isfinite(signals[t]).all() or np.any(signals[t]<0) or
                np.any(budgets[t]<=0) or not np.isclose(budgets[t].sum(),1.) or
                np.any(signals[t].sum(axis=1)>1.+1e-12)):
            raise ValueError("HR_SEVEN_SLOT_BOOK_INVALID")
    return signals,updates,regimes,budgets,validity


def static_check():
    n=3800
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    s=q*(.4+.1*np.sin(t[:,None]/89.+np.arange(4)))
    r=np.full_like(c,.0001)
    e=np.zeros_like(c);e[::8]=1.
    mask=np.ones_like(c,dtype=bool)
    mask[1900:1902]=False
    s[1900:1902]=np.nan
    a=bundle(o,h,l,c,r,e,q,s,mask)
    c2,o2,h2,l2,q2,r2,s2=[x.copy() for x in (c,o,h,l,q,r,s)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.
    s2[3200:]*=2.
    r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2,s2,mask)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("HR_FUTURE_MUTATION_CAUSALITY_"+str(i))
    if not np.all(a[4][WARMUP]):
        raise ValueError("HR_INITIAL_SPOT_SOURCE")
    invalid_epoch=next(t for t in range(WARMUP,n,CLOCK) if 1900 <= t <= 2237)
    if np.any(a[4][invalid_epoch]) or np.any(a[0][invalid_epoch,1]):
        raise ValueError("HR_PARTIAL_GAP_SPOT_SIGNAL_LEAK")
    return True


if __name__ == "__main__":
    if not static_check():
        raise SystemExit(2)
    print("HR_SPOT_PARTICIPATION_CAUSAL_SOURCE_PASS")
