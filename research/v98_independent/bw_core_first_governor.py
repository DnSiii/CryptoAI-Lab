#!/usr/bin/env python3
"""BW physical core-first hourly arbitration with actual prior-hour fill capacity."""
from __future__ import annotations
import numpy as np
from ba_ratio_reversion_governor import BAGovernor,ENTRY_FRACTION
from v98_persistent_inventory_governor import govern_units
from v98_staged_exit_viability_governor_v2 import (
    four,capacity_units,stress_audit,FEES,FUNDING_RESERVE_HOURS,ORDERS)

class BWCoreFirstGovernor(BAGovernor):
    def __init__(self):
        super().__init__()
        self.component_rows=np.zeros((4,4))
        self.satellite_admission_fraction=0.
        self.satellite_admissions=0;self.satellite_denials=0
        self.satellite_first_exits=0
    def signal_components(self,rows,core_epoch=False):
        a=np.asarray(rows,dtype=float)
        if a.shape!=(4,4) or not np.isfinite(a).all():
            raise ValueError("BW_COMPONENT_INPUT")
        if np.any(a[1:,:2]):
            raise ValueError("BW_SATELLITE_CORE_ASSET_OVERLAP")
        if self.epochs and not core_epoch:
            prev=self.authorized[:2]
            a=a.copy()
            a[0,:2]=np.sign(a[0,:2])*np.minimum(
                np.abs(a[0,:2]),np.where(
                    np.sign(prev)==np.sign(a[0,:2]),np.abs(prev),0.))
        self.component_rows=a.copy()
        self.requested=a.sum(axis=0)
        self.needs_authorization=True;self.epochs+=1
    def _authorize(self,cash,old,prev_close,opening,down,up,f,qexit,
                   fee_mode,order):
        old,p0,p,d,u,b,q=map(four,(old,prev_close,opening,down,up,f,qexit))
        saved=self.requested.copy()
        try:
            self.requested=self.component_rows[0].copy()
            core=super()._authorize(cash,old,p0,p,d,u,b,q,fee_mode,order)
        finally:self.requested=saved
        satellites=self.component_rows[1:].sum(axis=0)
        self.satellite_admission_fraction=0.
        if not np.any(satellites):return core
        cap=ENTRY_FRACTION*capacity_units(p,q)
        cash_open=float(cash+old@(p-p0))
        friction=float(sum(FEES[fee_mode]))
        def safe(n):
            if np.any(np.abs(n)>cap+1e-8):return False
            turnover=float(np.sum(np.abs((n-old)*p)))
            payer=old if order=="carried_before_fill" else n
            payer_reserve=FUNDING_RESERVE_HOURS*float(
                np.sum(np.abs(payer*p)*b))
            new_reserve=FUNDING_RESERVE_HOURS*float(
                np.sum(np.abs(n*p)*b))
            after=cash_open-friction*turnover-max(0.,payer_reserve-new_reserve)
            return stress_audit(after,n,p,d,u,b,friction)[0]
        if not safe(core):
            self.satellite_denials+=1
            return core
        if safe(core+satellites):fraction=1.
        else:
            lo,hi=0.,1.
            for _ in range(36):
                mid=(lo+hi)*.5
                if safe(core+mid*satellites):lo=mid
                else:hi=mid
            fraction=lo
        self.satellite_admission_fraction=float(fraction)
        if fraction>1e-8:self.satellite_admissions+=1
        else:self.satellite_denials+=1
        return core+fraction*satellites
    def trade(self,cash,old,prev_close,opening,down,up,f,
              prior_quote,min_exit_window_quote,
              fee_mode="base",funding_order="carried_before_fill"):
        if fee_mode not in FEES or funding_order not in ORDERS:
            raise ValueError("BW_MODE")
        old=four(old)
        if self.needs_authorization:
            self.authorized=self._authorize(
                cash,old,prev_close,opening,down,up,f,
                min_exit_window_quote,fee_mode,funding_order)
            self.needs_authorization=False
        args=(cash,old,prev_close,opening,self.authorized,down,up,f,
              prior_quote,min_exit_window_quote)
        n=govern_units(*args,fee_mode=fee_mode,funding_order=funding_order)
        # When risk would forcibly reduce core, test a PHYSICALLY FEASIBLE
        # alternate that unwinds satellites FIRST within prior-hour liquidity.
        involuntary=(old[:2]*self.authorized[:2]>0)&(
            np.abs(self.authorized[:2])>=np.abs(old[:2])-1e-8)&(
            np.abs(n[:2])<np.abs(old[:2])-1e-8)
        if np.any(involuntary) and np.any(np.abs(old[2:])>1e-8):
            alt_target=self.authorized.copy()
            alt_target[2:]=0.
            try:
                alt=govern_units(cash,old,prev_close,opening,alt_target,
                    down,up,f,prior_quote,min_exit_window_quote,
                    fee_mode=fee_mode,funding_order=funding_order)
            except ValueError:
                alt=None
            if (alt is not None and
                np.sum(np.abs(alt[:2]))>np.sum(np.abs(n[:2]))+1e-8):
                n=alt
                self.authorized[2:]=alt[2:]
                self.satellite_first_exits+=1
        shrink=(old*self.authorized>0)&(
            np.abs(self.authorized)>=np.abs(old)-1e-8)&(
            np.abs(n)<np.abs(old)-1e-8)
        if np.any(shrink):
            self.authorized=np.where(shrink,n,self.authorized)
            self.forced_ratchets+=1
        return n

def static_check():
    p=np.full(4,100.);q=np.full(4,1e8)
    d=np.full(4,.3);u=np.full(4,.4);f=np.full(4,.0005)
    rows=np.zeros((4,4));rows[0,:2]=[10.,10.]
    only=BWCoreFirstGovernor();only.signal_components(rows,core_epoch=True)
    core=only._authorize(10000.,np.zeros(4),p,p,d,u,f,q,
                         "base","carried_before_fill")
    rows[1,2]=10000.;rows[2,3]=-10000.
    g=BWCoreFirstGovernor();g.signal_components(rows,core_epoch=True)
    n=g._authorize(10000.,np.zeros(4),p,p,d,u,f,q,
                   "base","carried_before_fill")
    assert np.allclose(n[:2],core[:2],rtol=0,atol=1e-8)
    assert 0.<=g.satellite_admission_fraction<=1.
    g.authorized=np.array([.4,.2,0.,0.]);g.epochs=1
    g.signal_components(rows,core_epoch=False)
    assert np.all(g.component_rows[0,:2]<=[.4,.2])
    g.signal_components(rows,core_epoch=True)
    assert np.allclose(g.component_rows[0,:2],[10.,10.])
    fresh=BWCoreFirstGovernor();fresh.signal_components(rows,core_epoch=True)
    result=fresh.trade(10000.,np.zeros(4),p,p,d,u,f,q,q*24)
    assert np.isfinite(result).all()
    return True
if __name__=="__main__":
    assert static_check()
    print("BW_HOURLY_CORE_FIRST_PHYSICAL_PASS")
