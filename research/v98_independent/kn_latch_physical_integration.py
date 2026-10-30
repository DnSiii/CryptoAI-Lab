#!/usr/bin/env python3
"""KN deterministic physical governor + event-latch integration, not historical PnL."""
from __future__ import annotations
import numpy as np
from kn_event_latch import latch_rows
from v98_persistent_inventory_governor import govern_units
from v98_staged_exit_viability_governor_v2 import PARTICIPATION

def run():
    p=np.full(4,100.)
    q=np.full(4,1e6)
    qexit=np.full(4,24e6)
    down=np.full(4,.40);up=np.full(4,.65)
    funding=np.full(4,.0005)
    cash=10000.
    rows=np.zeros((4,4))
    rows[0,0]=70. # $7000 request; physical 0.25% hourly participation permits only 25 units
    old=np.zeros(4)
    first=govern_units(cash,old,p,p,rows.sum(axis=0),down,up,funding,q,qexit)
    assert 0<first[0]<=PARTICIPATION*q[0]/p[0]+1e-9
    assert first[0]<rows.sum(axis=0)[0]
    rows,cut=latch_rows(rows,first)
    assert cut[0] and np.isclose(rows.sum(axis=0)[0],first[0])
    # An unfilled event request may NEVER be reissued every hour.
    old=first.copy()
    for _ in range(200):
        approved=govern_units(cash,old,p,p,rows.sum(axis=0),
                              down,up,funding,q,qexit)
        later,cut=latch_rows(rows,approved)
        assert np.allclose(approved,old,rtol=0,atol=1e-10)
        assert np.array_equal(later,rows) and not cut.any()
        rows=later;old=approved
    # A hard capacity collapse forces a physical exit; do not re-enter.
    forced=govern_units(cash,old,p,p,rows.sum(axis=0),
                        down,up,funding,q,np.zeros(4))
    assert np.allclose(forced,0.)
    rows,cut=latch_rows(rows,forced)
    assert cut[0] and not rows.any()
    # No quote participation -> emergency cannot pretend to liquidate.
    try:
        govern_units(cash,old,p,p,rows.sum(axis=0),down,up,funding,
                     np.zeros(4),np.zeros(4))
    except ValueError as exc:
        assert str(exc)=="V98_UNIT_EMERGENCY_EXIT_TOO_SLOW"
    else:raise AssertionError("KN_FICTITIOUS_ZERO_QUOTE_EXIT")
    # A new pre-scheduled event alone can request new inventory.
    rows[0,0]=50.
    after=govern_units(cash,np.zeros(4),p,p,rows.sum(axis=0),
                       down,up,funding,q,qexit)
    rows,cut=latch_rows(rows,after)
    assert cut[0] and 0<rows[0,0]<=25.+1e-9
    return True
if __name__=="__main__":
    assert run()
    print("KN_PHYSICAL_GOVERNOR_200_HOUR_LATCH_NO_REENTRY_FORCED_EXIT_AND_ZERO_QUOTE_PASS")
