#!/usr/bin/env python3
"""V98 AV epoch-frozen risk authorization and monotone no-re-risk governor.
Future architecture infrastructure. Never re-run or rescue rejected AU/AT.
"""
from __future__ import annotations
import numpy as np
from v98_persistent_inventory_governor import (
    govern_units,target_units_at_completed_close)
from v98_staged_exit_viability_governor_v2 import (
    four,capacity_units,stress_audit,FEES,ORDERS,FUNDING_RESERVE_HOURS)

class EpochRiskGovernor:
    def __init__(self):
        self.requested=np.zeros(4)
        self.authorized=np.zeros(4)
        self.needs_authorization=False
        self.epochs=0
        self.forced_ratchets=0
    def signal(self,weights,settled_nav,completed_close):
        self.requested=target_units_at_completed_close(
            weights,settled_nav,completed_close)
        self.needs_authorization=True
        self.epochs+=1
    def _authorize(self,cash,old,prev_close,opening,down,up,f,qexit,
                   fee_mode,order):
        old,p0,p,d,u,f,qexit=map(four,(
            old,prev_close,opening,down,up,f,qexit))
        cash_open=float(cash+old@(p-p0))
        if not np.isfinite(cash_open) or cash_open<=0:
            raise ValueError("AV_EPOCH_GAP_INSOLVENCY")
        friction=sum(FEES[fee_mode])
        cap=capacity_units(p,qexit)
        candidate=np.clip(self.requested,-cap,cap)
        def safe(n):
            turnover=float(np.sum(np.abs((n-old)*p)))
            payer=old if order=="carried_before_fill" else n
            payer_reserve=FUNDING_RESERVE_HOURS*float(
                np.sum(np.abs(payer*p)*f))
            new_reserve=FUNDING_RESERVE_HOURS*float(
                np.sum(np.abs(n*p)*f))
            after=cash_open-friction*turnover-max(0.,payer_reserve-new_reserve)
            return stress_audit(after,n,p,d,u,f,friction)[0]
        if safe(candidate):
            return candidate
        if not safe(old):
            # Physical governor must attempt an actual-capacity emergency
            # reduction; never assume instant zeroing of carried units.
            return np.zeros(4)
        lo,hi=0.,1.
        for _ in range(36):
            mid=(lo+hi)*.5
            if safe(old+mid*(candidate-old)):lo=mid
            else:hi=mid
        return old+lo*(candidate-old)
    def trade(self,cash,old,prev_close,opening,down,up,f,
              prior_quote,min_exit_window_quote,
              fee_mode="base",funding_order="carried_before_fill"):
        if fee_mode not in FEES or funding_order not in ORDERS:
            raise ValueError("AV_EPOCH_MODE")
        old=four(old)
        if self.needs_authorization:
            self.authorized=self._authorize(
                cash,old,prev_close,opening,down,up,f,
                min_exit_window_quote,fee_mode,funding_order)
            self.needs_authorization=False
        n=govern_units(cash,old,prev_close,opening,self.authorized,
                      down,up,f,prior_quote,min_exit_window_quote,
                      fee_mode=fee_mode,funding_order=funding_order)
        # If the physical risk governor was forced to shrink carried units
        # despite a non-shrinking target, never re-risk before new signal.
        shrink=(old*self.authorized>0)&(
            np.abs(self.authorized)>=np.abs(old)-1e-8)&(
            np.abs(n)<np.abs(old)-1e-8)
        if np.any(shrink):
            self.authorized=np.where(shrink,n,self.authorized)
            self.forced_ratchets+=1
        return n

def static_check():
    p=np.full(4,100.)
    q=np.full(4,1e8);qexit=q*24
    d=np.full(4,.4);u=np.full(4,.65);f=np.full(4,.0005)
    g=EpochRiskGovernor()
    g.signal(np.array([.5,.25,0.,0.]),10000.,p)
    n=g.trade(10000.,np.zeros(4),p,p,d,u,f,q,qexit)
    assert np.isfinite(n).all()
    assert not g.needs_authorization and g.epochs==1
    n2=g.trade(10000.,n,p,p,d,u,f,q,qexit)
    assert np.array_equal(n,n2),(n,n2)
    # A genuine de-risk can never be re-authorized automatically.
    g.authorized=np.array([1.,0.,0.,0.])
    old=np.array([.8,0.,0.,0.])
    # Directly test the ratchet invariant on an adverse capacity opening.
    lowq=np.zeros(4)
    try:
        g.trade(10000.,old,p,p,d,u,f,lowq,lowq)
    except ValueError as exc:
        assert "EMERGENCY" in str(exc)
    else:
        assert abs(g.authorized[0])<=.8+1e-8
    return True

if __name__=="__main__":
    assert static_check()
    print("AV_EPOCH_AUTHORIZED_NO_RE_RISK_STATIC_PASS")
