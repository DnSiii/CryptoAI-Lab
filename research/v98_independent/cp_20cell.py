#!/usr/bin/env python3
"""CP preregistered structural growth and native carry-spread seven-slot shared-collateral seven-slot 20-cell USD10k fail-fast historical TRAINING only.
Causal completed-close source; next actual open; pinned 2022-2024 native funding.
No 2025, V99, frozen engines, paper, live orders or external benchmarks.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math
import numpy as np
from cp_sources import bundle,BUDGETS,WARMUP,static_check
from cg_buffered_governor import CGBufferedGovernor as CPBufferedGovernor
from v98_staged_exit_viability_governor_v2 import FEES,ORDERS,prior_min_exit_window_quote
from ak_slow_compound_execution import risk_history
from phase1246_ai_two_stage_margin import settle_hour
from phase1260_aj_authenticated_source_digest import load_official,HOURS

PATHS=("CP_core_only","CP_full","CP_minus_opportunity","CP_minus_RV","CP_minus_stress")
CAPITAL={"immediate":10000.}
FIRST_2023=744
FIRST_2024=9504
START_EXECUTION=WARMUP+1
INCLUDED={
    "CP_core_only":(0,),
    "CP_full":(0,1,2,3),
    "CP_minus_opportunity":(0,2,3),
    "CP_minus_RV":(0,1,3),
    "CP_minus_stress":(0,1,2),
}

def metrics(dollars,returns,positive_days,total_days):
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
        down,up,f,_=risk_history(o,h,l,r,e,q,t)
        out[t]=(down,up,f,prior_min_exit_window_quote(q,t))
    return out

def cell(path,mode,fee,order,frames,risks,sources):
    o,h,l,c,q,r,e,ml,mh=frames
    signals,updates,regimes=sources
    cash=float(CAPITAL[mode])
    initial=cash
    old=np.zeros(4)
    module_units=np.zeros((4,4))
    governor=CPBufferedGovernor()
    peak=cash;max_dd=0.;min_nav=cash
    gross_peak=net_peak=concentration_peak=0.
    fees=slippage=funding=turnover=0.
    fills=target_updates=0
    years={"2023":{"start_nav":initial,"deltas":[],"returns":[],"days":0,"positive":0,
                   "peak":initial,"dd":0.},
           "2024":{"start_nav":None,"deltas":[],"returns":[],"days":0,"positive":0,
                   "peak":None,"dd":0.}}
    day_start=initial
    for t in range(HOURS):
        if t>=FIRST_2023:
            yr="2023" if t<FIRST_2024 else "2024"
            y=years[yr]
            if t==FIRST_2024:
                y["start_nav"]=cash;y["peak"]=cash;day_start=cash
            previous=cash
            if t>=START_EXECUTION and (np.any(old) or governor.needs_authorization
                                       or np.any(governor.authorized)):
                try:
                    down,up,bound,exitq=risks[t]
                    target=governor.trade(cash,old,c[t-1],o[t],down,up,bound,
                                          q[t-1],exitq,fee_mode=fee,
                                          funding_order=order)
                    target=np.where(abs((target-old)*o[t])<1e-7,old,target)
                    settled=settle_hour(cash,old,c[t-1],o[t],h[t],l[t],c[t],
                                        target,r[t],e[t],ml[t],mh[t],
                                        fee_mode=fee,funding_order=order)
                    if (settled["hidden_borrow"] or not settled["cash_settled"]
                        or not math.isclose(settled["cash"],settled["equity"],rel_tol=0,abs_tol=1e-7)):
                        raise ValueError("CP_LEDGER")
                    cash=float(settled["cash"]);old=settled["units"].copy()
                    fees+=settled["fees"];slippage+=settled["slippage"]
                    funding+=settled["funding"];turnover+=settled["turnover"]
                    fills+=int(settled["turnover"]>1e-5)
                    gross=float(np.sum(abs(old*c[t])))
                    if cash<=0:raise ValueError("CP_NAV_NONPOSITIVE")
                    gross_peak=max(gross_peak,gross/cash)
                    net_peak=max(net_peak,abs(float(old@c[t]))/cash)
                    if gross>0:concentration_peak=max(concentration_peak,
                        float(np.max(abs(old*c[t]))/gross))
                except Exception as exc:
                    raise ValueError("CP_T"+str(t)+"_"+str(exc)) from exc
            delta=cash-previous
            y["deltas"].append(float(delta))
            y["returns"].append(float(delta/previous))
            peak=max(peak,cash);min_nav=min(min_nav,cash)
            max_dd=max(max_dd,1.-cash/peak)
            y["peak"]=max(y["peak"],cash)
            y["dd"]=max(y["dd"],1.-cash/y["peak"])
            if t%24==23:
                y["days"]+=1;y["positive"]+=int(cash>day_start)
                day_start=cash
            if t==FIRST_2024-1:years["2023"]["end_nav"]=cash
            if t==HOURS-1:years["2024"]["end_nav"]=cash
        # At completed close t, freeze only the newly updated module units.
        # Other module units remain fixed (not silently rebalanced).
        if t>=WARMUP and updates[t].any():
            mask=np.array([i in INCLUDED[path] for i in range(4)]) & updates[t]
            if mask.any():
                for i in np.flatnonzero(mask):
                    module_units[i]=signals[t,i]*BUDGETS[str(regimes[t])][i]*cash/c[t]
                governor.signal_components(module_units.sum(axis=0))
                target_updates+=1
    annual={}
    for yr,duration in (("2023",365),("2024",366)):
        y=years[yr]
        start,end=y["start_nav"],y["end_nav"]
        annual[yr]={"start_nav":float(start),"end_nav":float(end),
                    "net_return":float(end/start-1.),
                    "annualized_cagr":float((end/start)**(365.25/duration)-1.),
                    "net_log_growth":float(math.log(end/start)),
                    "max_drawdown":float(y["dd"]),
                    **metrics(y["deltas"],y["returns"],y["positive"],y["days"])}
    return {"path":path,"mode":mode,"fee":fee,"order":order,"passed":True,
            "historical_training_only":True,"validation_2025_read":False,
            "external_benchmarks_used":False,"trading_authorized":False,
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
            "fees":float(fees),"slippage":float(slippage),
            "funding":float(funding),"turnover":float(turnover),
            "annual":annual,
            **metrics(years["2023"]["deltas"]+years["2024"]["deltas"],
                      years["2023"]["returns"]+years["2024"]["returns"],
                      years["2023"]["positive"]+years["2024"]["positive"],
                      years["2023"]["days"]+years["2024"]["days"])}

def run(path):
    frames,manifest=load_official()
    source=bundle(frames[3],frames[5],frames[6],frames[4])
    risks=prepare_risks(frames)
    cases=[]
    for mode,fee,order in itertools.product(CAPITAL,("base","severe"),ORDERS):
        try:cases.append(cell(path,mode,fee,order,frames,risks,source))
        except Exception as exc:
            cases.append({"path":path,"mode":mode,"fee":fee,"order":order,
                          "passed":False,"reason":str(exc)[:600],
                          "historical_training_only":True,"validation_2025_read":False})
    return {"architecture":"CP","path":path,
            "historical_training_only":True,"validation_2025_read":False,
            "external_benchmarks_used":False,
            "source_manifest_sha256":hashlib.sha256(json.dumps(
                manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            "cells_expected":4,"cells":cases,
            "decision":"PASS_CP_MECPANICAL_ONLY" if len(cases)==4 and
            all(x["passed"] for x in cases) else "BLOCP_CP_PHYSICAL_SURVIVAL"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--path",required=True,choices=PATHS)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    assert static_check()
    result=run(a.path)
    with open(a.output,"w") as f:json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
    print("CP_PATH",a.path,result["decision"],
          sum(c["passed"] for c in result["cells"]),"/",len(result["cells"]))
    raise SystemExit(0 if all(c["passed"] for c in result["cells"]) else 2)
