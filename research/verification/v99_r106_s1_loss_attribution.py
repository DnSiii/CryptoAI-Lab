"""Read-only S1 TRAIN loss decomposition; NOT a candidate, no retuning or validation."""
from __future__ import annotations
import json
import math
import statistics
import sys
from pathlib import Path
from research.verification.independent_v99_r106_s1_spot_train import (
    load, signal, verify_report, START, END, HOUR, N, EDGES,
)

ASSETS=("BTC","ETH")
SCENARIOS={"frictionless_diagnostic":0.,"severe":.0025,"supersevere":.006}

def rebalance(cash,units,prices,target,fee):
    """Self-financing exact post-fee target with a fixed-point solution."""
    if not (0 <= fee < 1) or any(not math.isfinite(prices[a]) or prices[a]<=0 for a in ASSETS):
        raise ValueError("BAD_INPUT")
    nav=cash+sum(units[a]*prices[a] for a in ASSETS)
    if not math.isfinite(nav) or nav<=0 or cash < -1e-8 or min(units.values()) < -1e-12:
        raise ValueError("BAD_INITIAL_ACCOUNT")
    weights={a:(.65 if a==target else 0.) for a in ASSETS}
    old={a:units[a]*prices[a] for a in ASSETS}
    after=nav
    for _ in range(100):
        after=nav-fee*sum(abs(weights[a]*after-old[a]) for a in ASSETS)
    new_units={a:weights[a]*after/prices[a] for a in ASSETS}
    turn=sum(abs(new_units[a]*prices[a]-old[a]) for a in ASSETS)
    paid=fee*turn
    new_cash=cash-sum((new_units[a]-units[a])*prices[a] for a in ASSETS)-paid
    new_nav=new_cash+sum(new_units[a]*prices[a] for a in ASSETS)
    if new_cash < -1e-8 or not math.isclose(new_nav,nav-paid,abs_tol=1e-9,rel_tol=1e-9):
        raise ValueError("ACCOUNTING_FAILURE")
    return max(0.,new_cash),new_units,turn,paid

def diagnostics(prices,fee):
    if len(prices["BTC"])!=N or len(prices["ETH"])!=N:
        raise ValueError("SOURCE_LENGTH")
    cash=1.
    units={a:0. for a in ASSETS}
    prev_nav=1.
    gross=0.;cost=0.;turnover=0.;events=0
    fold_gross=[0.]*5;fold_cost=[0.]*5
    asset_gross={a:0. for a in ASSETS}
    days=dict(total=0,raw_spread=0,trend_veto=0,vol_veto=0,
              vetoed_raw_spread=0,accepted=0,cash=0)
    exposed_hours={a:0 for a in ASSETS}
    maxdd=0.;high=1.
    for t in range(N):
        px={a:prices[a][t] for a in ASSETS}
        nav_before=cash+sum(units[a]*px[a] for a in ASSETS)
        hourly_gross=nav_before-prev_nav
        fold=next((i for i in range(5) if EDGES[i]<=START+t*HOUR<EDGES[i+1]),None)
        if fold is None:raise ValueError("OUTSIDE_TRAIN")
        gross+=hourly_gross;fold_gross[fold]+=hourly_gross
        if t:
            for a in ASSETS:
                asset_gross[a]+=units[a]*(prices[a][t]-prices[a][t-1])
        if t>=720 and t%24==0:
            days["total"]+=1
            target,_=signal(prices,t)
            b,e=prices["BTC"],prices["ETH"]
            rb=b[t-1]/b[t-73]-1;re=e[t-1]/e[t-73]-1
            raw=abs(rb-re)>=.08
            trend=b[t-1]/b[t-720]-1
            def vol(q):
                return statistics.pstdev(math.log(q[j]/q[j-1]) for j in range(t-72,t))*math.sqrt(24)
            veto_trend=trend<-.25
            veto_vol=max(vol(b),vol(e))>.08
            days["raw_spread"]+=int(raw)
            days["trend_veto"]+=int(veto_trend)
            days["vol_veto"]+=int(veto_vol)
            days["vetoed_raw_spread"]+=int(raw and (veto_trend or veto_vol))
            days["accepted"]+=int(target is not None)
            days["cash"]+=int(target is None)
            cash,units,turn,paid=rebalance(cash,units,px,target,fee)
            if turn>1e-10:events+=1
            turnover+=turn;cost+=paid;fold_cost[fold]+=paid
        if t==N-1 and any(units.values()):
            cash,units,turn,paid=rebalance(cash,units,px,None,fee)
            if turn>1e-10:events+=1
            turnover+=turn;cost+=paid;fold_cost[fold]+=paid
        for a in ASSETS:
            if units[a]>1e-12:exposed_hours[a]+=1
        nav=cash+sum(units[a]*px[a] for a in ASSETS)
        high=max(high,nav);maxdd=min(maxdd,nav/high-1)
        prev_nav=nav
    if not math.isclose(prev_nav-1,gross-cost,abs_tol=1e-9,rel_tol=1e-9):
        raise ValueError("GROSS_MINUS_COST_DOES_NOT_RECONCILE")
    if not math.isclose(gross,sum(asset_gross.values()),abs_tol=1e-9,rel_tol=1e-9):
        raise ValueError("ASSET_PNL_DOES_NOT_RECONCILE")
    if not math.isclose(gross,sum(fold_gross),abs_tol=1e-9):
        raise ValueError("FOLD_GROSS_DOES_NOT_RECONCILE")
    if not math.isclose(cost,sum(fold_cost),abs_tol=1e-9):
        raise ValueError("FOLD_COST_DOES_NOT_RECONCILE")
    return dict(roi=prev_nav-1,gross_dollar_pnl=gross,modeled_cost=cost,
                net_dollar_pnl=gross-cost,turnover=turnover,trades=events,
                max_drawdown=maxdd,fold_gross_dollar=fold_gross,fold_cost_dollar=fold_cost,
                asset_gross_dollar=asset_gross,decision_days=days,
                exposed_hours=exposed_hours,decision_count=days["total"])

