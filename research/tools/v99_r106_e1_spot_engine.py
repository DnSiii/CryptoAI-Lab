"""E1 fixed, spot-only, preregistered TRAIN engine. Modeled economics, NO ORDERS."""
from __future__ import annotations
import hashlib, json, math, statistics, sys
from datetime import datetime, timezone
from pathlib import Path
from research.verification.independent_d1_native_train_receipts import verify
from research.tools.v99_r106_d1_real_train_source_join import START, END, HOUR, HOURS, FOLD_EDGES, strict_json

WEIGHTS = (0.45, 0.45)
COSTS = {"severe":(0.0007,0.0005), "supersevere":(0.0014,0.0010),
         "severe_shock":(0.0007,0.0105), "supersevere_shock":(0.0014,0.0210)}
FLAGS = {"native_fee_tier_authenticated":False,"actual_account_fills_authenticated":False,
         "realized_paper_pnl":False,"validation_opened":False,"holdout_opened":False,
         "orders_enabled":False,"promotion_authorized":False}

def load_original_spot(root):
    root=Path(root)
    if verify(root)["status"] != "INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("FIRST_PARTY_SOURCE_ORACLE_FAILED")
    result=[]
    for asset in ("BTC-USDT","ETH-USDT"):
        raw=strict_json(root/asset/"train_opens.json")
        if len(raw)!=HOURS or [r["ts"] for r in raw]!=list(range(START,END,HOUR)):
            raise ValueError("INVALID_TRAIN_ONLY_HOURLY_GRID")
        prices=[float(r["open"]) for r in raw]
        if not all(math.isfinite(x) and x>0 for x in prices):
            raise ValueError("BAD_ORIGINAL_SPOT_PRICE")
        result.append(prices)
    return result

def targets_at(ts):
    d=datetime.fromtimestamp(ts/1000,timezone.utc)
    return ts==START or (d.day==1 and d.hour==0)

def rebalance(cash,qty,prices,weights,fee,slip):
    pre=cash+sum(q*p for q,p in zip(qty,prices))
    c=fee+slip
    # Independent of trade direction, solve the exact post-cost target equity.
    def residual(e):
        return e+c*sum(abs(w*e-q*p) for w,q,p in zip(weights,qty,prices))-pre
    low,high=0.0,pre
    for _ in range(70):
        mid=(low+high)/2
        if residual(mid)>0: high=mid
        else: low=mid
    e=(low+high)/2
    target=[w*e/p for w,p in zip(weights,prices)]
    turnover=sum(abs((n-o)*p) for n,o,p in zip(target,qty,prices))
    fee_paid=fee*turnover
    slip_paid=slip*turnover
    new_cash=cash-sum((n-o)*p for n,o,p in zip(target,qty,prices))-fee_paid-slip_paid
    if new_cash < -1e-10 or abs(new_cash+sum(n*p for n,p in zip(target,prices))-e)>1e-9:
        raise ValueError("NOT_SELF_FINANCING")
    return max(new_cash,0.0),target,turnover,fee_paid,slip_paid

def run(prices,weights,fee,slip,monthly):
    cash=1.0
    qty=[0.0,0.0]
    journal=[]
    for i in range(HOURS):
        t=START+i*HOUR
        px=[prices[0][i],prices[1][i]]
        do=(i==0 or (monthly and targets_at(t)))
        turnover=fee_paid=slip_paid=0.0
        if do:
            cash,qty,turnover,fee_paid,slip_paid=rebalance(cash,qty,px,weights,fee,slip)
        nav=cash+sum(q*p for q,p in zip(qty,px))
        if not math.isfinite(nav) or nav<=0 or cash<0 or min(qty)<0:
            raise ValueError("INVALID_NAV_OR_SHORT")
        journal.append({"hour_ms":t,"btc_open":px[0],"eth_open":px[1],
                        "btc_qty":qty[0],"eth_qty":qty[1],"cash":cash,"nav":nav,
                        "turnover":turnover,"fee_paid":fee_paid,"slippage_paid":slip_paid,
                        "rebalanced":do})
    return journal

