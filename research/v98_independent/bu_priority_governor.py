#!/usr/bin/env python3
"""BU V98-only core-first physical admission governor; no changes to shared governors."""
from __future__ import annotations
import numpy as np
from ba_ratio_reversion_governor import BAGovernor,ENTRY_FRACTION
from v98_staged_exit_viability_governor_v2 import (
    four,capacity_units,stress_audit,FEES,FUNDING_RESERVE_HOURS)

class BUPriorityGovernor(BAGovernor):
    def __init__(self):
        super().__init__()
        self.component_rows=np.zeros((4,4))
        self.satellite_admission_fraction=0.
        self.satellite_admissions=0
        self.satellite_denials=0
    def signal_components(self,rows):
        a=np.asarray(rows,dtype=float)
        if a.shape!=(4,4) or not np.isfinite(a).all():
            raise ValueError("BU_COMPONENT_INPUT")
        self.component_rows=a.copy()
        self.requested=a.sum(axis=0)
        self.needs_authorization=True
        self.epochs+=1
    def _authorize(self,cash,old,prev_close,opening,down,up,f,qexit,
                   fee_mode,order):
        old,p0,p,d,u,b,q=map(four,(old,prev_close,opening,down,up,f,qexit))
        saved=self.requested.copy()
        try:
            self.requested=self.component_rows[0].copy()
            core=super()._authorize(cash,old,p0,p,d,u,b,q,fee_mode,order)
        finally:
            self.requested=saved
        satellites=self.component_rows[1:].sum(axis=0)
        self.satellite_admission_fraction=0.
        if not np.any(satellites):
            return core
        cap=ENTRY_FRACTION*capacity_units(p,q)
        cash_open=float(cash+old@(p-p0))
        friction=float(sum(FEES[fee_mode]))
        def safe(n):
            if np.any(np.abs(n)>cap+1e-8):return False
            turnover=float(np.sum(np.abs((n-old)*p)))
            payer=old if order=="carried_before_fill" else n
            payer_reserve=FUNDING_RESERVE_HOURS*float(np.sum(np.abs(payer*p)*b))
            new_reserve=FUNDING_RESERVE_HOURS*float(np.sum(np.abs(n*p)*b))
            after=cash_open-friction*turnover-max(0.,payer_reserve-new_reserve)
            return stress_audit(after,n,p,d,u,b,friction)[0]
        if not safe(core):
            self.satellite_denials+=1
            return core
        if safe(core+satellites):
            fraction=1.
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

def static_check():
    p=np.full(4,100.);q=np.full(4,1e8)
    d=np.full(4,.3);u=np.full(4,.4);f=np.full(4,.0005)
    rows=np.zeros((4,4))
    rows[0,:2]=[10.,10.]
    only=BUPriorityGovernor();only.signal_components(rows)
    ncore=only._authorize(10000.,np.zeros(4),p,p,d,u,f,q,"base","carried_before_fill")
    rows[1,2]=10000.;rows[2,3]=-10000.
    g=BUPriorityGovernor();g.signal_components(rows)
    n=g._authorize(10000.,np.zeros(4),p,p,d,u,f,q,"base","carried_before_fill")
    assert np.allclose(n[:2],ncore[:2],rtol=0,atol=1e-8)
    assert 0.<=g.satellite_admission_fraction<=1.
    assert np.isfinite(n).all()
    return True
if __name__=="__main__":
    assert static_check()
    print("BU_CORE_PRIORITY_PHYSICAL_AUTHORIZATION_PASS")
