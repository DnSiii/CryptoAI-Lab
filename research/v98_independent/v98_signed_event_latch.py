#!/usr/bin/env python3
"""V98 Independent prospective SIGNED event latch: no risk-cut or capacity-cut hourly refill.

Pure execution infrastructure for future composed engines, not a rescue of KP/KO/KN.
"""
from __future__ import annotations
import numpy as np

def latch_signed_rows(rows,approved,tol=1e-10):
    r=np.asarray(rows,dtype=float);a=np.asarray(approved,dtype=float)
    if (r.shape!=(4,4) or a.shape!=(4,) or
        not np.isfinite(r).all() or not np.isfinite(a).all()):
        raise ValueError("V98_SIGNED_LATCH_BAD_INPUT")
    out=r.copy();cut=np.zeros(4,dtype=bool)
    for j in range(4):
        positive=np.any(r[:,j]>tol)
        negative=np.any(r[:,j]<-tol)
        if positive and negative:
            raise ValueError("V98_SIGNED_LATCH_OPPOSING_ROWS")
        requested=float(r[:,j].sum())
        if abs(requested)<=tol:continue
        if requested*a[j]<0 or abs(a[j])<abs(requested)-tol:
            scale=max(0.,min(1.,abs(a[j])/abs(requested))) if requested*a[j]>0 else 0.
            out[:,j]*=scale
            cut[j]=True
    if np.any(np.abs(out)>np.abs(r)+tol):
        raise ValueError("V98_SIGNED_LATCH_REENTRY")
    return out,cut

def static_check():
    rows=np.array([[10.,0,0,0],[5.,0,0,0],[0.,-8.,8.,0],[0.,0,0,0.]])
    after,cut=latch_signed_rows(rows,np.array([6.,-4.,0.,0.]))
    assert np.allclose(after.sum(axis=0),[6.,-4.,0.,0.])
    assert np.array_equal(cut,[True,True,True,False])
    for _ in range(200):
        newer,mask=latch_signed_rows(after,after.sum(axis=0))
        assert np.array_equal(newer,after) and not mask.any()
        after=newer
    new,mask=latch_signed_rows(rows,np.array([6.,4.,0.,0.]))
    assert not new[:,1].any() and mask[1]
    rows2=np.zeros((4,4));rows2[0,0]=10.;rows2[1,0]=-1.
    try:latch_signed_rows(rows2,np.zeros(4))
    except ValueError as exc:assert "OPPOSING" in str(exc)
    else:raise AssertionError("SIGNED_LATCH_OPPOSING_ROWS_ACCEPTED")
    for bad in (np.array([np.nan,0,0,0]),np.array([np.inf,0,0,0])):
        try:latch_signed_rows(rows,bad)
        except ValueError:pass
        else:raise AssertionError("SIGNED_LATCH_BAD_INPUT_ACCEPTED")
    return True
if __name__=="__main__":
    assert static_check()
    print("V98_SIGNED_EVENT_LATCH_200H_NO_AUTO_REENTRY_PASS")
