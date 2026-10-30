#!/usr/bin/env python3
"""CA independent native-funding / intrabar cashflow replay on ORIGINAL physical targets.
Uses CA signal and physical governors only to produce orders. Independently
rederives signed native funding, fees, gap/close PnL and all 81 intrabar corners.
This does not independently audit alpha generation or exchange fill realism.
"""
from __future__ import annotations
import argparse,itertools,json,math
import numpy as np
from ca_90cell import prepare_risk,preregistered_decisions,START_EXECUTION
from ca_sources import source_bundle
from ca_ringfenced_governor import CARingfencedGovernor,INITIAL_SHARES
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from phase1246_ai_two_stage_margin import settle_hour
from v98_staged_exit_viability_governor_v2 import FEES

CORNERS=np.asarray(tuple(itertools.product(range(3),repeat=4)),dtype=int)

def independent_settlement(previous,old,p0,p,h,l,c,target,rate,event,ml,mh,fee,order):
    gap=float(np.dot(old,p-p0))
    turnover=float(np.sum(np.abs((target-old)*p)))
    cost_rate=sum(FEES[fee])
    payer=old if order=="carried_before_fill" else target
    obligation=payer*rate*event
    mark=np.where(obligation>=0,mh,ml)
    funding=-float(np.sum(obligation*mark))
    cash_open=float(previous+gap+funding-cost_rate*turnover)
    corners=np.stack((l,p,h))[CORNERS,np.arange(4)]
    equity=cash_open+(corners-p)@target
    maintenance=.18*np.sum(np.abs(target)[None,:]*corners,axis=1)
    if np.any(equity<maintenance-1e-8):
        raise ValueError("CA_INDEPENDENT_REALIZED_MARGIN")
    if np.any(equity<.35*previous-1e-8):
        raise ValueError("CA_INDEPENDENT_REALIZED_FLOOR")
    close_cash=cash_open+float(np.dot(target,c-p))
    if close_cash<=0:raise ValueError("CA_INDEPENDENT_INSOLVENT")
    return close_cash,funding,turnover,float(np.min(equity-maintenance))

def replay(frames,risks,decisions,fee,order):
    o,h,l,c,q,r,e,ml,mh=frames
    weights,changes=decisions
    cash=INITIAL_SHARES.copy()*10000.
    units=np.zeros((4,4));g=CARingfencedGovernor()
    funding_total=0.;turnover_total=0.;max_abs_delta=0.
    intrabar_checks=0;book_hour_settlements=0;native_event_exposures=0
    for t in range(HOURS):
        if t>=START_EXECUTION:
            down,up,bpund,exitq=risks[t]
            previous=units.copy()
            for i in range(4):
                book=g.governors[i]
                if not np.any(units[i]) and not book.needs_authorization and not np.any(book.authorized):
                    continue
                target=g.trade_one(i,float(cash[i]),units[i],c[t-1],o[t],
                                   down,up,bpund,q[t-1],exitq,fee,order)
                target=np.where(np.abs((target-units[i])*o[t])<1e-7,units[i],target)
                independent,funding,turnover,margin=independent_settlement(
                    float(cash[i]),units[i],c[t-1],o[t],h[t],l[t],c[t],
                    target,r[t],e[t],ml[t],mh[t],fee,order)
                official=settle_hour(float(cash[i]),units[i],c[t-1],o[t],
                    h[t],l[t],c[t],target,r[t],e[t],ml[t],mh[t],
                    fee_mode=fee,funding_order=order)
                max_abs_delta=max(max_abs_delta,abs(independent-official["cash"]),
                                  abs(funding-official["funding"]),
                                  abs(turnover-official["turnover"]))
                if not math.isclose(independent,official["cash"],rel_tol=1e-11,abs_tol=1e-7):
                    raise ValueError("CA_INDEPENDENT_CASH_MISMATCH_T"+str(t))
                if not math.isclose(funding,official["funding"],rel_tol=1e-11,abs_tol=1e-7):
                    raise ValueError("CA_INDEPENDENT_FUNDING_MISMATCH_T"+str(t))
                if not math.isclose(turnover,official["turnover"],rel_tol=1e-11,abs_tol=1e-7):
                    raise ValueError("CA_INDEPENDENT_TURNOVER_MISMATCH_T"+str(t))
                cash[i]=official["cash"];units[i]=target
                funding_total+=funding;turnover_total+=turnover
                intrabar_checks+=81;book_hour_settlements+=1
                native_event_exposures+=int(bool(np.any(e[t]*(
                    units[i] if order=="new_after_fill" else previous[i]))))
            g.assert_aggregate_physical(previous,units,o[t],q[t-1])
        for i in np.flatnonzero(changes[t]):
            g.signal(int(i),weights[t,i]*cash[i]/c[t])
    return {"fee":fee,"order":order,"passed":True,
            "final_nav":float(cash.sum()),"book_final_nav":cash.tolist(),
            "funding":float(funding_total),"turnover":float(turnover_total),
            "max_abs_independent_cashflow_delta":float(max_abs_delta),
            "independent_81_corner_checks":intrabar_checks,
            "book_hour_settlements":book_hour_settlements,
            "native_funding_exposed_book_events":native_event_exposures}

def run():
    frames,manifest=load_official()
    source=source_bundle(frames[3],frames[4],frames[5],frames[6])
    decisions=preregistered_decisions("CA_full",frames,source)
    risks=prepare_risk(frames)
    cases=[]
    for fee,order in itertools.product(FEES,("carried_before_fill","new_after_fill")):
        try:cases.append(replay(frames,risks,decisions,fee,order))
        except Exception as exc:
            cases.append({"fee":fee,"order":order,"passed":False,
                          "reason":str(exc)[:450]})
    return {"architecture":"CA","historical_training_only":True,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "cases":cases,
            "native_funding_independently_rederived":all(c["passed"] for c in cases),
            "decision":"PASS_CA_NATIVE_EVENT_REPLAY_ONLY" if all(c["passed"] for c in cases)
                else "BLOCK_CA_NATIVE_EVENT_REPLAY"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    a=p.parse_args();result=run()
    with open(a.output,"w") as f:
        json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)
    print("CA_NATIVE_EVENT_REPLAY",result["decision"])
    for c in result["cases"]:
        print(c["fee"],c["order"],c["passed"],
              c.get("independent_81_corner_checks"),c.get("reason"))
    raise SystemExit(0 if all(c["passed"] for c in result["cases"]) else 2)
