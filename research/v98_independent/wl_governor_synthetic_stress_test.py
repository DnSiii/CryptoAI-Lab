#!/usr/bin/env python3
"""WL governor *synthetic* stress checks; never economic evidence or WL rescue."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS
from wl_funding_buffer_physical import simulate
def fixture():
    p=np.full((HOURS,4),100.,dtype=float)
    d={"o":p.copy(),"h":p.copy(),"l":p.copy(),"c":p.copy(),
       "q":np.full((HOURS,4),1e6),
       "rate":np.zeros((HOURS,4)),
       "event":np.zeros((HOURS,4),dtype=bool),
       "mark_lower":p.copy(),"mark_upper":p.copy()}
    d["event"][::8]=True
    d["rate"][752:889:8,0]=.04  # extreme synthetic debit, never an observed rate
    return d
def run():
    d=fixture()
    long={743:np.array([.70,0.,0.,0.]),887:np.zeros(4)}
    checks=[]
    for order in ("carried_before_fill","new_after_fill"):
        r,_=simulate(d,long,"base",order,record=False)
        if not r["passed"] or r["governor_trims"]<1:
            raise ValueError("WL_SYNTHETIC_FUNDING_GOVERNOR_DID_NOT_TRIM_"+order)
        checks.append({"order":order,"passed":True,
                       "governor_trims":r["governor_trims"]})
    adverse=fixture()
    adverse["h"][760,0]=1000. # extreme short squeeze, must fail physical survival
    short={743:np.array([-.70,0.,0.,0.]),887:np.zeros(4)}
    bad,_=simulate(adverse,short,"base","carried_before_fill",record=False)
    if bad["passed"] or bad["reason"]!="INTRAHOUR_ADVERSE_MARGIN" or bad["hour"]!=760:
        raise ValueError("WL_SYNTHETIC_ADVERSE_MARGIN_NOT_DETECTED")
    # Without trims, fixed initial gross 7000 exceeds initial cash 9993
    # after 11 x 280 synthetic funding debits. This is a closed-form
    # counterfactual, NOT a market observation or strategy return.
    ungoverned=10000.-7.-11*(7000*.04)
    if ungoverned>=7000:raise ValueError("WL_SYNTHETIC_COUNTERFACTUAL_NOT_ADVERSE")
    result={"decision":"PASS_WL_SYNTHETIC_GOVERNOR_BRANCH_NOT_MARKET_VALIDATION",
            "funding_erosion_checks":checks,
            "adverse_short_margin_rejected_at_hour":bad["hour"],
            "ungoverned_counterfactual_cash_after_11_debits":ungoverned,
            "2026_accessed":False,"holdout_accessed":False,
            "real_pnl_computed":False,"WL_rejection_unchanged":True}
    print("WL_GOVERNOR_SYNTHETIC",json.dumps(result,sort_keys=True),flush=True)
    return result
if __name__=="__main__":run()
