#!/usr/bin/env python3
"""JB preregistered causal online shadow allocator seven-slot shared-collateral 30-cell USD10k historical TRAINING only.
Causal completed-close source; next actual open; exact Dec-2022 warmup and pinned 2023-2024 native funding.
No 2025, V99, frozen engines, paper, live orders or external benchmarks.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math
import numpy as np
from pathlib import Path
from jb_regime_regret_sources import bundle,WARMUP,static_check,GROSS
from gl_order_invariant_governor import GLOrderInvariantBufferedGovernor as HEBufferedGovernor
from v98_staged_exit_viability_governor_v2 import FEES,ORDERS,prior_min_exit_window_quote
# JB-local equivalent of generic prior-only risk bounds; generic helper has
# an unrelated 2016h guard despite needing only 672h history.
def jb_prior_only_risk_history(opening,high,low,rate,event,quote,t):
    if t<672 or t>len(opening):
        raise ValueError("JB_INSUFFICIENT_PRIOR_RISK_HISTORY")
    down=np.maximum(.40,np.max(1.-low[t-336:t]/opening[t-336:t],axis=0))
    up=np.maximum(.65,np.max(high[t-336:t]/opening[t-336:t]-1.,axis=0))
    funding=np.maximum(.0005,3.*np.max(
        np.abs(rate[t-672:t]*event[t-672:t]),axis=0))
    min_quote=np.min(quote[t-336:t],axis=0)
    return down,up,funding,min_quote

from phase1246_ai_two_stage_margin import settle_hour
from phase1260_aj_authenticated_source_digest import load_official,HOURS

PATIC=("JB_core_only","JB_full","JB_minus_opportunity","JB_minus_RV","JB_minus_stress")
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
        down,up,f,_=jb_prior_only_risk_history(o,h,l,r,e,q,t)
        out[t]=(down,up,f,prior_min_exit_window_quote(q,t))
    return out

def cell(path,mode,fee,order,frames,risks,sources):
    o,h,l,c,q,r,e,ml,mh=frames
    targets,updates,regimes,validity,forecasts=sources
    cash=float(CAPITAL[mode])
    initial=cash
    old=np.zeros(4)
    governor=HEBufferedGovernor()
    peak=cash;max_de=0.;min_nav=cash
    gross_peak=net_peak=concentration_peak=0.
    fees=slippage=funding=turnover=0.
    fills=target_updates=0
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
                        raise ValueError("JB_LEDGER")
                    cash=float(settled["cash"]);old=settled["units"].copy()
                    fees+=settled["fees"];slippage+=settled["slippage"]
                    funding+=settled["funding"];turnover+=settled["turnover"]
                    fills+=int(settled["turnover"]>1e-5)
                    gross=float(np.sum(abs(old*c[t])))
                    if cash<=0:raise ValueError("JB_NAV_NONPOSITIVE")
                    gross_peak=max(gross_peak,gross/cash)
                    net_peak=max(net_peak,abs(float(old@c[t]))/cash)
                    if gross>0:concentration_peak=max(concentration_peak,
                        float(np.max(abs(old*c[t]))/gross))
                except Exception as exc:
                    raise ValueError("JB_T"+str(t)+"_"+str(exc)) from exc
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
        # Independently funded four-expert causal shadow-growth composed engine.
        # Unqualified and ablated experts finance Core rather than
        # simulated with zero-return synthetic PnL. Every ablation replays
        # the complete physical ledger from USD10k.
        if t>=WARMUP and updates[t]:
            # JB joint forecast optimization is computed causally for each
            # independently funded ablation. No post-result sleeve selection.
            weights=targets[t,PATIC.index(path)].copy()
            if not validity[t] and not np.allclose(weights,targets[t,0]):
                raise ValueError("JB_INVALID_QUOTE_TARGET")
            if np.abs(weights).sum()>1.+1e-10:
                raise ValueError("JB_GROSS_NONCONSERVATION")
            governor.signal_components(weights*GROSS[regimes[t]]*cash/c[t])
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
            "forced_risk_ratchets":governor.forced_ratchets,
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
    return {"architecture":"JB","path":path,
            "historical_training_only":True,"validation_2025_read":False,
            "external_benchmarks_used":False,
            "source_manifest_sha256":hashlib.sha256(json.dumps(
                manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            "cells_expected":6,"cells":cases,
            "decision":"PASS_JB_MECHANICAL_ONLY" if len(cases)==6 and
            all(x["passed"] for x in cases) else "BLOCK_JB_PHYSICAL_SURVIVAL"}

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
            print("JB_PHYSICAL_FITST_FAULT",failed["fee"],failed["order"],failed.get("reason","unknown"))
    print("JB_PATH",a.path,result["decision"],
          sum(c["passed"] for c in result["cells"]),"/",len(result["cells"]))
    raise SystemExit(0 if all(c["passed"] for c in result["cells"]) else 2)