def statistics_for(journal,prices):
    nav=[r["nav"] for r in journal]
    total=nav[-1]-1.0
    max_seen=1.0
    maxdd=0.0
    for v in nav:
        max_seen=max(max_seen,v)
        maxdd=min(maxdd,v/max_seen-1)
    # End-of-TRAIN partial UTC day is retained as a final marked interval.
    indices=list(range(0,HOURS,24))
    if indices[-1]!=HOURS-1: indices.append(HOURS-1)
    daily=[math.log(nav[b]/nav[a]) for a,b in zip(indices,indices[1:])]
    daily_simple=[math.expm1(x) for x in daily]
    gains=sum(x for x in daily_simple if x>0)
    losses=-sum(x for x in daily_simple if x<0)
    folds=[]
    for a,b in zip(FOLD_EDGES,FOLD_EDGES[1:]):
        first=(a-START)//HOUR
        last=(b-START)//HOUR-1
        if not (0<=first<=last<HOURS):raise ValueError("BAD_PREREG_FOLD")
        folds.append(nav[last]/nav[first]-1)
    top5=sum(sorted([max(x,0) for x in daily_simple],reverse=True)[:5])
    weekly=[nav[min(HOURS-1,i+168)]/nav[i]-1 for i in range(0,HOURS-1,168)]
    # t-1-only 3x2 BTC regime: 30d BTC change with +/-2% neutral band,
    # 7d hourly realized vol vs median of previous 168 lagged 7d vols.
    hourly_btc=[0.0]+[math.log(prices[0][i]/prices[0][i-1]) for i in range(1,HOURS)]
    vol=[None]*HOURS
    for i in range(168,HOURS):
        vol[i]=statistics.pstdev(hourly_btc[i-167:i+1])
    regimes={f"{s}_{v}":{"hours":0,"sum_log_nav":0.0} for s in ("down","flat","up") for v in ("low","high")}
    for i in range(889,HOURS):
        r30=prices[0][i-1]/prices[0][i-721]-1
        trend="up" if r30>0.02 else ("down" if r30< -0.02 else "flat")
        prev_vols=vol[i-168:i]
        if any(v is None for v in prev_vols): continue
        bucket="high" if vol[i-1]>statistics.median(prev_vols) else "low"
        z=regimes[f"{trend}_{bucket}"]
        z["hours"]+=1
        z["sum_log_nav"]+=math.log(nav[i]/nav[i-1])
    for z in regimes.values():
        z["compounded_return"]=math.expm1(z.pop("sum_log_nav"))
    return {"roi":total,"max_drawdown":maxdd,"fold_returns":folds,
            "positive_folds":sum(x>0 for x in folds),
            "daily_profit_factor":(gains/losses if losses else None),
            "remove_best_day_roi":math.expm1(math.log(nav[-1])-max(daily)),
            "worst_daily_return":min(daily_simple),"worst_week_return":min(weekly),
            "top5_positive_days_share_of_gains":(top5/gains if gains else None),
            "total_fee":sum(r["fee_paid"] for r in journal),
            "total_slippage":sum(r["slippage_paid"] for r in journal),
            "total_turnover":sum(r["turnover"] for r in journal),
            "rebalance_hours":sum(r["rebalanced"] for r in journal),
            "regimes_3x2":regimes}

def write_json(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n")

def main(price_root,out):
    prices=load_original_spot(price_root)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    results={}
    for name,(fee,slip) in COSTS.items():
        j=run(prices,WEIGHTS,fee,slip,True)
        path=out/f"e1_{name}_hourly.jsonl"
        with path.open("w") as f:
            for row in j:f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
        results[name]={"metrics":statistics_for(j,prices),
                       "journal_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                       "fee_per_side":fee,"slippage_per_side":slip}
    bench={}
    for label,weights in (("btc",(1.0,0.0)),("eth",(0.0,1.0)),("buy_once_45_45_10",WEIGHTS)):
        bench[label]={}
        for scenario in ("severe","supersevere"):
            f,s=COSTS[scenario]
            bench[label][scenario]=statistics_for(run(prices,weights,f,s,False),prices)["roi"]
    s=results["severe"]["metrics"];u=results["supersevere"]["metrics"]
    gates={
        "severe_positive":s["roi"]>0,
        "supersevere_positive":u["roi"]>0,
        "severe_4_of_5_folds":s["positive_folds"]>=4,
        "supersevere_3_of_5_folds":u["positive_folds"]>=3,
        "both_maxdd_above_minus35pct":min(s["max_drawdown"],u["max_drawdown"])>=-0.35,
        "both_daily_pf_above_one":all(z["daily_profit_factor"] is not None and z["daily_profit_factor"]>1 for z in (s,u)),
        "both_remove_best_day_positive":min(s["remove_best_day_roi"],u["remove_best_day_roi"])>0,
        "both_worst_day_above_minus15pct":min(s["worst_daily_return"],u["worst_daily_return"])>=-0.15,
        "supersevere_beats_buy_once_by_2pp":u["roi"]-bench["buy_once_45_45_10"]["supersevere"]>=0.02,
    }
    report={"schema":"E1_PREREGISTERED_SPOT_ONLY_TRAIN_ECONOMICS_V1",
            "status":"PERMANENT_TRAIN_REJECT_NO_RETUNE" if not all(gates.values()) else "PROVISIONAL_TRAIN_PASS_PENDING_NATIVE_PROVENANCE_AND_INDEPENDENT_ORACLE",
            "start_ms":START,"end_exclusive_ms":END,"hours":HOURS,
            "preregistration_commit":"d98632b91a6ffaf5d9ef6012d47de6a298c03870",
            "results":results,"benchmarks":bench,"gates":gates,
            "source":"ORIGINAL_OKX_HTTP_TRAIN_ONLY_NOT_ACCOUNT_FILLS",
            "model_only":True,"independent_oracle_complete":False,**FLAGS}
    write_json(out/"e1_train_report.json",report)
    print(json.dumps({"status":report["status"],"severe_roi":s["roi"],
        "supersevere_roi":u["roi"],"severe_folds":s["fold_returns"],
        "supersevere_folds":u["fold_returns"],"failed_gates":[k for k,v in gates.items() if not v],
        "native_provenance":False,"promotion":False},sort_keys=True))
    return report

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: python -m research.tools.v99_r106_e1_spot_engine PRICE_ROOT OUTPUT_DIR")
    main(*sys.argv[1:])
