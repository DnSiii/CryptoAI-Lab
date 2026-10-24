#!/usr/bin/env python3
"""BX four non-cross-collateralized V98-only physical governors.
Independent ledger for each book; no interbook netting, cash transfers or hidden leverage.
"""
from __future__ import annotations
import numpy as np
from ba_ratio_reversion_governor import BAGovernor
from v98_staged_exit_viability_governor_v2 import four,PARTICIPATION

BOOKS=4
CAPACITY_SHARE=1./BOOKS
INITIAL_SHARES=np.array([.65,.15,.10,.10])

class BXRingfencedGovernor:
    def __init__(self):
        self.governors=[BAGovernor() for _ in range(BOOKS)]
    def signal(self,i,requested_units):
        if i not in range(BOOKS):raise ValueError("BX_BOOK_INDEX")
        self.governors[i].signal_components(four(requested_units))
    def trade_one(self,i,cash,old,prev_close,opening,down,up,funding_bound,
                  prior_quote,min_exit_quote,fee_mode,order):
        if i not in range(BOOKS):raise ValueError("BX_BOOK_INDEX")
        return self.governors[i].trade(
            cash,old,prev_close,opening,down,up,funding_bound,
            four(prior_quote)*CAPACITY_SHARE,
            four(min_exit_quote)*CAPACITY_SHARE,
            fee_mode=fee_mode,funding_order=order)
    def assert_aggregate_physical(self,old,new,opening,prior_quote):
        old=np.asarray(old,dtype=float);new=np.asarray(new,dtype=float)
        if old.shape!=(BOOKS,4) or new.shape!=(BOOKS,4):
            raise ValueError("BX_AGGREGATE_SHAPE")
        # Each book is charged gross; opposite orders are NOT magically crossed.
        gross_by_asset=np.sum(np.abs((new-old)*four(opening)),axis=0)
        if np.any(gross_by_asset>PARTICIPATION*four(prior_quote)+1e-6):
            raise ValueError("BX_AGGREGATE_PHYSICAL_OVERFILL")
        return gross_by_asset

def static_check():
    p=np.full(4,100.);q=np.full(4,1e7)
    down=np.full(4,.3);up=np.full(4,.4);f=np.full(4,.0001)
    g=BXRingfencedGovernor()
    old=np.zeros((4,4));new=np.zeros_like(old)
    for i in range(4):
        g.signal(i,np.full(4,10.))
        new[i]=g.trade_one(i,10000.*INITIAL_SHARES[i],old[i],p,p,
            down,up,f,q,q*24,"base","carried_before_fill")
    used=g.assert_aggregate_physical(old,new,p,q)
    assert np.all(used<=PARTICIPATION*q+1e-6)
    assert np.isclose(INITIAL_SHARES.sum(),1.)
    return True
if __name__=="__main__":
    assert static_check()
    print("BX_FOUR_BOOK_PHYSICAL_NONNETTING_PASS")
