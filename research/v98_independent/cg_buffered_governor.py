#!/usr/bin/env python3
"""CG conservative buffered physical authorization; physical infrastructure only, no rejected CF signals.
Adds 60% stressed post-fill NAV entry reserve; never relaxes original V98
40% hourly floor, 18% maintenance, staged liquidity or native funding reserve.
"""
from __future__ import annotations
import numpy as np
from ba_ratio_reversion_governor import BAGovernor,ENTRY_FRACTION
from v98_staged_exit_viability_governor_v2 import (
    four,capacity_units,stress_audit,FEES,
    FUNDING_RESERVE_HOURS,EXIT_FRICTION_MULTIPLIER,
    CONTINUATION_PER_HOUR,MAINTENANCE)
MIN_STRESS_NAV_RATIO=.60

def buffered_safe(cash,old,prev_close,opening,n,down,up,f,qexit,fee_mode,order):
    old,p0,p,n,d,u,f,qexit=map(four,(old,prev_close,opening,n,down,up,f,qexit))
    if fee_mode not in FEES or order not in ("carried_before_fill","new_after_fill"):
        return False
    cap=ENTRY_FRACTION*capacity_units(p,qexit)
    if np.any(abs(n)>cap+1e-8):
        return False
    cash_open=float(cash+old@(p-p0))
    friction=sum(FEES[fee_mode])
    turnover=float(np.sum(abs((n-old)*p)))
    payer=old if order=="carried_before_fill" else n
    payer_reserve=FUNDING_RESERVE_HOURS*float(np.sum(abs(payer*p)*f))
    new_reserve=FUNDING_RESERVE_HOURS*float(np.sum(abs(n*p)*f))
    after=cash_open-friction*turnover-max(0.,payer_reserve-new_reserve)
    if after<=0 or not np.isfinite(after):
        return False
    if not stress_audit(after,n,p,d,u,f,friction)[0]:
        return False
    shocked=np.where(n>=0,p*(1.-d),p*(1.+u))
    terminal=shocked*np.where(n>=0,(1.-CONTINUATION_PER_HOUR)**24,
                                     (1.+CONTINUATION_PER_HOUR)**24)
    remaining=(after+float(n@(terminal-p))
               -FUNDING_RESERVE_HOURS*float(np.sum(abs(n*p)*f))
               -EXIT_FRICTION_MULTIPLIER*friction*float(np.sum(abs(n*terminal))))
    gross=float(np.sum(abs(n*terminal)))
    return bool(remaining>=max(MIN_STRESS_NAV_RATIO*after,
                               MAINTENANCE*gross)-1e-8)

class CGBufferedGovernor(BAGovernor):
    def _authorize(self,cash,old,prev_close,opening,down,up,f,qexit,
                   fee_mode,order):
        candidate=super()._authorize(cash,old,prev_close,opening,down,up,f,qexit,
                                     fee_mode,order)
        def safe(v):
            return buffered_safe(cash,old,prev_close,opening,v,down,up,f,qexit,
                                 fee_mode,order)
        if safe(candidate):
            return candidate
        anchor=old.copy() if safe(old) else np.zeros(4)
        if not safe(anchor):
            raise ValueError("CG_BUFFER_NO_SAFE_ZERO_ANCHOR")
        lo,hi=0.,1.
        for _ in range(40):
            mid=(lo+hi)*.5
            if safe(anchor+mid*(candidate-anchor)):
                lo=mid
            else:
                hi=mid
        return anchor+lo*(candidate-anchor)

def static_check():
    p=np.full(4,100.)
    q=np.full(4,1e9);qexit=q*24
    d=np.full(4,.40);u=np.full(4,.65);f=np.full(4,.0005)
    old=np.zeros(4)
    a=BAGovernor();a.signal_components(np.array([150.,0.,0.,0.]))
    n_a=a.trade(10000.,old,p,p,d,u,f,q,qexit)
    b=CGBufferedGovernor();b.signal_components(np.array([150.,0.,0.,0.]))
    n_b=b.trade(10000.,old,p,p,d,u,f,q,qexit)
    assert buffered_safe(10000.,old,p,p,n_b,d,u,f,qexit,"base","carried_before_fill")
    assert abs(n_b[0])<=abs(n_a[0])+1e-8
    assert abs(n_b[0])<abs(n_a[0])-1e-3
    n_again=b.trade(10000.,n_b,p,p,d,u,f,q,qexit)
    assert np.array_equal(n_again,n_b)
    for fee in FEES:
        b=CGBufferedGovernor();b.signal_components(np.array([150.,0.,0.,0.]))
        n=b.trade(10000.,old,p,p,d,u,f,q,qexit,fee_mode=fee)
        assert buffered_safe(10000.,old,p,p,n,d,u,f,qexit,fee,"carried_before_fill")
    return True

if __name__=="__main__":
    assert static_check()
    print("CG_PRE_REGISTERED_BUFFERED_PHYSICAL_AUTHORIZATION_PASS")
