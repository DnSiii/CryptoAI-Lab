#!/usr/bin/env python3
"""V98 AZ preregistered 25% prior-window physical exit-capacity entry reserve.
No change to generic frozen V98 governors; AZ only.
"""
from __future__ import annotations
import numpy as np
from aw_component_governor import AWComponentGovernor
from v98_staged_exit_viability_governor_v2 import four,capacity_units

ENTRY_FRACTION=.25

class AZGovernor(AWComponentGovernor):
    def _authorize(self,cash,old,prev_close,opening,down,up,f,qexit,fee_mode,order):
        opening,qexit=map(four,(opening,qexit))
        cap=ENTRY_FRACTION*capacity_units(opening,qexit)
        self.requested=np.clip(self.requested,-cap,cap)
        return super()._authorize(cash,old,prev_close,opening,down,up,f,qexit,
                                  fee_mode,order)

def static_check():
    p=np.full(4,100.)
    qexit=np.full(4,1e5)
    old=np.zeros(4)
    g=AZGovernor()
    g.signal_components(np.array([10.,-10.,0.,0.]))
    n=g.trade(10000.,old,p,p,np.full(4,.3),np.full(4,.3),
              np.full(4,.0001),np.full(4,1e6),qexit)
    cap=ENTRY_FRACTION*capacity_units(p,qexit)
    assert np.all(np.abs(n)<=cap+1e-8)
    assert n[0]>=0 and n[1]<=0
    return True
if __name__=="__main__":
    assert static_check()
    print("AZ_PREAUTHORIZED_PHYSICAL_CAPACITY_PASS")
