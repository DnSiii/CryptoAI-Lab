#!/usr/bin/env python3
"""AA Phase1156: source-only entry-time exit-liquidity and 81-corner governor.

Independent implementation of Phase1155 preregistration. No historical PnL,
external benchmark, XRP, future data, or rejected-engine dependency.
"""
from __future__ import annotations
import itertools
import numpy as np

CORNERS=np.array(tuple(itertools.product(range(3),repeat=4)),dtype=np.int8)
ASSET_CAP,NET_CAP,GROSS_CAP,EQUITY_FLOOR=.45,.75,1.35,.25
ENTRY_PARTICIPATION,EXIT_RESERVE=.01,.006
SLIPPAGE,STRESS_FEE=.002,.002

def gate(candidate,carried,down,up,funding,entry_quote,minimum_72h_quote,capital):
    """Pretrade gate using completed bar t; all 81 corners and exit reserve."""
    w,old,d,u,f,q,qmin=(np.asarray(x,dtype=float) for x in
                        (candidate,carried,down,up,funding,entry_quote,minimum_72h_quote))
    if (any(x.shape!=(4,) or not np.isfinite(x).all() for x in (w,old,d,u,f,q,qmin))
        or not np.isfinite(capital) or capital<=0 or (d<0).any() or (d>=1).any()
        or (u<0).any() or (f<0).any() or (q<0).any() or (qmin<0).any()):return False
    entry=ENTRY_PARTICIPATION*q/(capital*(1+SLIPPAGE))
    exit_cap=EXIT_RESERVE*qmin/capital
    if ((np.abs(w-old)>entry+1e-10).any() or
        (np.abs(w)*(1+u)>exit_cap+1e-10).any() or
        (np.abs(w)>ASSET_CAP+1e-10).any() or
        np.abs(w).sum()>GROSS_CAP+1e-10 or abs(w.sum())>NET_CAP+1e-10):return False
    friction=(SLIPPAGE+STRESS_FEE)*np.abs(w-old).sum()+np.sum(np.abs(w)*f)
    prices=np.stack((1-d,np.ones(4),1+u))[CORNERS,np.arange(4)]
    exposure=prices*w
    equity=1+np.sum(exposure-w,axis=1)-friction
    return bool(np.all(equity>=EQUITY_FLOOR-1e-10) and
        np.all(np.abs(exposure)<=ASSET_CAP*equity[:,None]+1e-10) and
        np.all(np.abs(exposure).sum(axis=1)<=GROSS_CAP*equity+1e-10) and
        np.all(np.abs(exposure.sum(axis=1))<=NET_CAP*equity+1e-10))

def allocate(alpha,cov,carried,down,up,funding,entry_quote,minimum_72h_quote,capital):
    """Deterministic 16-step log-growth surrogate; charge reduce-only against
    ORIGINAL carried inventory, never invent an instantaneous free exit."""
    mu=np.asarray(alpha,float);sigma=np.asarray(cov,float)
    old=np.asarray(carried,float);u=np.asarray(up,float)
    q=np.asarray(entry_quote,float);qmin=np.asarray(minimum_72h_quote,float)
    f=np.asarray(funding,float)
    if (mu.shape!=(4,) or sigma.shape!=(4,4) or not np.isfinite(sigma).all()
        or not np.isfinite(mu).all() or old.shape!=(4,) or not np.isfinite(old).all()
        or q.shape!=(4,) or qmin.shape!=(4,) or not np.isfinite(q).all()
        or not np.isfinite(qmin).all() or not np.isfinite(capital) or capital<=0):
        raise ValueError('AA1156_ALLOCATOR_INPUT')
    if np.linalg.eigvalsh(sigma).min()<-1e-9:
        raise ValueError('AA1156_NON_PSD_COV')
    entry=ENTRY_PARTICIPATION*q/(capital*(1+SLIPPAGE))
    reserve=EXIT_RESERVE*qmin/capital
    check=lambda w:gate(w,old,down,up,funding,q,qmin,capital)
    if check(old):base=old.copy()
    else:
        if not check(np.zeros(4)):
            raise ValueError('AA1156_UNEXECUTABLE_PRIOR_EXIT')
        left,right=0.,1.
        for _ in range(24):
            mid=(left+right)/2
            if check(old*mid):left=mid
            else:right=mid
        base=old*left
        if not check(base):base=np.zeros(4)
    sigma=sigma+np.eye(4)*1e-8
    step=1/max(.1,8*np.linalg.eigvalsh(sigma)[-1])
    w=base.copy()
    for _ in range(16):
        grad=mu-sigma@w-(SLIPPAGE+STRESS_FEE)*np.sign(w-old)-f*np.sign(w)
        candidate=np.clip(w+step*grad,old-entry,old+entry)
        candidate=np.clip(candidate,-ASSET_CAP,ASSET_CAP)
        candidate=np.clip(candidate,-reserve/(1+u),reserve/(1+u))
        candidate*=min(1.,GROSS_CAP/max(np.abs(candidate).sum(),1e-12),
                       NET_CAP/max(abs(candidate.sum()),1e-12))
        if check(candidate):w=candidate
        else:
            left,right=0.,1.
            for _ in range(16):
                mid=(left+right)/2
                if check(w+mid*(candidate-w)):left=mid
                else:right=mid
            w=w+left*(candidate-w)
    # Signed truncation may worsen net risk near a tight boundary.
    # Test the 16 adjacent six-decimal lattice vertices; this is a
    # numerical representation fix, NOT a risk threshold relaxation.
    trunc=np.sign(w)*np.floor(np.abs(w)*1e6+1e-9)/1e6
    if check(trunc):return trunc
    low=np.floor(w*1e6)/1e6;high=np.ceil(w*1e6)/1e6
    feasible=[]
    for bits in itertools.product((0,1),repeat=4):
        trial=np.where(bits,high,low)
        if check(trial):feasible.append(trial)
    if feasible:
        return min(feasible,key=lambda x:(float(np.sum((x-w)**2)),tuple(x)))
    # Preserve original feasible inventory; otherwise quantized reduce-only
    # is charged against ORIGINAL carried units, never a fictitious free exit.
    if check(old):return old.copy()
    left,right=0.,1.;fallback=np.zeros(4)
    for _ in range(24):
        mid=(left+right)/2
        trial=np.sign(old)*np.floor(np.abs(old*mid)*1e6)/1e6
        if check(trial):left=mid;fallback=trial
        else:right=mid
    if not check(fallback):
        raise ValueError('AA1156_UNEXECUTABLE_QUANTIZATION')
    return fallback
