#!/usr/bin/env python3
"""AB actual-NAV stateful signed-unit growth allocator, source-only.
No rejected engine imports. Completed t inputs; fills no earlier than t+1.
"""
from __future__ import annotations
import itertools
import numpy as np
CORNERS=np.array(tuple(itertools.product(range(3),repeat=4)),dtype=np.int8)
ASSET_CAP,NET_CAP,GROSS_CAP,FLOOR=.45,.75,1.35,.25
ORDER_FRACTION,ENTRY_STRESS_FRACTION=.005,.0025
SLIPPAGE,SEVERE_FEE=.002,.002

def vec(a):
    x=np.asarray(a,float)
    if x.shape!=(4,) or not np.isfinite(x).all():raise ValueError('AB1165_VECTOR')
    return x

def gate(new_units,old_units,price,equity,down,up,funding,quote,min336):
    """Hard 81-corner survival on ACTUAL carried units and equity."""
    try:
        n=vec(new_units);old=vec(old_units);p=vec(price);d=vec(down)
        u=vec(up);f=vec(funding);q=vec(quote);qmin=vec(min336)
    except ValueError:return False
    if (not np.isfinite(equity) or equity<=0 or (p<=0).any() or (d<0).any()
        or (d>=1).any() or (u<0).any() or (f<0).any() or
        (q<0).any() or (qmin<0).any()):return False
    order=np.abs(n-old)*p*(1+SLIPPAGE)
    if np.any(order>ORDER_FRACTION*q+1e-8):return False
    # Only new/increased positions must meet the trailing 336h stress cap.
    increases=np.abs(n)>np.abs(old)+1e-12
    if np.any(increases & (np.abs(n)*p*(1+u)>ENTRY_STRESS_FRACTION*qmin+1e-8)):
        return False
    w=n*p/equity
    if (np.abs(w).max()>ASSET_CAP+1e-10 or np.abs(w).sum()>GROSS_CAP+1e-10
        or abs(w.sum())>NET_CAP+1e-10):return False
    fee=(SLIPPAGE+SEVERE_FEE)*order.sum()
    debit=np.abs(n*p*f).sum()
    stressed=p*np.stack((1-d,np.ones(4),1+u))[CORNERS,np.arange(4)]
    pnl=((stressed-p)*n).sum(axis=1)
    stressed_eq=equity+pnl-fee-debit
    exposed=stressed*n
    return bool(np.all(stressed_eq>=FLOOR*equity-1e-8) and
        np.all(np.abs(exposed)<=ASSET_CAP*stressed_eq[:,None]+1e-8) and
        np.all(np.abs(exposed).sum(axis=1)<=GROSS_CAP*stressed_eq+1e-8) and
        np.all(np.abs(exposed.sum(axis=1))<=NET_CAP*stressed_eq+1e-8))

def allocate(intent,cov,old_units,price,equity,down,up,funding,quote,min336):
    """16-step actual-NAV log-growth surrogate with no free forced exits."""
    mu=vec(intent);old=vec(old_units);p=vec(price);q=vec(quote)
    qmin=vec(min336);u=vec(up);s=np.asarray(cov,float)
    if (s.shape!=(4,4) or not np.isfinite(s).all() or
        np.linalg.eigvalsh(s).min()<-1e-9 or not np.isfinite(equity) or equity<=0):
        raise ValueError('AB1165_BAD_COV_OR_EQUITY')
    check=lambda units:gate(units,old,p,equity,down,up,funding,q,qmin)
    if check(old):base=old.copy()
    else:
        if not check(np.zeros(4)):
            raise ValueError('AB1165_UNEXECUTABLE_SURVIVAL_REDUCTION')
        lo,hi=0.,1.
        for _ in range(24):
            mid=(lo+hi)/2
            if check(old*mid):lo=mid
            else:hi=mid
        base=old*lo
        if not check(base):base=np.zeros(4)
    w=base*p/equity
    sigma=s+np.eye(4)*1e-8
    step=1/max(.1,8*np.linalg.eigvalsh(sigma)[-1])
    for _ in range(16):
        grad=mu-sigma@w-(SLIPPAGE+SEVERE_FEE)*np.sign(w-old*p/equity)-vec(funding)*np.sign(w)
        wanted=(w+step*grad)*equity/p
        delta=np.clip(wanted-old,-ORDER_FRACTION*q/(p*(1+SLIPPAGE)),
                      ORDER_FRACTION*q/(p*(1+SLIPPAGE)))
        wanted=old+delta
        if check(wanted):w=wanted*p/equity
        else:
            lo,hi=0.,1.;current=w*equity/p
            for _ in range(16):
                mid=(lo+hi)/2
                if check(current+mid*(wanted-current)):lo=mid
                else:hi=mid
            w=(current+lo*(wanted-current))*p/equity
    out=w*equity/p
    if not check(out):
        raise ValueError('AB1165_FINAL_SURVIVAL')
    return out
