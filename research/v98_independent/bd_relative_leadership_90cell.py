#!/usr/bin/env python3
"""BD preregistered 90-cell ACTUAL-OPEN native carry-quality historical training.
Only Dec2022-Dec2024 pinned Clean4, 2025 holdout never loaded.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math
import numpy as np
from bd_relative_leadership_sources import source_bundle
from bd_relative_leadership_allocator import BDAllocator
from aw_component_governor import freeze_rows
from ba_ratio_reversion_governor import BAGovernor
from v98_staged_exit_viability_governor_v2 import (
    prior_min_exit_window_quote,FEES,ORDERS)
from ak_slow_compound_execution import risk_history
from phase1246_ai_two_stage_margin import settle_hour
from phase1260_aj_authenticated_source_digest import load_official,HOURS

PATHS=("BD_core_only","BD_full","BD_minus_opportunity",
       "BD_minus_RV","BD_minus_stress")
CAPITAL={"immediate":10000.,"capacity_1m":1e6,"capacity_10m":1e7}
FIRST_2023=744
FIRST_2024=9504
START_EXECUTION=2016

def metrics(dollars,returns,positive_days,total_days):
    d=np.asarray(dollars,dtype=float)
    r=np.asarray(returns,dtype=float)
    win=d[d>1e-10];loss=-d[d< -1e-10]
    var=float(np.quantile(r,.01)) if len(r) else None
    return {
        "hourly_net_profit_factor":float(win.sum()/loss.sum()) if len(loss) and loss.sum() else None,
        "hourly_net_payoff":float(win.mean()/loss.mean()) if len(win) and len(loss) else None,
        "hourly_net_win_rate":float(len(win)/(len(win)+len(loss))) if len(win)+len(loss) else 0.,
        "positive_utc_days":int(positive_days),"total_utc_days":int(total_days),
        "positive_day_fraction":float(positive_days/total_days) if total_days else 0.,
        "worst_hour_net_return":float(r.min()) if len(r) else None,
        "hourly_vas_1pct":var,
        "hourly_cvas_1pct":float(r[r<=var].mean()) if var is not None else None,
        "positive_hours":int(len(win)),"negative_hours":int(len(loss)),
    }

def prepare_risk(frames):
    o,h,l,c,q,r,e,ml,mh=frames
    risks=[None]*HOURS
    for t in range(START_EXECUTION,HOURS):
        down,up,bound,_=risk_history(o,h,l,r,e,q,t)
        exitq=prior_min_exit_window_quote(q,t)
        risks[t]=(down,up,bound,exitq)
    return risks

def preregistered_decisions(path,frames,sources):
    if path not in PATHS:raise ValueError("BD_UNKNOWN_PATH")
    c,r,e=frames[3],frames[5],frames[6]
    a=BDAllocator()
    changes=np.zeros((HOURS,4),dtype=bool)
    targets=np.zeros((HOURS,4,4))
    for t in range(HOURS):
        s=np.stack([sources[j][t] for j in range(4)])
        if path=="BD_core_only":s[1:]=0.
        elif path=="BD_minus_opportunity":s[1]=0.
        elif path=="BD_minus_RV":s[2]=0.
        elif path=="BD_minus_stress":s[3]=0.
        lr=np.log(c[t]/c[t-1]) if t else np.zeros(4)
        a.observe(lr,r[t],e[t])
        w,changed=a.decide(s,str(sources[4]["state"][t]),t)
        changes[t]=changed
        targets[t]=w
    return targets,changes

def cell(path,mode,fee,order,frames,risks,decisions):
    o,h,l,c,q,r,e,ml,mh=frames
    weights,changes=decisions
    cash=float(CAPITAL[mode]);initial=cash
    old=np.zeros(4);governor=BAGovernor()
    frozen_rows=np.zeros((4,4))
    peak=cash;max_dd=0.;min_nav=cash
    gross_peak=net_peak=concentration_peak=0.
    fees=slippage=funding=turnover=0.
    fills=0;target_updates=0
    year_start={"2023":cash};year_end={}
    year_peak={"2023":cash};year_dd={"2023":0.,"2024":0.}
    deltas={"2023":[],"2024":[]};returns={"2023":[],"2024":[]}
    days={"2023":0,"2024":0};positive={"2023":0,"2024":0}
    day_start=cash
    for t in range(HOURS):
        if t>=FIRST_2023:
            year="2023" if t<FIRST_2024 else "2024"
            if t==FIRST_2024:
                year_start["2024"]=cash
                year_peak["2024"]=cash
                day_start=cash
            previous_cash=cash
            if t>=START_EXECUTION:
                try:
                    down,up,bound,exitq=risks[t]
                    target=governor.trade(
                        cash,old,c[t-1],o[t],down,up,bound,q[t-1],exitq,
                        fee_mode=fee,funding_order=order)
                    # Ignore sub-cent spread orders: do not invent fills.
                    target=np.where(np.abs((target-old)*o[t])<1e-7,old,target)
                    out=settle_hour(
                        cash,old,c[t-1],o[t],h[t],l[t],c[t],
                        target,r[t],e[t],ml[t],mh[t],
                        fee_mode=fee,funding_order=order)
                except Exception as exc:
                    raise ValueError("BD_T"+str(t)+"_"+str(exc)) from exc
                cash=float(out["cash"]);old=out["units"].copy()
                if (out["hidden_borrow"] or not out["cash_settled"]
                    or not np.isclose(out["equity"],cash,rtol=0,atol=1e-7)):
                    raise ValueError("BD_NBD_RECONCILIATION_T"+str(t))
                fees+=out["fees"];slippage+=out["slippage"]
                funding+=out["funding"];turnover+=out["turnover"]
                fills+=int(out["turnover"]>1e-5)
                notionals=np.abs(old*c[t]);gross=float(notionals.sum())
                gross_peak=max(gross_peak,gross/cash)
                net_peak=max(net_peak,abs(float(old@c[t]))/cash)
                if gross>0:concentration_peak=max(
                    concentration_peak,float(notionals.max()/gross))
            delta=cash-previous_cash
            deltas[year].append(float(delta))
            returns[year].append(float(delta/previous_cash))
            peak=max(peak,cash);min_nav=min(min_nav,cash)
            max_dd=max(max_dd,1.-cash/peak)
            year_peak[year]=max(year_peak[year],cash)
            year_dd[year]=max(year_dd[year],1.-cash/year_peak[year])
            if t%24==23:
                days[year]+=1;positive[year]+=int(cash>day_start)
                day_start=cash
            if t==FIRST_2024-1:year_end["2023"]=cash
            if t==HOURS-1:year_end["2024"]=cash
        # Signals close at t, unit orders first eligible at t+1 open.
        if changes[t].any():
            frozen_rows=freeze_rows(frozen_rows,weights[t],changes[t],cash,c[t])
            governor.signal_components(frozen_rows.sum(axis=0))
            target_updates+=1
    annual={}
    for yr,duration in (("2023",365),("2024",366)):
        start,end=year_start[yr],year_end[yr]
        annual[yr]={
            "start_nav":float(start),"end_nav":float(end),
            "net_return":float(end/start-1.),
            "annualized_cagr":float((end/start)**(365.25/duration)-1.),
            "net_log_growth":float(math.log(end/start)),
            "max_drawdown":float(year_dd[yr]),
            **metrics(deltas[yr],returns[yr],positive[yr],days[yr]),
        }
    return {
        "path":path,"mode":mode,"fee":fee,"order":order,
        "passed":True,"historical_training_only":True,
        "validation_2025_read":False,"external_benchmarks_used":False,
        "executed_hours":HOURS-START_EXECUTION,
        "target_updates":target_updates,"physical_fill_hours":fills,
        "forced_risk_ratchets":governor.forced_ratchets,
        "initial_nav":initial,"final_nav":cash,
        "net_total_return":float(cash/initial-1.),
        "net_log_growth":float(math.log(cash/initial)),
        "two_year_cagr":float((cash/initial)**(365.25/731)-1.),
        "max_drawdown":float(max_dd),"min_nav":float(min_nav),
        "max_gross_to_nav":float(gross_peak),
        "max_abs_net_to_nav":float(net_peak),
        "max_single_asset_gross_concentration":float(concentration_peak),
        "turnover":float(turnover),"fees":float(fees),
        "slippage":float(slippage),"funding":float(funding),
        "annual":annual,
        **metrics(deltas["2023"]+deltas["2024"],
                  returns["2023"]+returns["2024"],
                  positive["2023"]+positive["2024"],
                  days["2023"]+days["2024"]),
    }

def run(path):
    frames,manifest=load_official()
    sources=source_bundle(frames[3],frames[4],frames[5],frames[6])
    decisions=preregistered_decisions(path,frames,sources)
    risks=prepare_risk(frames)
    cells=[]
    for mode,fee,order in itertools.product(CAPITAL,FEES,ORDERS):
        try:cells.append(cell(path,mode,fee,order,frames,risks,decisions))
        except Exception as exc:
            cells.append({
                "path":path,"mode":mode,"fee":fee,"order":order,
                "passed":False,"reason":str(exc)[:450],
                "historical_training_only":True,"validation_2025_read":False})
    passed=len(cells)==18 and all(x["passed"] for x in cells)
    return {
        "architecture":"BD","path":path,
        "historical_training_only":True,"validation_2025_read":False,
        "external_benchmarks_used":False,"cells_expected":18,
        "source_manifest_sha256":hashlib.sha256(
            json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "cells":cells,
        "decision":"PASS_BD_PATH_18_MECHANICAL_ONLY" if passed else
                   "REJECT_BD_PATH_SURVIVAL",
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--path",choices=PATHS,required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    result=run(args.path)
    with open(args.output,"w") as f:
        json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
    print("BD_TRAINING_PATH",result["path"],result["decision"],
          "survived",sum(c["passed"] for c in result["cells"]),
          "of",len(result["cells"]))
    raise SystemExit(0 if all(c["passed"] for c in result["cells"]) else 2)
