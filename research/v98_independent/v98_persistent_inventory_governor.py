#!/usr/bin/env python3
"""V98 Independent: causal UNIT-target staged inventory governor.

Infrastructure for FUTURE independent architectures only. Does NOT re-run,
alter, rescue or promote permanently rejected AS/AT candidates.
Signals freeze target *units* at a completed close; subsequent hours may
physically fill that frozen unit order or emergency de-risk. A constant target
never becomes an implicit hourly portfolio rebalance. The actual-open ledger
is external and must independently enforce 81 intrabar corners.
"""
from __future__ import annotations
import numpy as np
from v98_staged_exit_viability_governor_v2 import (
    four, capacity_units, stress_audit, FEES, ORDERS,
    PARTICIPATION, FUNDING_RESERVE_HOURS,
)

def target_units_at_completed_close(weights, settled_nav, completed_close):
    """Called at signal-close t; units are frozen for future open t+1."""
    w,p=map(four,(weights,completed_close))
    if not np.isfinite(settled_nav) or settled_nav<=0 or np.any(p<=0):
        raise ValueError("V98_UNIT_TARGET_INPUT")
    return w*float(settled_nav)/p

def govern_units(cash, old, prev_close, opening, pending_units,
                 down, up, funding_bound, prior_quote, min_exit_window_quote,
                 fee_mode="base", funding_order="carried_before_fill"):
    old,p0,p,target,d,u,f,q,qexit=map(four,(
        old,prev_close,opening,pending_units,down,up,funding_bound,
        prior_quote,min_exit_window_quote))
    if (fee_mode not in FEES or funding_order not in ORDERS or
        not np.isfinite(cash) or cash<=0 or
        np.any(p0<=0) or np.any(p<=0) or
        np.any(d<0) or np.any(d>=1) or np.any(u<0) or
        np.any(f<0) or np.any(q<0) or np.any(qexit<0)):
        raise ValueError("V98_UNIT_GOVERN_INPUT")
    cash_open=float(cash+old@(p-p0))
    if cash_open<=0:
        raise ValueError("V98_UNIT_OPEN_INSOLVENT")
    friction=sum(FEES[fee_mode])
    cap=capacity_units(p,qexit)
    delta=PARTICIPATION*q/p
    desired=np.clip(np.clip(target,-cap,cap),old-delta,old+delta)
    def safe(n):
        turnover=float(np.sum(np.abs(n-old)*p))
        payer=old if funding_order=="carried_before_fill" else n
        payer_reserve=FUNDING_RESERVE_HOURS*float(np.sum(np.abs(payer*p)*f))
        new_reserve=FUNDING_RESERVE_HOURS*float(np.sum(np.abs(n*p)*f))
        # Reserve whichever payer could be worse, without double counting.
        after=cash_open-friction*turnover-max(0.,payer_reserve-new_reserve)
        return stress_audit(after,n,p,d,u,f,friction)[0]
    def emergency():
        forced=np.clip(np.zeros(4),old-delta,old+delta)
        if np.any(np.abs(forced)>cap+1e-8):
            raise ValueError("V98_UNIT_EMERGENCY_EXIT_TOO_SLOW")
        if not safe(forced):
            raise ValueError("V98_UNIT_EMERGENCY_COLLATERAL")
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
    qexit=np.full(4,24e8)
    d=np.full(4,.40)
    u=np.full(4,.65)
    f=np.full(4,.0005)
    cash=10000.
    n=target_units_at_completed_close(np.array([.5,.25,0.,0.]),cash,p)
    filled=govern_units(cash,np.zeros(4),p,p,n,d,u,f,q,qexit)
    assert np.isfinite(filled).all()
    assert np.all(np.abs(filled*p)<=PARTICIPATION*q+1e-8)
    # This is the essential anti-churn invariant: if target units equal
    # carried units, a changed NAV/opening does not create a new trade.
    changed_open=p*1.001
    held=govern_units(cash,filled,p,changed_open,filled,d,u,f,q,qexit)
    assert np.array_equal(held,filled),(held,filled)
    # No prior-hour volume -> no fictitious opening fill.
    zero=govern_units(cash,np.zeros(4),p,p,n,d,u,f,np.zeros(4),qexit)
    assert np.array_equal(zero,np.zeros(4))
    # An impossible forced liquidation must fail, not assume a fill.
    try:
        govern_units(cash,np.array([1000.,0.,0.,0.]),p,p,
                     np.zeros(4),d,u,f,np.zeros(4),np.zeros(4))
    except ValueError as exc:
        assert str(exc)=="V98_UNIT_EMERGENCY_EXIT_TOO_SLOW"
    else:
        raise AssertionError("UNIT_GOVERN_HIDDEN_EXIT")
    return True

if __name__=="__main__":
    assert static_check()
    print("V98_UNIT_TARGET_PHYSICAL_GOVERNOR_PASS")
