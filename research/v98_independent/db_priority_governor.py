#!/usr/bin/env python3
"""DB physical core-first residual satellite authorization; only tightens generic governor."""
from __future__ import annotations
import numpy as np
from cg_buffered_governor import CGBufferedGovernor,buffered_safe
from ba_ratio_reversion_governor import ENTRY_FRACTION
from v98_staged_exit_viability_governor_v2 import four,capacity_units

class DBPriorityGovernor(CGBufferedGovernor):
    def __init__(self):
        super().__init__()
        self.core_requested=np.zeros(4)
        self.satellite_requested=np.zeros(4)
        self.core_authorized_last=np.zeros(4)
        self.residual_scale_last=0.
        self.core_displacement_count=0
    def signal_components(self,core_units,satellite_units):
        self.core_requested=four(core_units).copy()
        self.satellite_requested=four(satellite_units).copy()
        self.requested=self.core_requested+self.satellite_requested
        self.needs_authorization=True
        self.epochs+=1
    def _authorize(self,cash,old,prev_close,opening,down,up,f,qexit,
                   fee_mode,order):
        full_request=self.requested.copy()
        try:
            self.requested=self.core_requested.copy()
            core=super()._authorize(cash,old,prev_close,opening,down,up,f,qexit,
                                    fee_mode,order)
        finally:
            self.requested=full_request
        core=four(core)
        self.core_authorized_last=core.copy()
        def safe(n):
            return buffered_safe(cash,old,prev_close,opening,n,down,up,f,qexit,
                                 fee_mode,order)
        if not safe(core):
            raise ValueError("DB_CORE_PRIORITY_NOT_PHYSICALLY_SAFE")
        cap=ENTRY_FRACTION*capacity_units(opening,qexit)
        # Never cancel/offset the already authorized core or carried legacy units.
        sat=np.where(np.abs(core)>1e-10,0.,self.satellite_requested)
        desired=np.clip(core+sat,-cap,cap)
        delta=desired-core
        delta=np.where(np.abs(core)>1e-10,0.,delta)
        if safe(core+delta):
            alpha=1.
        else:
            lo,hi=0.,1.
            for _ in range(40):
                mid=(lo+hi)*.5
                if safe(core+mid*delta):lo=mid
                else:hi=mid
            alpha=lo
        target=core+alpha*delta
        mask=np.abs(core)>1e-10
        if not np.array_equal(target[mask],core[mask]):
            self.core_displacement_count+=1
            raise ValueError("DB_CORE_DISPLACEMENT")
        if not safe(target):
            raise ValueError("DB_RESIDUAL_NOT_PHYSICALLY_SAFE")
        self.residual_scale_last=float(alpha)
        return target

def static_check():
    p=np.full(4,100.)
    q=np.full(4,1e9)
    exitq=q*24
    d=np.full(4,.4);u=np.full(4,.65);f=np.full(4,.0005)
    for fee in ("base","severe"):
        for order in ("carried_before_fill","new_after_fill"):
            g=DBPriorityGovernor()
            g.signal_components(np.array([150.,0.,0.,0.]),
                                np.array([-150.,75.,-75.,0.]))
            n=g.trade(10000.,np.zeros(4),p,p,d,u,f,q,exitq,
                      fee_mode=fee,funding_order=order)
            assert g.core_displacement_count==0
            assert n[0]>=0
            assert np.array_equal(g.authorized[np.abs(g.core_authorized_last)>1e-10],
                                  g.core_authorized_last[np.abs(g.core_authorized_last)>1e-10])
            assert buffered_safe(10000.,np.zeros(4),p,p,n,d,u,f,exitq,fee,order)
    return True

if __name__=="__main__":
    assert static_check()
    print("DB_PROTECTED_CORE_RESIDUAL_PHYSICAL_STATIC_PASS")
