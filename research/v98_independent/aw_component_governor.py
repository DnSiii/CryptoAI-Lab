#!/usr/bin/env python3
"""AW independent per-sleeve frozen unit epoch adapter; AV mechanics unchanged."""
from __future__ import annotations
import numpy as np
from av_epoch_risk_governor import EpochRiskGovernor
from v98_staged_exit_viability_governor_v2 import four

class AWComponentGovernor(EpochRiskGovernor):
    def signal_components(self,aggregate_units):
        self.requested=four(aggregate_units).copy()
        self.needs_authorization=True
        self.epochs+=1

def freeze_rows(rows,targets,mask,nav,completed_close):
    old=np.asarray(rows,dtype=float)
    target=np.asarray(targets,dtype=float)
    m=np.asarray(mask,dtype=bool)
    p=four(completed_close)
    if (old.shape!=(4,4) or target.shape!=(4,4) or m.shape!=(4,)
        or not np.isfinite(old).all() or not np.isfinite(target).all()
        or not np.isfinite(nav) or nav<=0 or np.any(p<=0)):
        raise ValueError("AW_COMPONENT_FREEZE_INPUT")
    out=old.copy()
    out[m]=target[m]*float(nav)/p
    return out

def static_check():
    p=np.full(4,100.)
    rows=np.zeros((4,4))
    target=np.zeros((4,4));target[0,0]=.5
    a=freeze_rows(rows,target,np.array([True,False,False,False]),10000.,p)
    target[1,1]=.1
    b=freeze_rows(a,target,np.array([False,True,False,False]),11000.,p*1.1)
    assert np.array_equal(a[0],b[0])
    assert b[1,1]>0 and np.array_equal(b[2:],a[2:])
    g=AWComponentGovernor();g.signal_components(b.sum(axis=0))
    assert g.needs_authorization and np.array_equal(g.requested,b.sum(axis=0))
    return True
if __name__=="__main__":
    assert static_check()
    print("AW_COMPONENT_UNIT_PERSISTENCE_PASS")
