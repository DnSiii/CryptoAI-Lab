"""H1: preregistered DVOL forward-risk BTC/ETH spot/cash complete TRAIN, NO ORDERS."""
from __future__ import annotations
import hashlib
import json
import math
import sys
from pathlib import Path

from research.tools.v99_r106_d1_real_train_source_join import START,END,HOUR,HOURS,FOLD_EDGES
from research.tools.v99_r106_e1_spot_engine import (
    load_original_spot,rebalance,statistics_for,run as benchmark_run,
    COSTS,write_json,
)

WEEK = 7*24*HOUR
DAY = 24*HOUR
PREREG = "72e301a2f1ff6097188842c9f8bdc5aaa0cd47d9"
FLAGS = dict(native_fee_tier_authenticated=False,
             actual_account_fills_authenticated=False,
             realized_paper_pnl=False,validation_opened=False,
             holdout_opened=False,orders_enabled=False,
             promotion_authorized=False)


def load_original_dvol(root):
    root=Path(root)
    r=json.loads((root/"dvol_train_source.json").read_text())
    if r["schema"]!="V99_DERIBIT_FIRSTPARTY_DVOL_PIT_TRAIN_V1" or r["good_folds"]!=5:
        raise ValueError("UNVERIFIED_DVOL_SOURCE_GATE")
    if r["gate"]!="DVOL_SOURCE_READY_FOR_ONE_ENGINE_PREREG":
        raise ValueError("DVOL_NOT_READY")
    assert (r["start_ms"],r["end_exclusive_ms"])==(START,END)
    if any(r[k] for k in ("economic_train_executed","validation_opened",
                          "holdout_opened","orders_enabled","promotion_authorized")):
        raise ValueError("DVOL_SOURCE_CONTAMINATED")
    candles={}
    for row in r["source_rows"]:
        if row["status"]!="SOURCE_OK":
            raise ValueError("INCOMPLETE_DVOL_ORIGINAL_SOURCE")
        raw=(root/row["receipt_file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row["sha256"]:
            raise ValueError("DVOL_RECEIPT_HASH_MISMATCH")
        data=json.loads(raw)["result"]["data"]
        candles[(row["fold"],row["currency"])]={
            int(x[0]):float(x[4]) for x in data
            if row["query_start_ms"]<=int(x[0])<=row["query_end_ms"]}
    weekly={}
    for row in r["weekly"]:
        t,f,c=row["decision_ms"],row["fold"],row["currency"]
        if not (START<t<END and FOLD_EDGES[f-1]<=t<FOLD_EDGES[f]):
            raise ValueError("DVOL_OUTSIDE_TRAIN")
        if not row["eligible"]:
            raise ValueError("MISSING_DVOL_WEEK")
        stamp=row["candle_start_ms"]
        if not (stamp+DAY<t and t-stamp-DAY<=2*DAY):
            raise ValueError("DVOL_LOOKAHEAD")
        if candles[(f,c)].get(stamp)!=row["dvol_close"]:
            raise ValueError("DVOL_ORIGINAL_MISMATCH")
        weekly[(t,c)]=float(row["dvol_close"])
    if len(weekly)!=188:
        raise ValueError("NOT_94_X_2_DVOL_WEEKS")
    return weekly


def target_for(t,weekly):
    b=weekly.get((t,"BTC"));e=weekly.get((t,"ETH"))
    pb=weekly.get((t-WEEK,"BTC"));pe=weekly.get((t-WEEK,"ETH"))
    if any(v is None or not math.isfinite(v) or v<=0 for v in (b,e,pb,pe)):
        return (0.0,0.0),"MISSING_PREVIOUS_WEEK"
    if b/pb>1.20 or e/pe>1.20:
        return (0.0,0.0),"WEEKLY_IMPLIED_VOL_SHOCK"
    if b>=90 or e>=110:
        return (0.0,0.0),"ABSOLUTE_IMPLIED_VOL_STRESS"
    wb=min(0.65,0.35*(60.0/b)**2)
    we=min(0.35,0.20*(75.0/e)**2)
    if wb+we>0.90:
        scale=0.90/(wb+we)
        wb*=scale;we*=scale
    assert 0<=wb<=0.65 and 0<=we<=0.35 and wb+we<=0.900000001
    return (wb,we),"DVOL_FORWARD_RISK_BUDGET"


def execute(prices,weekly,fee,slip):
    cash=1.0
    qty=[0.0,0.0]
    journal=[]
    last_weights=(0.0,0.0)
    last_reason="CASH_BEFORE_FIRST_WEEK"
    for i in range(HOURS):
        t=START+i*HOUR
        px=(prices[0][i],prices[1][i])
        decision=(t,"BTC") in weekly
        turnover=fee_paid=slip_paid=0.0
        if decision:
            last_weights,last_reason=target_for(t,weekly)
            cash,qty,turnover,fee_paid,slip_paid=rebalance(
                cash,qty,px,last_weights,fee,slip)
        nav=cash+qty[0]*px[0]+qty[1]*px[1]
        if not math.isfinite(nav) or nav<=0 or cash<0 or min(qty)<0:
            raise ValueError("INVALID_SELF_FINANCING_NAV")
        journal.append(dict(hour_ms=t,btc_open=px[0],eth_open=px[1],
                            btc_qty=qty[0],eth_qty=qty[1],cash=cash,nav=nav,
                            turnover=turnover,fee_paid=fee_paid,slippage_paid=slip_paid,
                            rebalanced=decision,target_btc=last_weights[0],
                            target_eth=last_weights[1],decision_reason=last_reason))
    assert len(journal)==HOURS
    return journal


def main(spot_root,dvol_root,out_dir):
    prices=load_original_spot(spot_root)
    weekly=load_original_dvol(dvol_root)
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    results={}
    for name,(fee,slip) in COSTS.items():
        journal=execute(prices,weekly,fee,slip)
        path=out/f"h1_{name}_hourly.jsonl"
        with path.open("w") as handle:
            for row in journal:
                handle.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
        results[name]=dict(metrics=statistics_for(journal,prices),
                           journal_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                           fee_per_side=fee,slippage_per_side=slip,
                           cash_veto_weeks=sum(row["rebalanced"] and
                                               row["target_btc"]==0 and row["target_eth"]==0
                                               for row in journal))
    bench={}
    for label,weights in (("btc_only",(1.0,0.0)),("eth_only",(0.0,1.0)),
                          ("buy_once_45_45_10",(0.45,0.45))):
        bench[label]={}
        for scenario in ("severe","supersevere"):
            fee,slip=COSTS[scenario]
            bench[label][scenario]=statistics_for(
                benchmark_run(prices,weights,fee,slip,False),prices)["roi"]
    bench["cash"]={"severe":0.0,"supersevere":0.0}
    s=results["severe"]["metrics"];u=results["supersevere"]["metrics"]
    gates={
        "severe_positive":s["roi"]>0,
        "supersevere_positive":u["roi"]>0,
        "severe_4_of_5_folds":s["positive_folds"]>=4,
        "supersevere_3_of_5_folds":u["positive_folds"]>=3,
        "both_maxdd_above_minus35pct":min(s["max_drawdown"],u["max_drawdown"])>=-0.35,
        "both_daily_pf_above_one":all(x["daily_profit_factor"] is not None and
                                      x["daily_profit_factor"]>1 for x in (s,u)),
        "both_remove_best_day_positive":min(s["remove_best_day_roi"],u["remove_best_day_roi"])>0,
        "both_worst_day_above_minus15pct":min(s["worst_daily_return"],u["worst_daily_return"])>=-0.15,
        "both_worst_week_above_minus25pct":min(s["worst_week_return"],u["worst_week_return"])>=-0.25,
        "both_top5_gains_concentration_at_most_60pct":all(
            x["top5_positive_days_share_of_gains"] is not None and
            x["top5_positive_days_share_of_gains"]<=0.60 for x in (s,u)),
        "supersevere_beats_buy_once_by_2pp":
            u["roi"]-bench["buy_once_45_45_10"]["supersevere"]>=0.02,
        "all_six_regimes_observed":all(all(v["hours"]>0 for v in
                                        x["regimes_3x2"].values()) for x in (s,u)),
    }
    status=("PROVISIONAL_TRAIN_PASS_PENDING_INDEPENDENT_AND_NATIVE_PROVENANCE"
            if all(gates.values()) else "PERMANENT_TRAIN_REJECT_NO_RETUNE")
    report=dict(schema="H1_PREREG_DVOL_FORWARD_RISK_SPOT_TRAIN_V1",
                status=status,start_ms=START,end_exclusive_ms=END,hours=HOURS,
                preregistration_commit=PREREG,source_okx_run=40019588739,
                source_dvol_run=40072202459,source_original=True,
                model_only=True,independent_oracle_complete=False,
                results=results,benchmarks=bench,gates=gates,**FLAGS)
    write_json(out/"h1_train_report.json",report)
    print(json.dumps(dict(status=status,severe_roi=s["roi"],
                          supersevere_roi=u["roi"],
                          severe_positive_folds=s["positive_folds"],
                          supersevere_positive_folds=u["positive_folds"],
                          severe_maxdd=s["max_drawdown"],supersevere_maxdd=u["max_drawdown"],
                          cash_veto_weeks=results["severe"]["cash_veto_weeks"],
                          failed_gates=[k for k,v in gates.items() if not v],
                          no_promotion=True),sort_keys=True))
    return report

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: python -m research.tools.v99_r106_h1_dvol_spot_engine OKX_ROOT DVOL_ROOT OUTPUT_DIR")
    main(*sys.argv[1:])
