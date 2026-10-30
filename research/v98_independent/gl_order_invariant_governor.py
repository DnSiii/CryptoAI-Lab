#!/usr/bin/env python3
"""GL-only order-invariant conservative CG authorization; NOT an alpha or PnL claim.
Funding order still applies in native settlement, never in risk target selection.
"""
from __future__ import annotations
import numpy as np
from cg_buffered_governor import CGBufferedGovernor,buffered_safe
from v98_staged_exit_viability_governor_v2 import FEES,ORDERS

class GLOrderInvariantBufferedGovernor(CGBufferedGovernor):
    def trade(self,cash,old,prev_close,opening,down,up,f,
              prior_quote,min_exit_window_quote,
              fee_mode="base",funding_order="carried_before_fill"):
        if fee_mode not in FEES or funding_order not in ORDERS:
            raise ValueError("GL_INVALID_SETTLEMENT_SCENARIO")
        # Always authorize under the more conservative old-payer reserve.
        # Actual native settlement still uses the caller's funding_order.
        return super().trade(
            cash,old,prev_close,opening,down,up,f,
            prior_quote,min_exit_window_quote,
            fee_mode=fee_mode,funding_order="carried_before_fill")

def static_check():
    from phase1246_ai_two_stage_margin import settle_hour,signed_funding
    p=np.full(4,100.)
    down=np.full(4,.40);up=np.full(4,.65)
    f=np.full(4,.0005)
    q=np.full(4,1e9);qexit=q*24
    requested=np.array([24.,18.,12.,6.])
    old=np.zeros(4)
    for fee in FEES:
        gl={}
        for order in ORDERS:
            g=GLOrderInvariantBufferedGovernor()
            g.signal_components(requested)
            n=g.trade(10000.,old,p,p,down,up,f,q,qexit,
                      fee_mode=fee,funding_order=order)
            gl[order]=(n.copy(),g.authorized.copy(),g.forced_ratchets)
            assert buffered_safe(10000.,old,p,p,n,down,up,f,qexit,
                                 fee,"carried_before_fill")
        assert np.array_equal(gl[ORDERS[0]][0],gl[ORDERS[1]][0])
        assert np.array_equal(gl[ORDERS[0]][1],gl[ORDERS[1]][1])
        assert gl[ORDERS[0]][2]==gl[ORDERS[1]][2]
        original=CGBufferedGovernor()
        original.signal_components(requested)
        conservative=original.trade(10000.,old,p,p,down,up,f,q,qexit,
                                    fee_mode=fee,funding_order="carried_before_fill")
        assert np.array_equal(gl[ORDERS[0]][0],conservative)

        # Repeat with an existing inventory to test order-independent ratchets.
        carried=gl[ORDERS[0]][0]
        for order in ORDERS:
            g=GLOrderInvariantBufferedGovernor()
            g.signal_components(requested)
            first=g.trade(10000.,old,p,p,down,up,f,q,qexit,
                          fee_mode=fee,funding_order=order)
            next_units=g.trade(10000.,first,p,p,down,up,f,q,qexit,
                               fee_mode=fee,funding_order=order)
            assert np.array_equal(next_units,first)

    # Settlement order remains REAL: if a trade coincides with a funding event,
    # cash must differ by the signed old-vs-new funding liability.
    units=np.array([.1,0.,0.,0.])
    target=np.array([.2,0.,0.,0.])
    rate=np.full(4,.0001)
    lo=np.full(4,99.);hi=np.full(4,101.)
    for e in (np.zeros(4),np.ones(4)):
        a=settle_hour(10000.,units,p,p,hi,lo,p,target,rate,e,lo,hi,
                      fee_mode="base",funding_order="carried_before_fill")
        b=settle_hour(10000.,units,p,p,hi,lo,p,target,rate,e,lo,hi,
                      fee_mode="base",funding_order="new_after_fill")
        expected=(signed_funding(target,rate,e,lo,hi)-
                  signed_funding(units,rate,e,lo,hi))
        assert abs((b["cash"]-a["cash"])-expected)<1e-8
        if not np.any(e):assert a["cash"]==b["cash"]
    return True

if __name__=="__main__":
    assert static_check()
    print("GL_CONSERVATIVE_ORDER_INVARIANT_AUTHORIZATION_PASS")
    print("GL_NATIVE_SETTLEMENT_ORDER_PRESERVED_PASS")
    print("GL_INFRASTRUCTURE_ONLY_NO_PNL_OR_HOLDOUT")
