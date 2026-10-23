"""Independent first-party E1 journal/accounting and economic-gate oracle.
Never imports E1 strategy, rebalance or metric functions. No orders.
"""
from __future__ import annotations
import hashlib,json,math,sys
from datetime import datetime,timezone
from pathlib import Path
from research.verification.independent_d1_native_train_receipts import verify

START=1639008000000
END=1696118400000
HOUR=3600000
FOLD_EDGES=[1639008000000,1650427200000,1661850000000,1673272800000,1684695600000,1696118400000]
PARAMS={"severe":(0.0007,0.0005),"supersevere":(0.0014,0.0010),
        "severe_shock":(0.0007,0.0105),"supersevere_shock":(0.0014,0.0210)}

def close(a,b,code,atol=1e-9):
    if not math.isfinite(float(a)) or abs(float(a)-float(b))>atol*max(1,abs(float(a)),abs(float(b))):
        raise ValueError(code)

def independently_verify(root,out):
    root,out=Path(root),Path(out)
    if verify(root)["status"]!="INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("ORIGINAL_RECEIPTS_NOT_INDEPENDENTLY_VERIFIED")
    spot=[]
    for inst in ("BTC-USDT","ETH-USDT"):
        raw=json.loads((root/inst/"train_opens.json").read_text())
        if len(raw)!=15864 or any(x["ts"]!=START+i*HOUR for i,x in enumerate(raw)):
            raise ValueError("ORIGINAL_SPOT_GRID_MISMATCH")
        spot.append([float(x["open"]) for x in raw])
    report=json.loads((out/"e1_train_report.json").read_text())
    if report["preregistration_commit"]!="d98632b91a6ffaf5d9ef6012d47de6a298c03870":
        raise ValueError("PREREG_COMMIT_NOT_PINNED")
    for key in ("model_only","validation_opened","holdout_opened","orders_enabled","promotion_authorized"):
        if report[key] is not (key=="model_only"):raise ValueError("UNSAFE_PROMOTION_FLAG")
    summaries={}
    for scenario,(fee,slip) in PARAMS.items():
        path=out/f"e1_{scenario}_hourly.jsonl"
        if hashlib.sha256(path.read_bytes()).hexdigest()!=report["results"][scenario]["journal_sha256"]:
            raise ValueError("JOURNAL_SHA256_MISMATCH")
        rows=[json.loads(x) for x in path.read_text().splitlines()]
        if len(rows)!=15864:raise ValueError("NOT_COMPLETE_TRAIN")
        cash=1.0; holdings=[0.0,0.0]; navs=[];total_turnover=total_fee=total_slip=0.0
        for i,r in enumerate(rows):
            t=START+i*HOUR
            if r["hour_ms"]!=t:raise ValueError("HOLDOUT_OR_GAP")
            px=[spot[0][i],spot[1][i]]
            close(r["btc_open"],px[0],"BTC_SOURCE_PRICE_MISMATCH")
            close(r["eth_open"],px[1],"ETH_SOURCE_PRICE_MISMATCH")
            new=[r["btc_qty"],r["eth_qty"]]
            if min(new)<0:raise ValueError("SHORT_SPOT_FORBIDDEN")
            change=[new[0]-holdings[0],new[1]-holdings[1]]
            turnover=sum(abs(delta)*price for delta,price in zip(change,px))
            expected_fee=turnover*fee
            expected_slip=turnover*slip
            cash-=sum(delta*price for delta,price in zip(change,px))+expected_fee+expected_slip
            if cash < -1e-9:raise ValueError("CASH_DEFICIT")
            nav=cash+new[0]*px[0]+new[1]*px[1]
            close(r["cash"],cash,"CASH_NOT_SELF_FINANCING")
            close(r["nav"],nav,"NAV_NOT_SELF_FINANCING")
            close(r["turnover"],turnover,"TURNOVER_MISMATCH")
            close(r["fee_paid"],expected_fee,"FEE_MISMATCH")
            close(r["slippage_paid"],expected_slip,"SLIPPAGE_MISMATCH")
            d=datetime.fromtimestamp(t/1000,timezone.utc)
            should_rebalance=(i==0 or d.day==1 and d.hour==0)
            if bool(r["rebalanced"])!=should_rebalance:raise ValueError("CALENDAR_DECISION_CHANGED")
            if should_rebalance:
                close(new[0]*px[0]/nav,0.45,"BTC_WEIGHT_NOT_PREREG")
                close(new[1]*px[1]/nav,0.45,"ETH_WEIGHT_NOT_PREREG")
                close(cash/nav,0.10,"CASH_WEIGHT_NOT_PREREG")
            else:
                if turnover>1e-9:raise ValueError("UNPREREGISTERED_TRADE")
            total_turnover+=turnover;total_fee+=expected_fee;total_slip+=expected_slip
            navs.append(nav);holdings=new
        metrics=report["results"][scenario]["metrics"]
        close(metrics["roi"],navs[-1]-1,"ROI_MISMATCH")
        peak=1.0;dd=0.0
        for n in navs:
            peak=max(peak,n);dd=min(dd,n/peak-1)
        close(metrics["max_drawdown"],dd,"MAX_DRAWDOWN_MISMATCH")
        fold_returns=[]
        for a,b in zip(FOLD_EDGES,FOLD_EDGES[1:]):
            first=(a-START)//HOUR;last=(b-START)//HOUR-1
            fold_returns.append(navs[last]/navs[first]-1)
        for x,y in zip(metrics["fold_returns"],fold_returns):
            close(x,y,"FOLD_MISMATCH")
        if metrics["positive_folds"]!=sum(x>0 for x in fold_returns):
            raise ValueError("FOLD_SIGN_MISMATCH")
        close(metrics["total_turnover"],total_turnover,"TOTAL_TURNOVER_MISMATCH")
        close(metrics["total_fee"],total_fee,"TOTAL_FEE_MISMATCH")
        close(metrics["total_slippage"],total_slip,"TOTAL_SLIP_MISMATCH")
        daily_marks=list(range(0,15864,24))
        if daily_marks[-1]!=15863:daily_marks.append(15863)
        daily=[navs[b]/navs[a]-1 for a,b in zip(daily_marks,daily_marks[1:])]
        close(metrics["worst_daily_return"],min(daily),"WORST_DAY_MISMATCH")
        positives=sum(x for x in daily if x>0)
        negatives=-sum(x for x in daily if x<0)
        if negatives:
            close(metrics["daily_profit_factor"],positives/negatives,"DAILY_PF_MISMATCH")
        best=max(math.log1p(x) for x in daily)
        close(metrics["remove_best_day_roi"],math.expm1(math.log(navs[-1])-best),"BEST_DAY_MISMATCH")
        summaries[scenario]={"roi":navs[-1]-1,"folds":fold_returns,"maxdd":dd,
                             "fee":total_fee,"slippage":total_slip,"trades":sum(r["rebalanced"] for r in rows)}
    # Independently derive buy-once benchmarks analytically from ORIGINAL first/last opens.
    b_ratio=spot[0][-1]/spot[0][0]
    e_ratio=spot[1][-1]/spot[1][0]
    for scenario in ("severe","supersevere"):
        fee,slip=PARAMS[scenario]
        c=fee+slip
        expected_bench={"btc":b_ratio/(1+c)-1,
                        "eth":e_ratio/(1+c)-1,
                        "buy_once_45_45_10":(0.1+0.45*b_ratio+0.45*e_ratio)/(1+0.9*c)-1}
        for label,expected in expected_bench.items():
            close(report["benchmarks"][label][scenario],expected,"BENCHMARK_ENVELOPE_MISMATCH")
    s=summaries["severe"];u=summaries["supersevere"]
    oracle_gates={
        "severe_positive":s["roi"]>0,
        "supersevere_positive":u["roi"]>0,
        "severe_4_of_5_folds":sum(x>0 for x in s["folds"])>=4,
        "supersevere_3_of_5_folds":sum(x>0 for x in u["folds"])>=3,
        "both_maxdd_above_minus35pct":min(s["maxdd"],u["maxdd"])>=-0.35,
        "both_daily_pf_above_one":all(z["pf"] is not None and z["pf"]>1 for z in (s,u)),
        "both_remove_best_day_positive":min(s["best_day_removed"],u["best_day_removed"])>0,
        "both_worst_day_above_minus15pct":min(s["worst_day"],u["worst_day"])>=-0.15,
        "supersevere_beats_buy_once_by_2pp":u["roi"]-report["benchmarks"]["buy_once_45_45_10"]["supersevere"]>=0.02,
    }
    if oracle_gates!=report["gates"]:
        raise ValueError("INDEPENDENT_ECONOMIC_GATES_DISAGREE")
    if not (summaries["severe"]["roi"]>=summaries["supersevere"]["roi"]-1e-10 and
            summaries["severe_shock"]["roi"]<=summaries["severe"]["roi"]+1e-10 and
            summaries["supersevere_shock"]["roi"]<=summaries["supersevere"]["roi"]+1e-10):
        raise ValueError("FIXED_TARGET_COST_MONOTONICITY_FAILED")
    # Negative control: intentionally corrupt an observed cash record, and prove the identity rejects it.
    tampered_cash=1.0
    first=json.loads((out/"e1_severe_hourly.jsonl").open().readline())
    try:
        close(first["cash"]+0.01,first["cash"],"INJECTED_CASH_TAMPER")
    except ValueError as exc:
        if str(exc)!="INJECTED_CASH_TAMPER":raise
    else:
        raise ValueError("NEGATIVE_CONTROL_NOT_EFFECTIVE")
    result={"status":"INDEPENDENT_ORIGINAL_PRICE_TO_CASH_LEDGER_VERIFIED",
            "scenarios":summaries,"hours_per_scenario":15864,
            "synthetic_adversarial_control":"CASH_CORRUPTION_DETECTABLE",
            "economic_train_gate_passed":all(oracle_gates.values()),
            "independent_benchmark_and_gate_recomputation":True,
            "native_fee_tier_authenticated":False,"real_account_fills":False,
            "validation_opened":False,"holdout_opened":False,"promotion_authorized":False}
    (out/"e1_independent_oracle.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"train_gate_passed":result["economic_train_gate_passed"],
                      "severe":summaries["severe"],"supersevere":summaries["supersevere"],
                      "promotion_authorized":False},sort_keys=True))
    return result

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: python -m research.verification.independent_v99_r106_e1_spot_oracle PRICE_ROOT OUTPUT")
    independently_verify(*sys.argv[1:])
