#!/usr/bin/env python3
"""KN event-latched physical authorization. No alpha or PnL; conservative no-reentry invariant.

For KN long-only component books, attribute the physically authorized aggregate
unit cap to every component pro-rata on that asset. An authorization shortfall
irreversibly reduces source-requested units until a new scheduled source event.
A pending exit may physically take multiple hours; it must never be converted
into a fresh entry. No NAV reset, source tuning or rejected KM rehabilitation.
"""
from __future__ import annotations
import numpy as np

def latch_rows(rows, approved, tol=1e-10):
    r=np.asarray(rows,dtype=float)
    a=np.asarray(approved,dtype=float)
    if r.shape!=(4,4) or a.shape!=(4,) or not np.isfinite(r).all() or not np.isfinite(a).all():
        raise ValueError("KN_LATCH_SHAPE_OR_NONFINITE")
    if np.any(r < -tol):
        raise ValueError("KN_LATCH_ONLY_LONG_COMPONENTS")
    if np.any(a < -tol):
        raise ValueError("KN_LATCH_AUTHORIZED_SIGN_FLIP")
    r=np.maximum(r,0.)
    a=np.maximum(a,0.)
    requested=r.sum(axis=0)
    new=r.copy()
    cut=np.zeros(4,dtype=bool)
    for j in range(4):
        if requested[j]<=tol:
            # A physically slow exit can leave old units temporarily above
            # a zero requested target. Do not invent a new component entry.
            continue
        if a[j] < requested[j]-tol:
            factor=max(0.,a[j]/requested[j])
            new[:,j]*=factor
            cut[j]=True
    if np.any(new>r+tol) or np.any(new < -tol):
        raise ValueError("KN_LATCH_REENTRY")
    return new,cut

def static_check():
    r=np.array([[5.,0,0,0],[2.,4.,0,0],[3.,0,0,0],[0.,0,0,0.]])
    new,cut=latch_rows(r,np.array([4.,1.,0.,0.]))
    assert np.allclose(new.sum(axis=0),[4.,1.,0.,0.])
    assert np.array_equal(cut,[True,True,False,False])
    assert np.allclose(new[:,0],r[:,0]*.4)
    # A previously forced cut cannot automatically re-enter next hour.
    for _ in range(200):
        later,mask=latch_rows(new,new.sum(axis=0))
        assert np.array_equal(later,new) and not mask.any()
        new=later
    # A scheduled event can add new units, but only by explicit caller update.
    new[1,1]=2.
    after,_=latch_rows(new,new.sum(axis=0))
    assert np.array_equal(after,new)
    # A physical partial exit does not recreate the exited component.
    zero=np.zeros((4,4))
    unchanged,mask=latch_rows(zero,np.array([1.,0,0,0]))
    assert np.array_equal(unchanged,zero) and not mask.any()
    for bad in (np.array([-1.,0,0,0]),np.array([np.nan,0,0,0])):
        try:latch_rows(r,bad)
        except ValueError:pass
        else:raise AssertionError("KN_LATCH_ACCEPTED_BAD_AUTHORIZATION")
    return True

if __name__=="__main__":
    assert static_check()
    print("KN_LATCH_200_HOUR_NO_REENTRY_AND_SLOW_EXIT_PASS")
