#!/usr/bin/env python3
"""V98 LA: preregistered seven-slot close-range breakout, acceleration, residual reversion, rebound.
Source-only causal intents; no rejected alpha, benchmark, future validation, or PnL imports.
"""
from __future__ import annotations
import numpy as np

WARMUP = 744
BUDGET = np.array([.55, .17, .12, .08], dtype=float)
PATHS = ("LA_core_only", "LA_full", "LA_minus_opportunity", "LA_minus_RV", "LA_minus_stress")

def bundle(opening, high, low, close, rate, event, quote):
    o, h, l, c, r, e, q = [np.asarray(x, dtype=float) for x in
                           (opening, high, low, close, rate, event, quote)]
    if (c.ndim != 2 or c.shape[1] != 4 or len(c) <= WARMUP
        or any(x.shape != c.shape or not np.isfinite(x).all() for x in (o,h,l,c,r,e,q))
        or np.any(o <= 0) or np.any(c <= 0) or np.any(l <= 0)
        or np.any(l > np.minimum(o,c)) or np.any(h < np.maximum(o,c))
        or np.any(q < 0) or np.any((e != 0) & (e != 1))):
        raise ValueError("LA_INVALID_CANONICAL_SOURCE")
    n = len(c)
    lc = np.log(c)
    intents = np.zeros((n,4,4), dtype=float)
    updates = np.zeros((n,4), dtype=bool)
    entries = np.zeros((n,3), dtype=bool)
    valid = np.zeros(n, dtype=bool)
    regimes = np.full(n, "MIXED", dtype="<U12")
    current = np.zeros((4,4), dtype=float)
    expiry = np.full(4,-1,dtype=int)
    for t in range(WARMUP,n):
        weekly = (t-WARMUP)%168 == 0
        monthly = (t-WARMUP)%672 == 0
        good = bool(np.all(q[t-671:t+1] > 0))
        valid[t] = good
        r672 = lc[t]-lc[t-672]
        r336 = lc[t]-lc[t-336]
        r168 = lc[t]-lc[t-168]
        rprev168 = lc[t-168]-lc[t-336]
        r72 = lc[t]-lc[t-72]
        r24 = lc[t]-lc[t-24]
        m168 = float(np.median(r168))
        m24 = float(np.median(r24))
        regimes[t] = ("TREND" if m168 > 0 else
                      "RECOVERY" if m168 < 0 and m24 > 0 else
                      "DEFENSE" if m168 < 0 else "MIXED")
        expired = set()
        for k in (1,2,3):
            if expiry[k] >= 0 and t >= expiry[k]:
                current[k] = 0.
                updates[t,k] = True
                expiry[k] = -1
                expired.add(k)
        if monthly and good:
            current[0] = 0.
            prior_high = np.max(h[t-671:t+1], axis=0)
            eligible = np.flatnonzero((r672 > 0) & (r168 > 0) & (c[t] >= .97*prior_high))
            if len(eligible):
                vol = np.std(np.diff(lc[t-336:t+1],axis=0),axis=0,ddof=0)
                score = r672 / np.maximum(vol,1e-12)
                ranked = sorted(eligible, key=lambda j:(-float(score[j]),int(j)))
                for j in ranked[:2]:
                    current[0,j] = .275
            updates[t,0] = True
        if weekly and good and expiry[1] < 0 and 1 not in expired:
            accel = r168-rprev168
            eligible = (accel > 0) & (r168 > 0) & (r24 > 0)
            if np.any(eligible):
                j = int(np.argmax(np.where(eligible,accel,-np.inf)))
                current[1] = 0.
                current[1,j] = .17
                expiry[1] = t+168
                updates[t,1] = True
                entries[t,0] = True
        if weekly and good and expiry[2] < 0 and 2 not in expired and m168 > 0:
            residual = r72-np.median(r72)
            winner = int(np.argmax(residual))
            loser = int(np.argmin(residual))
            if winner != loser and residual[winner]-residual[loser] > .03:
                current[2] = 0.
                current[2,loser] = .06
                current[2,winner] = -.06
                expiry[2] = t+168
                updates[t,2] = True
                entries[t,1] = True
        if weekly and good and expiry[3] < 0 and 3 not in expired and m168 < 0 and m24 > 0:
            eligible = r24 > 0
            if np.any(eligible):
                j = int(np.argmax(np.where(eligible,r24,-np.inf)))
                current[3] = 0.
                current[3,j] = .08
                expiry[3] = t+168
                updates[t,3] = True
                entries[t,2] = True
        intents[t] = current
        if np.abs(current).sum() > .92+1e-10:
            raise ValueError("LA_HIDDEN_GROSS")
    return intents, updates, entries, valid, regimes

def static_check():
    n=2200
    t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.00025,.00030,.00035,.00045]])
                 + .06*np.sin(t[:,None]/83.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01
    l=np.minimum(o,c)*.99
    q=1e6*(1.2+.35*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.tile(np.array([-.00008,.00012,.00001,.00025]),(n,1))
    e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    cc,oo,hh,ll,qq,rr=[z.copy() for z in (c,o,h,l,q,r)]
    for z in (cc,oo,hh,ll):z[1700:]*=1.8
    qq[1700:]*=4.;rr[1700:]*=-1.
    b=bundle(oo,hh,ll,cc,rr,e,qq)
    for i in range(5):
        if not np.array_equal(a[i][:1700],b[i][:1700]):
            raise ValueError("LA_FUTURE_LEAK_"+str(i))
    changes=np.any(np.diff(a[0],axis=0)!=0,axis=2)
    if np.any(changes & ~a[1][1:]):
        raise ValueError("LA_SILENT_ROW_REBALANCE")
    bad=q.copy();bad[700,2]=0.
    g=bundle(o,h,l,c,r,e,bad)
    if g[3][744] or np.any(g[2][744]) or np.any(g[1][744]):
        raise ValueError("LA_QUOTE_QUARANTINE")
    assert np.abs(a[0]).sum(axis=(1,2)).max()<=.92+1e-10
    assert not a[1][:WARMUP].any()
    return True

if __name__=="__main__":
    assert static_check()
    print("LA_SOURCE_SYNTHETIC_CAUSAL_PASS")
