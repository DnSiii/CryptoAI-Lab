#!/usr/bin/env python3
"""V98 Independent: PRE-ECONOMIC staged 24h liquidation-capacity viability governor V2.

NOT a qualified engine, not authorized for live trading. This is a new
structural execution hypothesis for a future independently preregistered
seven-slot portfolio, NOT a rescue of rejected AR or earlier candidates.

The prior one-hour exit inventory cap throttles USD1m/10m capacity. A staged
24h exit can be considered only with conservative 50% quote-volume haircut,
24h 1%-per-hour adverse continuation, native funding reserve, physical
per-hour entry fills, actual-open execution and 81-corner settlement.
"""
from __future__ import annotations
import numpy as np

HOURS=24
PARTICIPATION=.0025
STRESSED_QUOTE_FRACTION=.50
EXIT_FRICTION_MULTIPLIER=2.2
CONTINUATION_PER_HOUR=.01
FUNDING_RESERVE_HOURS=24
FLOOR=.40
MAINTENANCE=.18
FEES={"base":(.0005,.0005),"severe":(.002,.003),
      "supersevere":(.005,.010)}
ORDERS=("carried_before_fill","new_after_fill")

def four(x):
    a=np.asarray(x,dtype=float)
    if a.shape!=(4,) or not np.isfinite(a).all():
        raise ValueError("V98_STAGED_VECTOR")
    return a

def capacity_units(opening,min_exit_window_quote):
    p,q=map(four,(opening,min_exit_window_quote))
    if np.any(p<=0) or np.any(q<0):
        raise ValueError("V98_STAGED_CAPACITY_INPUT")
    # q is the minimum observed *24h aggregate* quote volume among all
    # rolling 24h windows in the previous 336h. Genuine zero-volume hours
    # remain zero within their windows; no invented future exit liquidity.
    return (PARTICIPATION*STRESSED_QUOTE_FRACTION*q/
            (EXIT_FRICTION_MULTIPLIER*p))

def prior_min_exit_window_quote(quote,t):
    q=np.asarray(quote,dtype=float)
    if (q.ndim!=2 or q.shape[1]!=4 or t<336 or t>len(q) or
        not np.isfinite(q[t-336:t]).all() or np.any(q[t-336:t]<0)):
        raise ValueError('V98_STAGED_WINDOW_INPUT')
    windows=np.lib.stride_tricks.sliding_window_view(q[t-336:t],HOURS,axis=0)
    return np.min(np.sum(windows,axis=2),axis=0)

def stress_audit(cash_open,units,opening,down,up,funding_bound,friction):
    n,p,d,u,f=map(four,(units,opening,down,up,funding_bound))
    if (not np.isfinite(cash_open) or cash_open<=0 or
        np.any(p<=0) or np.any(d<0) or np.any(d>=1) or
        np.any(u<0) or np.any(f<0) or friction<0):
        return False,"BAD_INPUT"
    # First-stage full historically observed one-hour adverse gap.
    shocked=np.where(n>=0,p*(1-d),p*(1+u))
    first_cash=float(cash_open+n@(shocked-p))
    # Second-stage 24-hour uninterrupted adverse drift, not a favorable
    # assumption of instantaneous exit or future quote recovery.
    continuation=np.where(n>=0,(1-CONTINUATION_PER_HOUR)**HOURS,
                          (1+CONTINUATION_PER_HOUR)**HOURS)
    terminal=shocked*continuation
    terminal_cash=float(first_cash+n@(terminal-shocked))
    funding_reserve=FUNDING_RESERVE_HOURS*float(np.sum(np.abs(n*p)*f))
    exit_cost=EXIT_FRICTION_MULTIPLIER*friction*float(
        np.sum(np.abs(n*terminal)))
    remaining=terminal_cash-funding_reserve-exit_cost
    gross=float(np.sum(np.abs(n*terminal)))
    return (bool(remaining>=max(FLOOR*cash_open,MAINTENANCE*gross)-1e-8),
            "PASS" if remaining>=max(FLOOR*cash_open,MAINTENANCE*gross)-1e-8
            else "STAGED_EXIT_COLLATERAL")

