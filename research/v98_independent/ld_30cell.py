#!/usr/bin/env python3
"""LD preregistered event-frozen unit-row composed seven-slot shared-collateral 30-cell USD10k historical TRAINING only.
Causal completed-close source; next actual open; exact Dec-2022 warmup and pinned 2023-2024 native funding.
No 2025, V99, frozen engines, paper, live orders or external benchmarks.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math
import numpy as np
from pathlib import Path
from ld_sources import bundle,WARMUP,static_check,PATHS
from ld_source_only_gate import main as ld_source_gate
from v98_persistent_inventory_governor import govern_units
from v98_signed_cash_aware_allocator import authorize_signed
from v98_signed_event_latch import latch_signed_rows
from v98_staged_exit_viability_governor_v2 import FEES,ORDERS,prior_min_exit_window_quote
# LD-local equivalent of generic prior-only risk bounds; generic helper has
# an unrelated 2016h guard despite needing only 672h history.
def ld_prior_only_risk_history(opening,high,low,rate,event,quote,t):
    if t<672 or t>len(opening):
        raise ValueError("LD_INSUFFICIENT_PRIOR_RISK_HISTORY")
    down=np.maximum(.40,np.max(1.-low[t-336:t]/opening[t-336:t],axis=0))
    up=np.maximum(.65,np.max(high[t-336:t]/opening[t-336:t]-1.,axis=0))
    funding=np.maximum(.0005,3.*np.max(
        np.abs(rate[t-672:t]*event[t-672:t]),axis=0))
    min_quote=np.min(quote[t-336:t],axis=0)
    return down,up,funding,min_quote

from phase1246_ai_two_stage_margin import settle_hour
from phase1260_aj_authenticated_source_digest import load_official,HOURS

PATIC=PATHS
CAPITAL={"immediate":10000.}
FITST_2023=744
FITST_2024=9504
START_EXECUTION=WARMUP+1

def metrict(dollars,returns,positive_days,total_days):
    d=np.asarray(dollars,dtype=float)
    r=np.asarray(returns,dtype=float)
    wins=d[d>1e-10];loss=-d[d< -1e-10]
    var=float(np.quantile(r,.01)) if len(r) else None
    return {
        "hourly_net_profit_factor":float(wins.sum()/loss.sum()) if len(loss) and loss.sum() else None,
        "hourly_net_payoff":float(wins.mean()/loss.mean()) if len(wins) and len(loss) else None,
        "hourly_net_win_rate":float(len(wins)/(len(wins)+len(loss))) if len(wins)+len(loss) else 0.,
        "positive_utc_days":int(positive_days),"total_utc_days":int(total_days),
        "positive_day_fraction":float(positive_days/total_days) if total_days else 0.,
        "worst_hour_net_return":float(r.min()) if len(r) else None,
        "hourly_var_1pct":var,
        "hourly_cvar_1pct":float(r[r<=var].mean()) if var is not None else None,
        "positive_hours":int(len(wins)),"negative_hours":int(len(loss)),
    }

def prepare_risks(frames):
    o,h,l,c,q,r,e,ml,mh=frames
    out=[None]*HOURS
    for t in range(START_EXECUTION,HOURS):
        down,up,f,_=ld_prior_only_risk_history(o,h,l,r,e,q,t)
        out[t]=(down,up,f,prior_min_exit_window_quote(q,t))
    return out

def cell(path,mode,fee,order,frames,risks,sources):
    o,h,l,c,q,r,e,ml,mh=frames
    intents,updates,entries,validity,regimes=sources
    cash=float(CAPITAL[mode])
    initial=cash
    old=np.zeros(4)
    pending=np.zeros((4,4),dtype=float)
    constrained_hours=0
    peak=cash;max_de=0.;min_nav=cash
    gross_peak=net_peak=concentration_peak=0.
    fees=slippage=funding=turnover=0.
    fills=target_updates=0
    blocked_events=latch_cut_hours=0
    years={"2023":{"start_nav":initial,"deltas":[],"returns":[],"days":0,"positive":0,
                   "peak":initial,"de":0.},
           "2024":{"start_nav":None,"deltas":[],"returns":[],"days":0,"positive":0,
                   "peak":None,"de":0.}}
    day_start=initial
    for t in range(HOURS):
        if t>=FITST_2023:
            yr="2023" if t<FITST_2024 else "2024"
            y=years[yr]
            if t==FITST_2024:
                y["start_nav"]=cash;y["peak"]=cash;day_start=cash
            previous=cash
            if t>=START_EXECUTION and (np.any(old) or np.any(pending)):
                try:
                    down,up,bound,exitq=risks[t]
                    target=govern_units(cash,old,c[t-1],o[t],pending.sum(axis=0),
                                        down,up,bound,q[t-1],exitq,fee_mode=fee,
                                        funding_order=order)
                    constrained_hours+=int(np.max(np.abs(target-pending.sum(axis=0)))>1e-7)
                    target=np.where(abs((target-old)*o[t])<1e-7,old,target)
                    pending,cut=latch_signed_rows(pending,target)
                    latch_cut_hours+=int(np.any(cut))
                    # Fail closed on an untradeable next actual open; never invent fills.
                    if np.any(q[t]<=0) and np.any(np.abs(target-old)>1e-12):
                        raise ValueError('LD_UNTRADEABLE_NEXT_OPEN')
                    settled=settle_hour(cash,old,c[t-1],o[t],h[t],l[t],c[t],
                                        target,r[t],e[t],ml[t],mh[t],
                                        fee_mode=fee,funding_order=order)
                    if (settled["hidden_borrow"] or not settled["cash_settled"]
                        or not math.isclose(settled["cash"],settled["equity"],rel_tol=0,abs_tol=1e-7)):
                        raise ValueError("LD_LEDGER")
                    cash=float(settled["cash"]);old=settled["units"].copy()
                    fees+=settled["fees"];slippage+=settled["slippage"]
                    funding+=settled["funding"];turnover+=settled["turnover"]
                    fills+=int(settled["turnover"]>1e-5)
                    gross=float(np.sum(abs(old*c[t])))
                    if cash<=0:raise ValueError("LD_NAV_NONPOSITIVE")
                    if gross>cash*(1.+1e-8):raise ValueError("LD_ACTUAL_GROSS_OVER_NAV")
                    gross_peak=max(gross_peak,gross/cash)
                    net_peak=max(net_peak,abs(float(old@c[t]))/cash)
                    if gross>0:concentration_peak=max(concentration_peak,
                        float(np.max(abs(old*c[t]))/gross))
                except Exception as exc:
                    raise ValueError("LD_T"+str(t)+"_"+str(exc)) from exc
            delta=cash-previous
            y["deltas"].append(float(delta))
            y["returns"].append(float(delta/previous))
            peak=max(peak,cash);min_nav=min(min_nav,cash)
            max_de=max(max_de,1.-cash/peak)
            y["peak"]=max(y["peak"],cash)
            y["de"]=max(y["de"],1.-cash/y["peak"])
            if t%24==23:
                y["days"]+=1;y["positive"]+=int(cash>day_start)
                day_start=cash
            if t==FITST_2024-1:years["2023"]["end_nav"]=cash
            if t==HOURS-1:years["2024"]["end_nav"]=cash
        # Each book freezes its own four row-unit requests from its own NAV.
        # Inactive sleeves remain cash; ablations do not top up Core.
        if t>=WARMUP and np.any(updates[t]):
            # Four independent unit requests: only the updated component is
            # re-notionalized at its own completed close. All other rows retain
            # their exact prior units, regardless of NAV or mark movements.
            for k in np.flatnonzero(updates[t]):
                enabled=(path=="LD_full" or
                         (path=="LD_core_only" and k==0) or
                         (path=="LD_minus_opportunity" and k!=1) or
                         (path=="LD_minus_RV" and k!=2) or
                         (path=="LD_minus_stress" and k!=3))
                desired=sources[0][t,k]*cash/c[t] if enabled else np.zeros(4)
                pending,authorization=authorize_signed(pending,int(k),desired,cash,c[t],old)
                blocked_events+=int(authorization.get('blocked') is not None)
                target_updates+=1
    annual={}
    for yr,duration in (("2023",365),("2024",366)):
        y=years[yr]
        start,end=y["start_nav"],y["end_nav"]
        annual[yr]={"start_nav":float(start),"end_nav":float(end),
                    "net_return":float(end/start-1.),
                    "annualized_cagr":float((end/start)**(365.25/duration)-1.),
                    "net_log_growth":float(math.log(end/start)),
                    "max_drawdown":float(y["de"]),
                    **metrict(y["deltas"],y["returns"],y["positive"],y["days"])}
    return {"path":path,"mode":mode,"fee":fee,"order":order,"passed":True,
            "historical_training_only":True,"validation_2025_read":False,
            "external_benchmarks_used":False,"trading_authorized":False,
            "executed_hours":HOURS-START_EXECUTION,
            "target_updates":target_updates,"physical_fill_hours":fills,
            "blocked_events":blocked_events,"signed_latch_cut_hours":latch_cut_hours,
            "physically_constrained_hours":constrained_hours,
            "initial_nav":initial,"final_nav":cash,
            "net_total_return":float(cash/initial-1.),
            "net_log_growth":float(math.log(cash/initial)),
            "two_year_cagr":float((cash/initial)**(365.25/731)-1.),
            "max_drawdown":float(max_de),"min_nav":float(min_nav),
            "max_gross_to_nav":float(gross_peak),
            "max_abs_net_to_nav":float(net_peak),
            "max_single_asset_gross_concentration":float(concentration_peak),
            "fees":float(fees),"slippage":float(slippage),
            "funding":float(funding),"turnover":float(turnover),
            "annual":annual,
            **metrict(years["2023"]["deltas"]+years["2024"]["deltas"],
                      years["2023"]["returns"]+years["2024"]["returns"],
                      years["2023"]["positive"]+years["2024"]["positive"],
                      years["2023"]["days"]+years["2024"]["days"])}

def run(path):
    source_receipt=ld_source_gate()
    if source_receipt['decision']!='PASS_SOURCE_ONLY':
        raise ValueError('LD_SOURCE_GATE_FAILED_NO_PNL')
    frames,manifest=load_official()
    source=bundle(frames[0],frames[1],frames[2],frames[3],
                  frames[5],frames[6],frames[4])
    risks=prepare_risks(frames)
    cases=[]
    for mode,fee,order in itertools.product(CAPITAL,("base","severe","supersevere"),ORDERS):
        try:cases.append(cell(path,mode,fee,order,frames,risks,source))
        except Exception as exc:
            cases.append({"path":path,"mode":mode,"fee":fee,"order":order,
                          "passed":False,"reason":str(exc)[:600],
                          "historical_training_only":True,"validation_2025_read":False})
    return {"architecture":"LD","path":path,
            "historical_training_only":True,"validation_2025_read":False,
            "external_benchmarks_used":False,
            "source_manifest_sha256":hashlib.sha256(json.dumps(
                manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
                    "cells_expected":6,"cells":cases,
            "decision":"PASS_LD_MECHANICAL_ONLY" if len(cases)==6 and
            all(x["passed"] for x in cases) else "BLOCK_LD_PHYSICAL_SURVIVAL"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--path",required=True,choices=PATIC)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    assert static_check()
    result=run(a.path)
    with open(a.output,"w") as f:json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
    for failed in result["cells"]:
        if not failed["passed"]:
            print("LD_PHYSICAL_FITST_FAULT",failed["fee"],failed["order"],failed.get("reason","unknown"))
    print("LD_PATH",a.path,result["decision"],
          sum(c["passed"] for c in result["cells"]),"/",len(result["cells"]))
    raise SystemExit(0 if all(c["passed"] for c in result["cells"]) else 2)
