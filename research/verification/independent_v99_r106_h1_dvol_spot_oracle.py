"""Independent H1 original DVOL -> target -> OKX spot cash ledger oracle. NO ORDERS.

No import of H1 strategy, H1 rebalance or E1 accounting/metric functions.
"""
from __future__ import annotations
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path
from research.verification.independent_d1_native_train_receipts import verify

START=1639008000000
END=1696118400000
HOUR=3600000
DAY=24*HOUR
WEEK=7*DAY
HOURS=15864
EDGES=[1639008000000,1650427200000,1661850000000,1673272800000,1684695600000,1696118400000]
COSTS={"severe":(0.0007,0.0005),"supersevere":(0.0014,0.0010),
       "severe_shock":(0.0007,0.0105),"supersevere_shock":(0.0014,0.0210)}

def close(a,b,code,tol=1e-9):
    if not math.isfinite(float(a)) or abs(float(a)-float(b))>tol*max(1,abs(float(a)),abs(float(b))):
        raise ValueError(code)


def original_dvol(dvol_root):
    p=Path(dvol_root)
    r=json.loads((p/"dvol_train_source.json").read_text())
    assert r["schema"]=="V99_DERIBIT_FIRSTPARTY_DVOL_PIT_TRAIN_V1"
    assert r["good_folds"]==5 and r["gate"]=="DVOL_SOURCE_READY_FOR_ONE_ENGINE_PREREG"
    assert (r["start_ms"],r["end_exclusive_ms"])==(START,END)
    assert r["fold_edges"]==EDGES
    assert all(not r[k] for k in ("economic_train_executed","validation_opened",
                                   "holdout_opened","orders_enabled","promotion_authorized"))
    raw={}
    for src in r["source_rows"]:
        assert src["status"]=="SOURCE_OK"
        blob=(p/src["receipt_file"]).read_bytes()
        assert hashlib.sha256(blob).hexdigest()==src["sha256"]
        data=json.loads(blob)
        assert not data.get("error")
        assert data["result"].get("continuation") is None
        candle={}
        for item in data["result"]["data"]:
            t=int(item[0])
            assert START<=t<END
            if not src["query_start_ms"]<=t<=src["query_end_ms"]:
                continue
            v=[float(x) for x in item[1:5]]
            assert all(math.isfinite(x) and x>0 for x in v)
            assert v[1]>=max(v[0],v[2],v[3]) and v[2]<=min(v[0],v[1],v[3])
            assert t not in candle
            candle[t]=v[3]
        assert len(candle)==src["candles"]
        raw[(src["fold"],src["currency"])]=candle
    weekly={}
    assert len(r["weekly"])==188
    for row in r["weekly"]:
        t,f,c=row["decision_ms"],row["fold"],row["currency"]
        assert START<t<END and EDGES[f-1]<=t<EDGES[f]
        options=[(stamp,value) for stamp,value in raw[(f,c)].items()
                 if stamp+DAY<t and t-stamp-DAY<=2*DAY]
        latest=max(options,default=None)
        assert latest is not None and row["eligible"]
        assert latest==(row["candle_start_ms"],row["dvol_close"])
        assert row["age_after_close_ms"]==t-latest[0]-DAY
        weekly[(t,c)]=latest[1]
    assert len(weekly)==188
    return weekly


def independent_targets(t,weekly):
    now_b=weekly.get((t,"BTC"));now_e=weekly.get((t,"ETH"))
    prev_b=weekly.get((t-WEEK,"BTC"));prev_e=weekly.get((t-WEEK,"ETH"))
    if any(v is None or v<=0 or not math.isfinite(v)
           for v in (now_b,now_e,prev_b,prev_e)):
        return 0.0,0.0
    if now_b>1.2*prev_b or now_e>1.2*prev_e:
        return 0.0,0.0
    if now_b>=90 or now_e>=110:
        return 0.0,0.0
    b=min(0.65,0.35*(60/now_b)**2)
    e=min(0.35,0.20*(75/now_e)**2)
    if b+e>0.90:
        k=0.90/(b+e);b*=k;e*=k
    return b,e


