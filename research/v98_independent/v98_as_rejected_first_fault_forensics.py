#!/usr/bin/env python3
"""V98 Independent: AS rejected-first-fault physical risk forensics ONLY.

No optimization, no valid PnL, no changes to frozen rejected AS strategy.
Reports whether a next-open max-liquidity emergency reduction could satisfy
the *same* staged collateral invariant; does not execute or rescue the trade.
"""
from __future__ import annotations
import argparse
import json
import numpy as np
import as_90cell_training as asrun
from as_staged_sources import source_bundle
from v98_staged_exit_viability_governor_v2 import govern_staged as govern_v2
from v98_staged_exit_capacity_governor import (
    capacity_units,stress_audit,FEES,PARTICIPATION,FUNDING_RESERVE_HOURS)

def run():
    frames,manifest=asrun.load_official()
    sources=source_bundle(frames[3],frames[1],frames[2],
                          frames[5],frames[6],frames[4])
    risks=asrun.prepare_risk(frames)
    original=asrun.govern_staged
    results=[]
    for mode in ("immediate","capacity_1m","capacity_10m"):
        captured=[]
        def inspect(cash,old,prev_close,opening,weights,down,up,bound,
                    prior_quote,exit_window_quote,fee_mode="base",
                    funding_order="carried_before_fill"):
            try:
                return original(cash,old,prev_close,opening,weights,
                                down,up,bound,prior_quote,exit_window_quote,
                                fee_mode=fee_mode,funding_order=funding_order)
            except ValueError as exc:
                old,p0,p,w,d,u,f,q,exitq=(np.asarray(x,dtype=float) for x in
                    (old,prev_close,opening,weights,down,up,bound,
                     prior_quote,exit_window_quote))
                cap=capacity_units(p,exitq)
                delta=PARTICIPATION*q/p
                forced=np.clip(np.zeros(4),old-delta,old+delta)
                cash_open=float(cash+old@(p-p0))
                fee,slip=FEES[fee_mode]
                friction=fee+slip
                payer=old if funding_order=="carried_before_fill" else forced
                reserve=FUNDING_RESERVE_HOURS*float(np.sum(np.abs(payer*p)*f))
                after_forced=(cash_open-friction*float(
                    np.sum(np.abs(forced-old)*p))-reserve)
                old_ok,old_reason=stress_audit(cash_open,old,p,d,u,f,friction)
                forced_ok,forced_reason=stress_audit(
                    after_forced,forced,p,d,u,f,friction)
                try:
                    v2_units=govern_v2(cash,old,p0,p,w,d,u,f,q,exitq,
                                       fee_mode=fee_mode,funding_order=funding_order)
                    v2_status='V2_FIRST_FAULT_PHYSICALLY_RECOVERABLE'
                except ValueError as v2exc:
                    v2_units=None
                    v2_status='V2_FIRST_FAULT_STILL_BLOCKED_'+str(v2exc)
                captured.append({
                    'v2_status':v2_status,
                    'v2_order_notional':(v2_units*p).tolist() if v2_units is not None else None,
                    'v2_per_hour_liquidity_compliant':bool(v2_units is not None and np.all(
                        np.abs((v2_units-old)*p)<=PARTICIPATION*q+1e-7)),
                    'v2_exit_capacity_compliant':bool(v2_units is not None and np.all(
                        np.abs(v2_units)<=cap+1e-8)),
                    "fault":str(exc),"mode":mode,
                    "cash_open":cash_open,
                    "old_notional":(old*p).tolist(),
                    "exit_capacity_notional":(cap*p).tolist(),
                    "per_hour_max_delta_notional":(delta*p).tolist(),
                    "forced_exit_notional":(forced*p).tolist(),
                    "capacity_breach_assets":int(np.count_nonzero(
                        np.abs(old)>cap+1e-8)),
                    "carried_stress_ok":bool(old_ok),
                    "carried_stress_reason":old_reason,
                    "max_liquid_emergency_stress_ok":bool(forced_ok),
                    "max_liquid_emergency_stress_reason":forced_reason,
                    "emergency_funding_and_fee_reserve_usd":float(
                        cash_open-after_forced),
                    "no_future_data":True,
                })
                raise
        asrun.govern_staged=inspect
        try:
            asrun.cell("AS_full",mode,"base","carried_before_fill",
                       frames,sources,risks)
            outcome="UNEXPECTED_SURVIVAL"
        except ValueError as exc:
            outcome=str(exc)
        finally:
            asrun.govern_staged=original
        results.append({"mode":mode,"outcome":outcome,
                        "first_fault":captured[0] if captured else None})
    return {"kind":"AS_REJECTED_FIRST_FAULT_FORENSIC_ONLY",
            "no_full_period_economic_result":True,
            "validation_2025_read":False,
            "results":results}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    args=p.parse_args()
    x=run()
    with open(args.output,"w") as f:
        json.dump(x,f,sort_keys=True,indent=2,allow_nan=False)
    print("V98_AS_FIRST_FAULT_FORENSIC",json.dumps(x,sort_keys=True))
