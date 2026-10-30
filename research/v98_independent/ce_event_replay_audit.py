#!/usr/bin/env python3
"""CE independent native funding / actual-open / 81-corner cashflow replay.
CE source and physical governor generate ORIGINAL orders; cash settlement,
signed funding and 81 realized OHLC corners independently rederived here.
No future alpha, no external engines, no live or paper trading.
"""
from __future__ import annotations
import argparse,itertools,json,math
import numpy as np
from ce_sources import bundle,BUDGETS,WARMUP
from ce_90cell import prepare_risks,START_EXECUTION
from ba_ratio_reversion_governor import BAGovernor
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from phase1246_ai_two_stage_margin import settle_hour
from v98_staged_exit_viability_governor_v2 import FEES

CORNERS=np.asarray(tuple(itertools.product(range(3),repeat=4)),dtype=int)

def independently_settle(previous,old,p0,p,h,l,c,target,r,e,ml,mh,fee,order):
    old=np.asarray(old,dtype=float)
    target=np.asarray(target,dtype=float)
    turnover=float(np.sum(abs((target-old)*p)))
    gap=float(np.dot(old,p-p0))
    payer=old if order=="carried_before_fill" else target
    obligations=payer*r*e
    marks=np.where(obligations>=0,mh,ml)
    funding=-float(np.dot(obligations,marks))
    cost=sum(FEES[fee])*turnover
    cash_open=float(previous+gap+funding-cost)
    corners=np.stack((l,p,h))[CORNERS,np.arange(4)]
    cash_corners=cash_open+(corners-p)@target
    maintenance=.18*np.sum(abs(target)[None,:]*corners,axis=1)
    if np.any(cash_corners<maintenance-1e-8):
        raise ValueError("CE_REPLAY_REALIZED_MARGIN")
    if np.any(cash_corners<.35*previous-1e-8):
        raise ValueError("CE_REPLAY_REALIZED_FLOOR")
    final=float(cash_open+np.dot(target,c-p))
    if final<=0:raise ValueError("CE_REPLAY_INSOLVENT")
    return final,funding,turnover,float(np.min(cash_corners-maintenance))

def replay(frames,risks,sources,fee,order):
    o,h,l,c,q,r,e,ml,mh=frames
    signals,updates,regimes=sources
    cash=10000.
    old=np.zeros(4)
    rows=np.zeros((4,4))
    g=BAGovernor()
    max_cash_delta=0.;max_funding_delta=0.;max_turnover_delta=0.
    funding_total=turnover_total=0.
    actual_corner_checks=settlements=exposed_events=0
    for t in range(HOURS):
        if t>=START_EXECUTION and (np.any(old) or g.needs_authorization or np.any(g.authorized)):
            down,up,bound,exitq=risks[t]
            target=g.trade(cash,old,c[t-1],o[t],down,up,bound,q[t-1],exitq,
                           fee_mode=fee,funding_order=order)
            target=np.where(abs((target-old)*o[t])<1e-7,old,target)
            independent,funding,turnover,margin=independently_settle(
                cash,old,c[t-1],o[t],h[t],l[t],c[t],target,r[t],e[t],ml[t],mh[t],
                fee,order)
            official=settle_hour(cash,old,c[t-1],o[t],h[t],l[t],c[t],
                target,r[t],e[t],ml[t],mh[t],fee_mode=fee,funding_order=order)
            max_cash_delta=max(max_cash_delta,abs(independent-official["cash"]))
            max_funding_delta=max(max_funding_delta,abs(funding-official["funding"]))
            max_turnover_delta=max(max_turnover_delta,abs(turnover-official["turnover"]))
            if not math.isclose(independent,official["cash"],rel_tol=1e-11,abs_tol=1e-7):
                raise ValueError("CE_REPLAY_CASH_T"+str(t))
            if not math.isclose(funding,official["funding"],rel_tol=1e-11,abs_tol=1e-7):
                raise ValueError("CE_REPLAY_FUNDING_T"+str(t))
            if not math.isclose(turnover,official["turnover"],rel_tol=1e-11,abs_tol=1e-7):
                raise ValueError("CE_REPLAY_TURNOVER_T"+str(t))
            payer=old if order=="carried_before_fill" else target
            exposed_events+=int(np.count_nonzero(e[t]*abs(payer)))
            cash=official["cash"];old=target.copy()
            funding_total+=funding;turnover_total+=turnover
            actual_corner_checks+=len(CORNERS)
            settlements+=1
        if t>=WARMUP and updates[t].any():
            for i in np.flatnonzero(updates[t]):
                rows[i]=signals[t,i]*BUDGETS[str(regimes[t])][i]*cash/c[t]
            g.signal_components(rows.sum(axis=0))
    return {"fee":fee,"order":order,"passed":True,
            "final_nav":float(cash),"funding":float(funding_total),
            "turnover":float(turnover_total),
            "settled_hours":settlements,
            "actual_independent_81_corner_checks":actual_corner_checks,
            "native_funding_asset_exposure_events":exposed_events,
            "max_cash_delta":max_cash_delta,
            "max_funding_delta":max_funding_delta,
            "max_turnover_delta":max_turnover_delta}

def run():
    frames,manifest=load_official()
    source=bundle(frames[3],frames[5],frames[6])
    risks=prepare_risks(frames)
    cases=[]
    for fee,order in itertools.product(FEES,("carried_before_fill","new_after_fill")):
        try:cases.append(replay(frames,risks,source,fee,order))
        except Exception as exc:
            cases.append({"fee":fee,"order":order,"passed":False,
                          "reason":str(exc)[:600]})
    return {"architecture":"CE","historical_training_only":True,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "trading_authorized":False,"cases":cases,
            "decision":"PASS_CE_INDEPENDENT_EVENT_REPLAY_ONLY" if all(c["passed"] for c in cases)
                else "BLOCK_CE_INDEPENDENT_EVENT_REPLAY"}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    a=p.parse_args();result=run()
    with open(a.output,"w") as f:json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)
    print("CE_REPLAY",result["decision"])
    for x in result["cases"]:
        print("CE_CASE",x["fee"],x["order"],x["passed"],
              "settled_hours",x.get("settled_hours"),
              "81_corner_checks",x.get("actual_independent_81_corner_checks"),
              "error",x.get("reason"))
    raise SystemExit(0 if all(c["passed"] for c in result["cases"]) else 2)
