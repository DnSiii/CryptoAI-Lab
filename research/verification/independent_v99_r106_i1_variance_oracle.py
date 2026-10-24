"""Independent I1 first-party original-byte and forward-variance oracle. NO ORDERS."""
from __future__ import annotations
import copy
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path
from research.tools.v99_r106_d1_real_train_source_join import START,END,HOUR,HOURS,FOLD_EDGES,strict_json
from research.verification.independent_d1_native_train_receipts import verify

DAY=24*HOUR
N=720


def read_spot(root):
    root=Path(root)
    if verify(root)["status"]!="INDEPENDENT_FOUR_LEG_TRAIN_SOURCE_COMPLETE_NO_ECONOMICS":
        raise ValueError("ORACLE_SPOT_RECEIPT_FAIL")
    result={}
    for asset in ("BTC","ETH"):
        rows=strict_json(root/(asset+"-USDT")/"train_opens.json")
        if len(rows)!=HOURS or any(row["ts"]!=START+i*HOUR for i,row in enumerate(rows)):
            raise ValueError("ORACLE_SPOT_GRID_FAIL")
        result[asset]=[float(row["open"]) for row in rows]
        if not all(math.isfinite(x) and x>0 for x in result[asset]):
            raise ValueError("ORACLE_SPOT_INVALID")
    return result


