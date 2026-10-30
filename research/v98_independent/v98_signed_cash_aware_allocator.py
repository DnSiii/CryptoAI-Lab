#!/usr/bin/env python3
"""V98 Independent prospective signed-unit allocator; never rescues rejected KO/KN.

Authorization is source-event-only; physical inventory and pending rows occupy
GROSS, not net, collateral. No intra-hour recycling of exits or leverage.
"""
from __future__ import annotations
import numpy as np
RESERVE=.05

def authorize_signed(rows,component,desired,nav,completed_close,physical_units):
    rows=np.asarray(rows,dtype=float)
    desired=np.asarray(desired,dtype=float)
    p=np.asarray(completed_close,dtype=float)
    physical=np.asarray(physical_units,dtype=float)
    if (rows.shape!=(4,4) or desired.shape!=(4,) or p.shape!=(4,) or
        physical.shape!=(4,) or not isinstance(component,(int,np.integer)) or
        component not in range(4) or not all(np.isfinite(x).all()
        for x in (rows,desired,p,physical)) or np.any(p<=0) or
        not np.isfinite(nav) or nav<=0):
        raise ValueError('V98_SIGNED_AUTH_BAD_INPUT')
    old=rows[component]
    for j in range(4):
        if desired[j]==0:continue
        if old[j]*desired[j]<0:
            raise ValueError('V98_SIGNED_AUTH_UNSETTLED_REVERSAL')
        others=np.delete(rows[:,j],component)
        if np.any(others*desired[j]<-1e-10) or physical[j]*desired[j]<-1e-10:
            return rows.copy(),{'blocked':'OPPOSING_CARRIED_INVENTORY',
                                'new_gross':0.,'entry_scale':0.}
    increment=np.maximum(np.abs(desired)-np.abs(old),0.)
    occupied=np.maximum(np.abs(physical),np.abs(rows).sum(axis=0))
    gross=float(occupied@p)
    room=max(0.,(1.-RESERVE)*float(nav)-gross)
    request=float(increment@p)
    scale=min(1.,room/request) if request>0 else 1.
    out=rows.copy()
    out[component]=np.sign(desired)*(np.minimum(np.abs(desired),np.abs(old))+scale*increment)
    after=np.maximum(np.abs(physical),np.abs(out).sum(axis=0))
    if float(after@p)>gross+room+1e-6:
        raise ValueError('V98_SIGNED_AUTH_GHOST_COLLATERAL')
    return out,{'blocked':None,'new_gross':request*scale,
                'entry_scale':scale,'occupied_gross':gross,'free_gross':room}

def static_check():
    p=np.full(4,100.);r=np.zeros((4,4));physical=np.zeros(4)
    r,_=authorize_signed(r,0,np.array([60.,0,0,0]),10000,p,physical)
    physical=r.sum(axis=0).copy()
    r,m=authorize_signed(r,2,np.array([0.,-20.,20.,0]),10000,p,physical)
    assert np.isclose(np.abs(r).sum(axis=0)@p,9500.)
    assert m['entry_scale']<1 and r[2,1]<0 and r[2,2]>0
    # Opposing physical BTC position blocks an entire RV pair, not just one leg.
    same=r.copy()
    r,m=authorize_signed(r,3,np.array([-10.,10.,0,0]),10000,p,physical)
    assert np.array_equal(r,same) and m['blocked']=='OPPOSING_CARRIED_INVENTORY'
    # Unfilled exit cannot recycle physical collateral at the same source close.
    physical=r.sum(axis=0).copy()
    r,_=authorize_signed(r,2,np.zeros(4),10000,p,physical)
    r,m=authorize_signed(r,3,np.array([0.,0.,0,10.]),10000,p,physical)
    assert not r[3].any() and m['new_gross']==0.
    # Negative short inventory uses gross rather than net collateral.
    short=np.zeros((4,4));short[0,0]=40.;short[1,1]=-30.
    short,m=authorize_signed(short,2,np.array([0.,0.,40.,0]),10000,p,np.array([40.,-30.,0,0]))
    assert np.isclose(short[2,2],25.) and np.isclose(np.abs(short).sum()*100,9500.)
    # A same-row signed reversal cannot jump through an unsettled exit.
    try:authorize_signed(short,1,np.array([0.,30.,0,0]),10000,p,np.zeros(4))
    except ValueError as exc:assert 'REVERSAL' in str(exc)
    else:raise AssertionError('V98_SIGNED_AUTH_REVERSAL_ACCEPTED')
    for bad in (np.array([np.nan,0,0,0]),np.array([np.inf,0,0,0])):
        try:authorize_signed(short,0,bad,10000,p,np.zeros(4))
        except ValueError:pass
        else:raise AssertionError('V98_SIGNED_AUTH_BAD_INPUT_ACCEPTED')
    return True
if __name__=='__main__':
    assert static_check()
    print('V98_SIGNED_CASH_AWARE_PHYSICAL_GROSS_AND_PENDING_EXIT_PASS')
