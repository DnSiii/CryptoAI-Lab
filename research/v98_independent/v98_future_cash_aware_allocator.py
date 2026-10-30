#!/usr/bin/env python3
"""Future V98 Independent cash-aware event authorization; never rescues rejected KN.

Only *positive incremental units* may consume remaining settled NAV gross room.
Exits are not counted as freed collateral until physically settled. Source-close
only, no prices or liquidity from future bars. Long-only composed unit books.
"""
from __future__ import annotations
import numpy as np
ROWS=4
ASSETS=4
RESERVE_FRACTION=.05

def authorize_event(rows,component,desired,settled_nav,completed_close,physical_units):
    rows=np.asarray(rows,dtype=float)
    desired=np.asarray(desired,dtype=float)
    close=np.asarray(completed_close,dtype=float)
    physical=np.asarray(physical_units,dtype=float)
    if (rows.shape!=(ROWS,ASSETS) or desired.shape!=(ASSETS,) or
        close.shape!=(ASSETS,) or physical.shape!=(ASSETS,) or
        not all(np.isfinite(x).all() for x in (rows,desired,close,physical)) or
        not np.isfinite(settled_nav) or settled_nav<=0 or
        not isinstance(component,(int,np.integer)) or component not in range(ROWS) or
        np.any(rows<0) or np.any(desired<0) or np.any(physical<0) or
        np.any(close<=0)):
        raise ValueError("V98_CASH_AWARE_BAD_INPUT")
    oldrow=rows[component].copy()
    delta=desired-oldrow
    increase=np.maximum(delta,0.)
    decrease=np.minimum(delta,0.)
    occupied=np.maximum(physical,rows.sum(axis=0))
    occupied_gross=float(occupied@close)
    available=max(0.,(1.-RESERVE_FRACTION)*float(settled_nav)-occupied_gross)
    requested=float(increase@close)
    scale=min(1.,available/requested) if requested>0 else 1.
    updated=oldrow+decrease+scale*increase
    if np.any(updated< -1e-9) or np.any(updated-oldrow>increase+1e-9):
        raise ValueError("V98_CASH_AWARE_ROW_OVERFLOW")
    out=rows.copy();out[component]=np.maximum(updated,0.)
    # Gross after event must never exceed the pre-existing occupied gross
    # plus available new gross; existing physical inventory cannot disappear.
    after=np.maximum(physical,out.sum(axis=0))
    if float(after@close)>occupied_gross+available+1e-6:
        raise ValueError("V98_CASH_AWARE_UNFUNDED_ENTRY")
    return out,{"requested_new_gross":requested,"authorized_new_gross":scale*requested,
                "occupied_gross":occupied_gross,"available_gross":available,
                "entry_scale":scale,"clipped":bool(scale<1.-1e-10)}

def static_check():
    p=np.full(ASSETS,100.)
    r=np.zeros((ROWS,ASSETS))
    physical=np.zeros(ASSETS)
    r,m=authorize_event(r,0,np.array([60.,0,0,0]),10000.,p,physical)
    assert np.isclose(r[0,0],60.) and not m["clipped"]
    physical=r.sum(axis=0).copy()
    r,m=authorize_event(r,1,np.array([0.,30.,0,0]),10000.,p,physical)
    assert np.isclose(r[1,1],30.) and not m["clipped"]
    r,m=authorize_event(r,2,np.array([0.,0,20.,0]),10000.,p,physical)
    assert np.isclose(r[2,2],5.) and m["clipped"] and np.isclose(m["entry_scale"],.25)
    r,m=authorize_event(r,3,np.array([0.,0,0.,10.]),10000.,p,physical)
    assert np.isclose(r[3,3],0.) and m["clipped"]
    assert np.isclose(r.sum(axis=0)@p,9500.)
    # Expiring a row cannot fictitiously recycle gross before actual physical exit.
    physical=r.sum(axis=0).copy()
    r,m=authorize_event(r,1,np.zeros(ASSETS),10000.,p,physical)
    assert not r[1].any() and np.isclose(m["authorized_new_gross"],0.)
    r,m=authorize_event(r,3,np.array([0.,0,0.,10.]),10000.,p,physical)
    assert not r[3].any() and m["clipped"]
    # A same-asset row update consumes ONLY incremental units, not full row gross.
    physical=np.zeros(ASSETS);r=np.zeros((ROWS,ASSETS));r[0,0]=50.
    physical[0]=50.
    r,m=authorize_event(r,0,np.array([70.,0,0,0]),10000.,p,physical)
    assert np.isclose(m["requested_new_gross"],2000.) and np.isclose(r[0,0],70.)
    # If old physical inventory exceeds target room, only reductions are permitted.
    physical[0]=100.
    r,m=authorize_event(r,1,np.array([0.,10.,0,0]),10000.,p,physical)
    assert not r[1].any() and m["clipped"]
    r,m=authorize_event(r,0,np.zeros(ASSETS),10000.,p,physical)
    assert not r[0].any()
    for bad in (np.array([-1.,0,0,0]),np.array([float("nan"),0,0,0])):
        try:authorize_event(r,0,bad,10000.,p,physical)
        except ValueError:pass
        else:raise AssertionError("V98_CASH_AWARE_BAD_INPUT_ACCEPTED")
    return True
if __name__=="__main__":
    assert static_check()
    print("V98_CASH_AWARE_EVENT_AUTHORIZATION_NO_GHOST_COLLATERAL_PASS")