def independent_regime_hours(prices):
    ret=[0.0]+[math.log(prices[0][i]/prices[0][i-1]) for i in range(1,HOURS)]
    vols=[None]*HOURS
    for i in range(168,HOURS):
        vols[i]=statistics.pstdev(ret[i-167:i+1])
    buckets={f"{s}_{v}":0 for s in ("down","flat","up") for v in ("low","high")}
    for i in range(889,HOURS):
        move=prices[0][i-1]/prices[0][i-721]-1
        trend="up" if move>0.02 else ("down" if move< -0.02 else "flat")
        recent=vols[i-168:i]
        if any(x is None for x in recent):
            continue
        regime="high" if vols[i-1]>statistics.median(recent) else "low"
        buckets[trend+"_"+regime]+=1
    return buckets


def verify_h1(okx_root,dvol_root,out_dir):
    root,out=Path(okx_root),Path(out_dir)
    if verify(root)["status"]!="INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("ORIGINAL_OKX_SOURCE_INVALID")
    spot=[]
    for name in ("BTC-USDT","ETH-USDT"):
        rows=json.loads((root/name/"train_opens.json").read_text())
        assert len(rows)==HOURS
        assert all(x["ts"]==START+i*HOUR for i,x in enumerate(rows))
        spot.append([float(x["open"]) for x in rows])
    weekly=original_dvol(dvol_root)
    report=json.loads((out/"h1_train_report.json").read_text())
    assert report["schema"]=="H1_PREREG_DVOL_FORWARD_RISK_SPOT_TRAIN_V1"
    assert report["preregistration_commit"]=="72e301a2f1ff6097188842c9f8bdc5aaa0cd47d9"
    assert report["source_dvol_run"]==40072202459
    assert report["model_only"] and not any(report[k] for k in
           ("validation_opened","holdout_opened","orders_enabled","promotion_authorized"))
    regimes=independent_regime_hours(spot)
    summaries={}
    for scenario,(fee,slip) in COSTS.items():
        path=out/f"h1_{scenario}_hourly.jsonl"
        assert hashlib.sha256(path.read_bytes()).hexdigest()==report["results"][scenario]["journal_sha256"]
        rows=[json.loads(x) for x in path.read_text().splitlines()]
        assert len(rows)==HOURS
        cash=1.0
        holdings=[0.0,0.0]
        navs=[]
        tot_turn=tot_fee=tot_slip=0.0
        decision_count=veto_count=0
        for i,row in enumerate(rows):
            t=START+i*HOUR
            if row["hour_ms"]!=t:
                raise ValueError("H1_HOURLY_GRID_OR_HOLDOUT")
            px=(spot[0][i],spot[1][i])
            close(row["btc_open"],px[0],"ORIGINAL_BTC_OPEN_MISMATCH")
            close(row["eth_open"],px[1],"ORIGINAL_ETH_OPEN_MISMATCH")
            new=[row["btc_qty"],row["eth_qty"]]
            if min(new)<0:raise ValueError("H1_SPOT_SHORT_FORBIDDEN")
            change=[new[j]-holdings[j] for j in range(2)]
            turnover=sum(abs(change[j])*px[j] for j in range(2))
            charge=turnover*fee
            friction=turnover*slip
            cash-=sum(change[j]*px[j] for j in range(2))+charge+friction
            if cash< -1e-9:raise ValueError("H1_NEGATIVE_CASH")
            nav=cash+sum(new[j]*px[j] for j in range(2))
            close(row["cash"],cash,"H1_CASH_LEDGER_BROKEN")
            close(row["nav"],nav,"H1_NAV_LEDGER_BROKEN")
            close(row["turnover"],turnover,"H1_TURNOVER_BROKEN")
            close(row["fee_paid"],charge,"H1_FEES_BROKEN")
            close(row["slippage_paid"],friction,"H1_SLIPPAGE_BROKEN")
            decision=(t,"BTC") in weekly
            assert bool(row["rebalanced"])==decision
            if decision:
                decision_count+=1
                wb,we=independent_targets(t,weekly)
                close(new[0]*px[0]/nav,wb,"H1_BTC_TARGET_BROKEN")
                close(new[1]*px[1]/nav,we,"H1_ETH_TARGET_BROKEN")
                close(cash/nav,1-wb-we,"H1_CASH_TARGET_BROKEN")
                close(row["target_btc"],wb,"H1_TARGET_METADATA_BTC")
                close(row["target_eth"],we,"H1_TARGET_METADATA_ETH")
                veto_count+=int(wb==0 and we==0)
            elif turnover>1e-9:
                raise ValueError("H1_UNSCHEDULED_TRADE")
            navs.append(nav)
            tot_turn+=turnover;tot_fee+=charge;tot_slip+=friction
            holdings=new
        assert decision_count==94
        assert veto_count==report["results"][scenario]["cash_veto_weeks"]
        metrics=report["results"][scenario]["metrics"]
        roi=navs[-1]-1
        close(metrics["roi"],roi,"H1_ROI_MISMATCH")
        peak=1.0;dd=0.0
        for n in navs:
            peak=max(peak,n);dd=min(dd,n/peak-1)
        close(metrics["max_drawdown"],dd,"H1_DD_MISMATCH")
        fold_returns=[]
        for a,b in zip(EDGES,EDGES[1:]):
            first=(a-START)//HOUR
            last=(b-START)//HOUR-1
            fold_returns.append(navs[last]/navs[first]-1)
        assert len(metrics["fold_returns"])==5
        for x,y in zip(metrics["fold_returns"],fold_returns):
            close(x,y,"H1_FOLD_MISMATCH")
        assert metrics["positive_folds"]==sum(x>0 for x in fold_returns)
        close(metrics["total_turnover"],tot_turn,"H1_TOTAL_TURNOVER")
        close(metrics["total_fee"],tot_fee,"H1_TOTAL_FEE")
        close(metrics["total_slippage"],tot_slip,"H1_TOTAL_SLIP")
        marks=list(range(0,HOURS,24))
        if marks[-1]!=HOURS-1:marks.append(HOURS-1)
        daily=[navs[b]/navs[a]-1 for a,b in zip(marks,marks[1:])]
        gains=sum(x for x in daily if x>0)
        losses=-sum(x for x in daily if x<0)
        pf=gains/losses if losses else None
        if pf is not None:close(metrics["daily_profit_factor"],pf,"H1_PF")
        worst=min(daily)
        close(metrics["worst_daily_return"],worst,"H1_WORST_DAY")
        best=max(math.log1p(x) for x in daily)
        remove_best=math.expm1(math.log(navs[-1])-best)
        close(metrics["remove_best_day_roi"],remove_best,"H1_REMOVE_BEST")
        weekly_ret=[navs[min(HOURS-1,i+168)]/navs[i]-1
                    for i in range(0,HOURS-1,168)]
        worst_week=min(weekly_ret)
        close(metrics["worst_week_return"],worst_week,"H1_WORST_WEEK")
        top5=sum(sorted([max(x,0) for x in daily],reverse=True)[:5])
        concentration=top5/gains if gains else None
        if concentration is not None:
            close(metrics["top5_positive_days_share_of_gains"],concentration,"H1_TAIL_SHARE")
        for label,n in regimes.items():
            assert metrics["regimes_3x2"][label]["hours"]==n
        summaries[scenario]=dict(roi=roi,folds=fold_returns,maxdd=dd,pf=pf,
                                 remove_best=remove_best,worst_day=worst,
                                 worst_week=worst_week,concentration=concentration,
                                 fee=tot_fee,slippage=tot_slip,turnover=tot_turn,
                                 veto_weeks=veto_count)
    btc_ratio=spot[0][-1]/spot[0][0]
    eth_ratio=spot[1][-1]/spot[1][0]
    for scenario in ("severe","supersevere"):
        f,s=COSTS[scenario]
        c=f+s
        expected=dict(btc_only=btc_ratio/(1+c)-1,
                      eth_only=eth_ratio/(1+c)-1,
                      buy_once_45_45_10=(0.1+0.45*btc_ratio+0.45*eth_ratio)/(1+0.9*c)-1)
        for name,v in expected.items():
            close(report["benchmarks"][name][scenario],v,"H1_BENCHMARK_INVALID")
        close(report["benchmarks"]["cash"][scenario],0,"H1_CASH_BENCHMARK")
    s=summaries["severe"];u=summaries["supersevere"]
    gates=dict(
        severe_positive=s["roi"]>0,
        supersevere_positive=u["roi"]>0,
        severe_4_of_5_folds=sum(x>0 for x in s["folds"])>=4,
        supersevere_3_of_5_folds=sum(x>0 for x in u["folds"])>=3,
        both_maxdd_above_minus35pct=min(s["maxdd"],u["maxdd"])>=-0.35,
        both_daily_pf_above_one=all(x["pf"] is not None and x["pf"]>1 for x in (s,u)),
        both_remove_best_day_positive=min(s["remove_best"],u["remove_best"])>0,
        both_worst_day_above_minus15pct=min(s["worst_day"],u["worst_day"])>=-0.15,
        both_worst_week_above_minus25pct=min(s["worst_week"],u["worst_week"])>=-0.25,
        both_top5_gains_concentration_at_most_60pct=all(
            x["concentration"] is not None and x["concentration"]<=0.60 for x in (s,u)),
        supersevere_beats_buy_once_by_2pp=u["roi"]-report["benchmarks"]["buy_once_45_45_10"]["supersevere"]>=0.02,
        all_six_regimes_observed=all(x>0 for x in regimes.values()))
    if gates!=report["gates"]:
        raise ValueError("H1_INDEPENDENT_GATE_DISAGREEMENT")
    assert s["roi"]>=u["roi"]-1e-10
    assert summaries["severe_shock"]["roi"]<=s["roi"]+1e-10
    assert summaries["supersevere_shock"]["roi"]<=u["roi"]+1e-10
    try:
        close(s["fee"]+0.01,s["fee"],"INJECTED_LEDGER_TAMPER")
    except ValueError as exc:
        assert str(exc)=="INJECTED_LEDGER_TAMPER"
    else:
        raise ValueError("H1_NEGATIVE_CONTROL_FAILED")
    passed=all(gates.values())
    assert report["status"]==("PROVISIONAL_TRAIN_PASS_PENDING_INDEPENDENT_AND_NATIVE_PROVENANCE"
                              if passed else "PERMANENT_TRAIN_REJECT_NO_RETUNE")
    result=dict(status="INDEPENDENT_H1_ORIGINAL_DVOL_TO_OKX_CASH_LEDGER_VERIFIED",
                hours_per_scenario=HOURS,scenarios=summaries,
                independent_gates=gates,train_gates_passed=passed,
                negative_control="LEDGER_TAMPER_DETECTED",
                native_fee_tier_authenticated=False,
                validation_opened=False,holdout_opened=False,
                orders_enabled=False,promotion_authorized=False)
    (out/"h1_independent_oracle.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(dict(status=result["status"],train_gates_passed=passed,
                          severe_roi=s["roi"],supersevere_roi=u["roi"],
                          severe_folds=s["folds"],supersevere_folds=u["folds"],
                          failed_gates=[k for k,v in gates.items() if not v],
                          no_promotion=True),sort_keys=True))
    return result

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_h1_dvol_spot_oracle OKX_ROOT DVOL_ROOT H1_ROOT")
    verify_h1(*sys.argv[1:])
