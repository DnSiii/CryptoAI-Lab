#!/usr/bin/env python3
"""BX independent ringfenced four-book seven-slot historical physical training.
Dec2022 warmup; ONLY 2023/2024 execution. 2025 sealed.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math
import numpy as np
from bx_sources import source_bundle
from bx_allocator import BXAllocator
from bx_ringfenced_governor import BXRingfencedGovernor,INITIAL_SHARES
from v98_staged_exit_viability_governor_v2 import (
    prior_min_exit_window_quote,FEES,ORDERS)
from ak_slow_compound_execution import risk_history
from phase1246_ai_two_stage_margin import settle_hour
from phase1260_aj_authenticated_source_digest import load_official,HOURS

PATHS=("BX_core_only","BX_full","BX_minus_opportunity",
       "BX_minus_RV","BX_minus_stress")
CAPITAL={"immediate":10000.,"capacity_1m":1e6,"capacity_10m":1e7}
FIRST_2023=744
FIRST_2024=9504
START_EXECUTION=2161

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
        down,up,bpund,_=risk_history(o,h,l,r,e,q,t)
        exitq=prior_min_exit_window_quote(q,t)
        risks[t]=(down,up,bpund,exitq)
    return risks

def preregistered_decisions(path,frames,sources):
    if path not in PATHS:raise ValueError("BX_UNKNOWN_PATH")
    a=BXAllocator()
    weights=np.zeros((HOURS,4,4))
    changes=np.zeros((HOURS,4),dtype=bool)
    for t in range(HOURS):
        sleeves=np.stack([sources[j][t] for j in range(4)])
        w,mask=a.decide(sleeves,str(sources[4]["state"][t]),t,
                        float(sources[4]["vol"][t]))
        if path=="BX_core_only":w[1:]=0.
        elif path=="BX_minus_opportunity":w[1]=0.
        elif path=="BX_minus_RV":w[2]=0.
        elif path=="BX_minus_stress":w[3]=0.
        weights[t]=w
        changes[t]=mask
    return weights,changes

def cell(path,mode,fee,order,frames,risks,decisions):
    o,h,l,c,q,r,e,ml,mh=frames
    weights,changes=decisions
    initial=float(CAPITAL[mode])
    book_cash=INITIAL_SHARES.copy()*initial
    book_old=np.zeros((4,4))
    governor=BXRingfencedGovernor()
    peak=initial;min_nav=initial;max_dd=0.
    gross_peak=net_peak=concentration_peak=0.
    fees=slippage=funding=turnover=0.
    book_fees=np.zeros(4);book_slippage=np.zeros(4)
    book_funding=np.zeros(4);book_turnover=np.zeros(4)
    fills=0;target_updates=0
    year_start={"2023":initial};year_end={}
    year_book_start={"2023":book_cash.copy()};year_book_end={}
    year_peak={"2023":initial};year_dd={"2023":0.,"2024":0.}
    deltas={"2023":[],"2024":[]};returns={"2023":[],"2024":[]}
    days={"2023":0,"2024":0};positive={"2023":0,"2024":0}
    day_start=initial
    for t in range(HOURS):
        if t>=FIRST_2023:
            year="2023" if t<FIRST_2024 else "2024"
            if t==FIRST_2024:
                year_start["2024"]=float(book_cash.sum())
                year_book_start["2024"]=book_cash.copy()
                year_peak["2024"]=float(book_cash.sum())
                day_start=float(book_cash.sum())
            previous_cash=float(book_cash.sum())
            if t>=START_EXECUTION:
                try:
                    down,up,bpund,exitq=risks[t]
                    prior=book_old.copy()
                    for i in range(4):
                        g=governor.governors[i]
                        if (not np.any(book_old[i]) and
                            not g.needs_authorization and
                            not np.any(g.authorized)):
                            continue
                        target=governor.trade_one(
                            i,float(book_cash[i]),book_old[i],c[t-1],o[t],
                            down,up,bpund,q[t-1],exitq,fee,order)
                        target=np.where(np.abs((target-book_old[i])*o[t])<1e-7,
                                        book_old[i],target)
                        out=settle_hour(
                            float(book_cash[i]),book_old[i],c[t-1],
                            o[t],h[t],l[t],c[t],target,r[t],e[t],ml[t],mh[t],
                            fee_mode=fee,funding_order=order)
                        if (out["hidden_borrow"] or not out["cash_settled"]
                            or not np.isclose(out["equity"],out["cash"],rtol=0,atol=1e-7)):
                            raise ValueError("BX_BOOK_LEDGER_RECONCILIATION")
                        book_cash[i]=float(out["cash"])
                        book_old[i]=out["units"].copy()
                        book_fees[i]+=out["fees"]
                        book_slippage[i]+=out["slippage"]
                        book_funding[i]+=out["funding"]
                        book_turnover[i]+=out["turnover"]
                        fills+=int(out["turnover"]>1e-5)
                    governor.assert_aggregate_physical(prior,book_old,o[t],q[t-1])
                except Exception as exc:
                    raise ValueError("BX_T"+str(t)+"_"+str(exc)) from exc
                nav=float(book_cash.sum())
                notionals=np.sum(np.abs(book_old*c[t]),axis=0)
                gross=float(notionals.sum())
                gross_peak=max(gross_peak,gross/nav)
                net_peak=max(net_peak,abs(float(book_old.sum(axis=0)@c[t]))/nav)
                if gross>0:
                    concentration_peak=max(concentration_peak,float(notionals.max()/gross))
            cash=float(book_cash.sum())
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
            if t==FIRST_2024-1:
                year_end["2023"]=cash
                year_book_end["2023"]=book_cash.copy()
            if t==HOURS-1:
                year_end["2024"]=cash
                year_book_end["2024"]=book_cash.copy()
        # A completed t close may only signal an order at t+1 open.
        for i in np.flatnonzero(changes[t]):
            requested=weights[t,i]*book_cash[i]/c[t]
            governor.signal(int(i),requested)
            target_updates+=1
    fees=float(book_fees.sum());slippage=float(book_slippage.sum())
    funding=float(book_funding.sum());turnover=float(book_turnover.sum())
    annual={}
    for yr,duration in (("2023",365),("2024",366)):
        start,end=year_start[yr],year_end[yr]
        annual[yr]={
            "start_nav":float(start),"end_nav":float(end),
            "net_return":float(end/start-1.),
            "annualized_cagr":float((end/start)**(365.25/duration)-1.),
            "net_log_growth":float(math.log(end/start)),
            "max_drawdown":float(year_dd[yr]),
            "book_start_nav":year_book_start[yr].tolist(),
            "book_end_nav":year_book_end[yr].tolist(),
            **metrics(deltas[yr],returns[yr],positive[yr],days[yr]),
        }
    return {
        "path":path,"mode":mode,"fee":fee,"order":order,
        "passed":True,"historical_training_only":True,
        "validation_2025_read":False,"external_benchmarks_used":False,
        "executed_hours":HOURS-START_EXECUTION,
        "target_updates":target_updates,"physical_book_fill_hours":fills,
        "forced_risk_ratchets":sum(g.forced_ratchets for g in governor.governors),
        "initial_nav":initial,"final_nav":float(book_cash.sum()),
        "book_final_nav":book_cash.tolist(),
        "book_fees":book_fees.tolist(),"book_slippage":book_slippage.tolist(),
        "book_funding":book_funding.tolist(),"book_turnover":book_turnover.tolist(),
        "net_total_return":float(book_cash.sum()/initial-1.),
        "net_log_growth":float(math.log(book_cash.sum()/initial)),
        "two_year_cagr":float((book_cash.sum()/initial)**(365.25/731)-1.),
        "max_drawdown":float(max_dd),"min_nav":float(min_nav),
        "max_gross_to_nav":float(gross_peak),
        "max_abs_net_to_nav":float(net_peak),
        "max_single_asset_gross_concentration":float(concentration_peak),
        "turnover":turnover,"fees":fees,"slippage":slippage,"funding":funding,
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
                "passed":False,"reason":str(exc)[:500],
                "historical_training_only":True,"validation_2025_read":False})
    passed=len(cells)==18 and all(x["passed"] for x in cells)
    return {
        "architecture":"BX","path":path,
        "historical_training_only":True,"validation_2025_read":False,
        "external_benchmarks_used":False,"cells_expected":18,
        "source_manifest_sha256":hashlib.sha256(
            json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "cells":cells,
        "decision":"PASS_BX_PATH_18_MECHANICAL_ONLY" if passed else
                   "REJECT_BX_PATH_SURVIVAL",
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--path",choices=PATHS,required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    result=run(args.path)
    with open(args.output,"w") as f:
        json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
    print("BX_TRAINING_PATH",result["path"],result["decision"],
          "survived",sum(c["passed"] for c in result["cells"]),
          "of",len(result["cells"]))
    raise SystemExit(0 if passed else 2)