def read_dvol(root):
    root=Path(root)
    doc=strict_json(root/"dvol_train_source.json")
    if doc.get("schema")!="V99_DERIBIT_FIRSTPARTY_DVOL_PIT_TRAIN_V1" or doc.get("good_folds")!=5:
        raise ValueError("ORACLE_DVOL_MANIFEST_INVALID")
    if doc.get("gate")!="DVOL_SOURCE_READY_FOR_ONE_ENGINE_PREREG":
        raise ValueError("ORACLE_DVOL_NOT_READY")
    if (doc["start_ms"],doc["end_exclusive_ms"])!=(START,END):
        raise ValueError("ORACLE_DVOL_PARTITION")
    for flag in ("economic_train_executed","validation_opened","holdout_opened","orders_enabled","promotion_authorized"):
        if doc[flag]:
            raise ValueError("ORACLE_DVOL_SOURCE_CONTAMINATION")
    original={}
    for rec in doc["source_rows"]:
        if rec["status"]!="SOURCE_OK":
            raise ValueError("ORACLE_DVOL_SOURCE_MISSING")
        raw=(root/rec["receipt_file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=rec["sha256"]:
            raise ValueError("ORACLE_DVOL_ORIGINAL_HASH")
        data=json.loads(raw)["result"]["data"]
        original[(rec["fold"],rec["currency"])]={
            int(candle[0]):float(candle[4]) for candle in data
            if rec["query_start_ms"]<=int(candle[0])<=rec["query_end_ms"]}
    weekly={}
    for w in doc["weekly"]:
        t,f,c=w["decision_ms"],w["fold"],w["currency"]
        if not (w["eligible"] and FOLD_EDGES[f-1]<=t<FOLD_EDGES[f]):
            raise ValueError("ORACLE_DVOL_WEEK_INVALID")
        stamp=w["candle_start_ms"]
        if not (stamp+DAY<t and 0<t-stamp-DAY<=2*DAY):
            raise ValueError("ORACLE_DVOL_LOOKAHEAD")
        if original[(f,c)].get(stamp)!=w["dvol_close"]:
            raise ValueError("ORACLE_DVOL_ORIGINAL_PRICE")
        weekly[(t,c)]=float(w["dvol_close"])
    if len(weekly)!=188:
        raise ValueError("ORACLE_DVOL_WEEK_COUNT")
    return weekly


def original_windows(weekly):
    times=sorted(t for t,c in weekly if c=="BTC" and (t,"ETH") in weekly)
    windows=[]
    for fold in range(5):
        lo,hi=FOLD_EDGES[fold:fold+2]
        eligible=[t for t in times if lo<=t and t+N*HOUR<hi]
        last=lo-N*HOUR
        for t in eligible:
            if t>=last+N*HOUR:
                windows.append((fold+1,t))
                last=t
    return windows


def lagged_regime(t,prices):
    i=(t-START)//HOUR
    if i<889:
        return "insufficient_lag"
    slope=prices[i-1]/prices[i-721]-1
    name="up" if slope>0.02 else ("down" if slope< -0.02 else "flat")
    vols=[]
    for ending in range(i-168,i+1):
        x=[math.log(prices[k]/prices[k-1]) for k in range(ending-167,ending+1)]
        vols.append(statistics.pstdev(x))
    return name+"_"+("high" if vols[-1]>statistics.median(vols[:-1]) else "low")


def verify_report(spot,dvol,report):
    if report.get("schema")!="I1_FIRSTPARTY_VARIANCE_PREMIUM_NONOVERLAP_STRUCTURAL_V1":
        raise ValueError("ORACLE_REPORT_SCHEMA")
    if (report["train_start_ms"],report["train_end_exclusive_ms"],report["horizon_hours"])!=(START,END,N):
        raise ValueError("ORACLE_PARTITION")
    if report["preregistration_commit"]!="89a88e4a248e42e87e55d0a0ea4c61322d6ea222":
        raise ValueError("ORACLE_PREREG")
    for k in ("promotion_authorized","validation_opened","holdout_opened","orders_enabled",
              "paper_publication_authorized","trading_engine_evaluated","economic_backtest_executed"):
        if report[k]:
            raise ValueError("ORACLE_FORBIDDEN_"+k)
    windows=original_windows(dvol)
    rows=report["rows"]
    if len(rows)!=len(windows)*2 or report["windows"]!=len(windows):
        raise ValueError("ORACLE_ROW_COUNT")
    results={"BTC":[],"ETH":[]}
    for (fold,t),pair in zip(windows,(rows[k:k+2] for k in range(0,len(rows),2))):
        i=(t-START)//HOUR
        regime=lagged_regime(t,spot["BTC"])
        for r,asset in zip(pair,("BTC","ETH")):
            if (r["fold"],r["decision_ms"],r["asset"],r["regime"])!=(fold,t,asset,regime):
                raise ValueError("ORACLE_ROW_IDENTITY")
            iv=dvol[(t,asset)]
            implied=(iv*iv/10000.0)*(30.0/365.0)
            # Independent explicit sum, no reuse of engine's fsum expression.
            qv=0.0
            increments=[]
            for k in range(i+1,i+N+1):
                increments.append(math.log(spot[asset][k]/spot[asset][k-1])**2)
            qv=math.fsum(increments)
            expected={"dvol":iv,"implied_variance":implied,"realized_variance":qv,
                      "premium":implied-qv,"premium_ratio":(implied-qv)/implied,
                      "realized_to_implied":qv/implied}
            for key,val in expected.items():
                if not math.isclose(r[key],val,rel_tol=1e-11,abs_tol=1e-12):
                    raise ValueError("ORACLE_MISMATCH_"+key)
            results[asset].append((fold,implied-qv,qv/implied))
    gates={}
    for asset in ("BTC","ETH"):
        series=results[asset]
        summaries=[]
        for fold in range(1,6):
            a=[p for f,p,ratio in series if f==fold]
            summaries.append(dict(fold=fold,windows=len(a),mean_premium=statistics.mean(a) if a else None,
                                  median_premium=statistics.median(a) if a else None,
                                  min_premium=min(a) if a else None))
        f=report["folds"][asset]
        for actual,expected in zip(f["folds"],summaries):
            if actual["fold"]!=expected["fold"] or actual["windows"]!=expected["windows"]:
                raise ValueError("ORACLE_FOLD_COUNT")
            for k in ("mean_premium","median_premium","min_premium"):
                if (actual[k] is None)!=(expected[k] is None):
                    raise ValueError("ORACLE_FOLD_NULL")
                if actual[k] is not None and not math.isclose(actual[k],expected[k],rel_tol=1e-11,abs_tol=1e-12):
                    raise ValueError("ORACLE_FOLD_VALUE")
        mean=statistics.mean(x[1] for x in series) if series else None
        pos=sum(x["mean_premium"] is not None and x["mean_premium"]>0 for x in summaries)
        positives=sorted((max(0.0,x[1]) for x in series),reverse=True)
        denom=math.fsum(positives)
        share=sum(positives[:2])/denom if denom else None
        ratio=max((x[2] for x in series),default=None)
        for name,expect in (("all_mean_premium",mean),("positive_folds",pos),
                            ("top_two_positive_premium_share",share),
                            ("worst_realized_to_implied",ratio)):
            got=f[name]
            if (got is None)!=(expect is None) or (got is not None and
                not math.isclose(got,expect,rel_tol=1e-11,abs_tol=1e-12)):
                raise ValueError("ORACLE_AGG_"+name)
        gates[asset]=dict(pos=pos,mean=mean,folds=summaries)
    fixed={
        "two_nonoverlapping_windows_each_fold_both_assets":all(p["windows"]>=2 for a in gates.values() for p in a["folds"]),
        "btc_at_least_four_positive_folds":gates["BTC"]["pos"]>=4,
        "eth_at_least_four_positive_folds":gates["ETH"]["pos"]>=4,
        "btc_all_mean_positive":gates["BTC"]["mean"] is not None and gates["BTC"]["mean"]>0,
        "eth_all_mean_positive":gates["ETH"]["mean"] is not None and gates["ETH"]["mean"]>0,
    }
    if fixed!=report["gates"]:
        raise ValueError("ORACLE_GATES_MISMATCH")
    expected_status=("GROSS_STRUCTURAL_SCREEN_PASS_EXECUTABLE_OPTIONS_DATA_STILL_BLOCKED"
                     if all(fixed.values()) else "I1_STRUCTURAL_MECHANISM_REJECTED_NO_RETUNE")
    if report["status"]!=expected_status:
        raise ValueError("ORACLE_STATUS_MISMATCH")
    return dict(status="INDEPENDENT_ORIGINAL_DVOL_SPOT_30D_VARIANCE_REEXECUTION_VERIFIED",
                decision=expected_status,windows=len(windows),positive_folds={a:x["pos"] for a,x in gates.items()},
                gates=fixed,validation_opened=False,holdout_opened=False,promotion_authorized=False)


def main(spot_root,dvol_root,report_dir):
    spot=read_spot(spot_root)
    dvol=read_dvol(dvol_root)
    p=Path(report_dir)
    report=json.loads((p/"i1_structural_report.json").read_text())
    result=verify_report(spot,dvol,report)
    # Adversarial negative control: one altered economic observation MUST fail.
    corrupted=copy.deepcopy(report)
    corrupted["rows"][0]["realized_variance"]+=0.00001
    try:
        verify_report(spot,dvol,corrupted)
    except ValueError as e:
        if "ORACLE_MISMATCH_realized_variance" not in str(e):
            raise
    else:
        raise ValueError("ORACLE_FAILED_NEGATIVE_CONTROL")
    result["adversarial_corruption_rejected"]=True
    (p/"i1_independent_oracle.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    return result


if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: python -m research.verification.independent_v99_r106_i1_variance_oracle OKX_ROOT DVOL_ROOT REPORT_DIR")
    main(*sys.argv[1:])