def govern_staged(cash,old,prev_close,opening,weights,
                  down,up,funding_bound,prior_quote,min_exit_window_quote,
                  fee_mode="base",funding_order="carried_before_fill"):
    old,p0,p,w,d,u,f,q,qexit=map(four,(old,prev_close,opening,weights,
                                   down,up,funding_bound,prior_quote,min_exit_window_quote))
    if (fee_mode not in FEES or funding_order not in ORDERS or
        not np.isfinite(cash) or cash<=0 or
        np.any(p0<=0) or np.any(p<=0) or
        np.any(d<0) or np.any(d>=1) or
        np.any(u<0) or np.any(f<0) or
        np.any(q<0) or np.any(qexit<0)):
        raise ValueError("V98_STAGED_INPUT")
    cash_open=float(cash+old@(p-p0))
    if cash_open<=0:
        raise ValueError("V98_STAGED_GAP_INSOLVENCY")
    fee,slip=FEES[fee_mode]
    friction=fee+slip
    cap=capacity_units(p,qexit)
    # Persistent target is reissued each hour and physically sliced by the
    # prior completed hour's observed quote volume, including zero volume.
    desired=np.clip(w*cash_open/p,-cap,cap)
    max_delta=PARTICIPATION*q/p
    desired=np.clip(desired,old-max_delta,old+max_delta)
    def safe(n):
        turnover=float(np.sum(np.abs(n-old)*p))
        payer=old if funding_order=="carried_before_fill" else n
        # stress_audit already reserves 24h funding on the *new* inventory.
        # Reserve only the excess if the payer is carried-before-fill.
        payer_reserve=FUNDING_RESERVE_HOURS*float(
            np.sum(np.abs(payer*p)*f))
        new_reserve=FUNDING_RESERVE_HOURS*float(
            np.sum(np.abs(n*p)*f))
        extra=max(0.,payer_reserve-new_reserve)
        after=cash_open-friction*turnover-extra
        return stress_audit(after,n,p,d,u,f,friction)[0]
    def emergency():
        # No instantaneous liquidation: use no more than the actual
        # prior-hour participation envelope and test full stress again.
        forced=np.clip(np.zeros(4),old-max_delta,old+max_delta)
        if np.any(np.abs(forced)>cap+1e-8):
            raise ValueError("V98_STAGED_V2_EMERGENCY_EXIT_TOO_SLOW")
        if not safe(forced):
            raise ValueError("V98_STAGED_V2_EMERGENCY_UNSAFE")
        return forced
    if np.any(np.abs(old)>cap+1e-8):
        return emergency()
    if safe(desired):
        return desired
    if not safe(old):
        return emergency()
    lo,hi=0.,1.
    for _ in range(36):
        mid=(lo+hi)/2.
        if safe(old+mid*(desired-old)):
            lo=mid
        else:
            hi=mid
    return old+lo*(desired-old)

def static_check():
    p=np.full(4,100.)
    q=np.full(4,1e8)
    exit_window=q*HOURS
    cap=capacity_units(p,exit_window)
    assert np.all(cap>0)
    assert np.allclose(cap*EXIT_FRICTION_MULTIPLIER*p,
                       PARTICIPATION*STRESSED_QUOTE_FRACTION*exit_window)
    history=np.full((336,4),1e8)
    history[120]=0.
    assert np.allclose(prior_min_exit_window_quote(history,336),23e8)
    history[120:144]=0.
    assert np.array_equal(prior_min_exit_window_quote(history,336),np.zeros(4))
    n=govern_staged(10000.,np.zeros(4),p,p,
                    np.array([.25,.25,.25,.25]),
                    np.full(4,.4),np.full(4,.65),
                    np.full(4,.0005),q,exit_window)
    assert np.isfinite(n).all()
    assert np.all(np.abs(n)<=cap+1e-8)
    assert np.all(np.abs(n*p)<=PARTICIPATION*q+1e-8)
    # Scaling capital does not increase the absolute capacity allowed by
    # physical liquidity, even when the requested portfolio weight is huge.
    large=govern_staged(1e7,np.zeros(4),p,p,np.ones(4)*100,
                       np.full(4,.4),np.full(4,.65),
                       np.full(4,.0005),q,q)
    assert np.all(np.abs(large)<=cap+1e-8)
    return True

if __name__=="__main__":
    assert static_check()
    print("V98_STAGED_CAPACITY_PRE_ECONOMIC_STATIC_PASS")
