#!/usr/bin/env python3
"""Independent V98 hourly futures settlement oracle. No engine/governor/settle_hour imports.
For full-history use: call on EVERY physically settled hour with real input and
settle_hour receipt. Synthetic self-test alone is NOT a historical ledger validation.
"""
from __future__ import annotations
import itertools,math
import numpy as np
FEE_SCHEDULE={"base":(.0005,.0005),"severe":(.002,.003),"supersevere":(.005,.010)}
FUNDING_ORDERS=("carried_before_fill","new_after_fill")
CORNERS=np.array(list(itertools.product(range(3),repeat=4)),dtype=int)
def vector(x):
    a=np.asarray(x,dtype=float)
    if a.shape!=(4,) or not np.isfinite(a).all():
        raise ValueError("ORACLE_INVALID_VECTOR")
    return a
def close(a,b,name):
    if not math.isclose(float(a),float(b),rel_tol=1e-11,abs_tol=1e-7):
        raise ValueError("ORACLE_MISMATCH_"+name)
def verify_hour(previous_cash,carried,previous_close,opening,high,low,
                closing,new_units,funding_rate,funding_event,mark_low,
                mark_high,fee_mode,funding_order,receipt):
    if fee_mode not in FEE_SCHEDULE or funding_order not in FUNDING_ORDERS:
        raise ValueError("ORACLE_INVALID_MODE")
    old,p0,p,h,l,c,n,r,e,ml,mh=map(vector,(carried,previous_close,opening,
            high,low,closing,new_units,funding_rate,funding_event,mark_low,mark_high))
    if (previous_cash<=0 or np.any(p<=0) or np.any(p0<=0) or
        np.any(l<=0) or np.any(l>np.minimum(p,c)) or
        np.any(h<np.maximum(p,c)) or np.any(ml<=0) or np.any(mh<ml) or
        not np.isin(e,(0.,1.)).all()):
        raise ValueError("ORACLE_GEOMETRY")
    fee,slip=FEE_SCHEDULE[fee_mode]
    payer=old if funding_order=="carried_before_fill" else n
    obligation=payer*r*e
    marks=np.where(obligation>=0,mh,ml)
    funding=-float(np.dot(obligation,marks))
    gap=float(np.dot(old,p-p0))
    turnover=float(np.dot(np.abs(n-old),p))
    fees=fee*turnover
    slippage=slip*turnover
    pnl=float(np.dot(n,c-p))
    open_cash=float(previous_cash+gap+funding-fees-slippage)
    cash=float(open_cash+pnl)
    if open_cash<=0 or cash<=0:
        raise ValueError("ORACLE_INSOLVENCY")
    corners=np.stack((l,p,h))[CORNERS,np.arange(4)]
    stress_equity=open_cash+(corners-p)@n
    margin=.18*np.sum(np.abs(n)[None,:]*corners,axis=1)
    if np.any(stress_equity<margin-1e-8):
        raise ValueError("ORACLE_REALIZED_MARGIN")
    if np.any(stress_equity<.35*previous_cash-1e-8):
        raise ValueError("ORACLE_REALIZED_FLOOR")
    expected={"cash":cash,"equity":cash,"gap_pnl":gap,"intrabar_pnl":pnl,
              "funding":funding,"turnover":turnover,"fees":fees,"slippage":slippage}
    for k,v in expected.items():
        close(v,receipt[k],k.upper())
    if not np.allclose(vector(receipt["units"]),n,rtol=0,atol=1e-10):
        raise ValueError("ORACLE_UNIT_MISMATCH")
    if receipt.get("hidden_borrow") is not False or receipt.get("cash_settled") is not True:
        raise ValueError("ORACLE_HIDDEN_BORROW")
    return {"verified":True,"cash":cash,"gross":float(np.dot(np.abs(n),c)),
            "funding":funding,"turnover":turnover,
            "min_intrabar_margin_surplus":float(np.min(stress_equity-margin))}
def static_check():
    z=np.zeros(4)
    old=np.array([1.,0.,0.,0.])
    new=np.array([2.,0.,0.,0.])
    p0=np.full(4,100.);p=np.full(4,102.)
    h=np.full(4,105.);l=np.full(4,100.);c=np.full(4,103.)
    r=np.array([.001,0.,0.,0.]);e=np.ones(4)
    ml=np.full(4,100.);mh=np.full(4,104.)
    for order,fund,cash in (("carried_before_fill",-.104,10003.794),
                            ("new_after_fill",-.208,10003.690)):
        receipt={"cash":cash,"equity":cash,"gap_pnl":2.,
                 "intrabar_pnl":2.,"funding":fund,"turnover":102.,
                 "fees":.051,"slippage":.051,"units":new.copy(),
                 "hidden_borrow":False,"cash_settled":True}
        assert verify_hour(10000.,old,p0,p,h,l,c,new,r,e,ml,mh,
                           "base",order,receipt)["verified"]
        tampered=dict(receipt,cash=cash+1.)
        try:verify_hour(10000.,old,p0,p,h,l,c,new,r,e,ml,mh,"base",order,tampered)
        except ValueError as exc:assert "MISMATCH_CASH" in str(exc)
        else:raise AssertionError("ORACLE_TAMPER_NOT_CAUGHT")
    return True
if __name__=="__main__":
    assert static_check()
    print("V98_INDEPENDENT_SETTLEMENT_ORACLE_STATIC_PASS_NOT_FULL_HISTORY")