def main(root,report_path,out):
    if not verify_report(root,report_path):raise ValueError("ORIGINAL_INDEPENDENT_ORACLE_FAILED")
    report=json.loads(Path(report_path).read_text())
    if report.get("status")!="S1_REJECTED_NO_RETUNE":raise ValueError("S1_NOT_REJECTED")
    prices=load(root)
    results={key:diagnostics(prices,fee) for key,fee in SCENARIOS.items()}
    for key in ("severe","supersevere"):
        observed=results[key];published=report[key]
        for a,b in (("roi","roi"),("modeled_cost","modeled_cost"),("trades","trades"),
                    ("turnover","turnover"),("max_drawdown","max_drawdown"),
                    ("decision_count","decision_count")):
            if not math.isclose(observed[a],published[b],abs_tol=1e-9,rel_tol=1e-9):
                raise ValueError("PUBLISHED_RESULT_MISMATCH_"+key+"_"+a)
    if results["severe"]["decision_days"]!=results["supersevere"]["decision_days"]:
        raise ValueError("SCENARIO_DECISIONS_DIFFER")
    payload={"schema":"V99_R106_S1_READ_ONLY_FAILURE_ATTRIBUTION_V1",
             "source_scope":"ORIGINAL_OKX_TRAIN_ONLY_THROUGH_2023_10_01_EXCLUSIVE",
             "model":"PERMANENTLY_REJECTED_S1_NO_RETUNE",
             "frictionless_is_diagnostic_not_candidate":True,
             "native_fills_or_fees_certified":False,"promotion_authorized":False,
             "validation_opened":False,"holdout_opened":False,"paper_or_frozen_changed":False,
             "scenarios":results}
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"S1_REJECTED_READ_ONLY_FAILURE_ATTRIBUTION_VERIFIED",
        "days":results["severe"]["decision_days"],
        "scenarios":{k:{"roi":v["roi"],"gross":v["gross_dollar_pnl"],
                        "cost":v["modeled_cost"],"trades":v["trades"],
                        "fold_gross":v["fold_gross_dollar"]} for k,v in results.items()},
        "NO_PROMOTION":True},sort_keys=True))

def selftest():
    p={"BTC":100.,"ETH":50.}
    for target in ("BTC","ETH",None):
        for fee in (0.,.0025,.006):
            cash,units,turn,paid=rebalance(1.,{"BTC":0.,"ETH":0.},p,target,fee)
            assert cash>=0 and all(u>=0 for u in units.values())
            assert math.isclose(cash+sum(units[a]*p[a] for a in ASSETS),1.-paid,abs_tol=1e-12)
    try:rebalance(1.,{"BTC":0.,"ETH":0.},{"BTC":0.,"ETH":50.},"BTC",.0025)
    except ValueError:pass
    else:raise AssertionError("bad price accepted")
    try:rebalance(-1.,{"BTC":0.,"ETH":0.},p,"BTC",.0025)
    except ValueError:pass
    else:raise AssertionError("bad cash accepted")
    print("S1_FORENSIC_SELFTEST_PASS")

if __name__=="__main__":
    if len(sys.argv)==2 and sys.argv[1]=="--selftest":selftest()
    elif len(sys.argv)==4:main(sys.argv[1],sys.argv[2],sys.argv[3])
    else:raise SystemExit("usage: python -m research.verification.v99_r106_s1_loss_attribution ROOT REPORT OUTPUT | --selftest")
