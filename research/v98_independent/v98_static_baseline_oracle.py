#!/usr/bin/env python3
"""Independent source/cash/funding replay for V98 static controls; never engine approval."""
from __future__ import annotations
import argparse, csv, json, math, tempfile
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS, source_gate

COLUMNS = ("hour","cash_before","cash_after","equity_before","equity_after",
           "gap_pnl","intrahour_pnl","funding","cost","trade_notional",
           "qty","open","close","rate","lower","upper","target_weight")
BOOKS = {"cash": (0.,0.,0.,0.), "equal_20": (.20,.20,.20,.20)}

def close_enough(actual, expected, label, t):
    a=np.asarray(actual,float);b=np.asarray(expected,float)
    if a.shape!=b.shape or not np.allclose(a,b,rtol=1e-10,atol=1e-7):
        raise ValueError("STATIC_INDEPENDENT_MISMATCH_"+label+"_HOUR_"+str(t))
    return 1

def audit(d, ledger_path, book, expected_result):
    source_gate(d)
    if book not in BOOKS:raise ValueError("STATIC_ORACLE_BOOK")
    q=np.zeros(4);cash=10000.;previous_close=None;checks=0;events=0;fees=0.;funding=0.;n=0
    with Path(ledger_path).open(newline="") as handle:
        reader=csv.DictReader(handle)
        if tuple(reader.fieldnames)!=COLUMNS:raise ValueError("STATIC_ORACLE_COLUMNS")
        for row in reader:
            t=int(row["hour"])
            if t!=n or t>=HOURS:raise ValueError("STATIC_ORACLE_HOUR")
            def vec(name):
                v=np.asarray(json.loads(row[name]),float)
                if v.shape!=(4,):raise ValueError("STATIC_ORACLE_VECTOR_"+name)
                return v
            for field,source in (("open","o"),("close","c"),("rate","rate"),
                                 ("lower","mark_lower"),("upper","mark_upper")):
                checks+=close_enough(vec(field),d[source][t],field,t)
            checks+=close_enough(float(row["cash_before"]),cash,"cash_before",t)
            checks+=close_enough(float(row["equity_before"]),cash,"equity_before",t)
            op=d["o"][t];cl=d["c"][t]
            gap=float(np.dot(q,op-(previous_close if t else op)))
            cash+=gap
            checks+=close_enough(float(row["gap_pnl"]),gap,"gap",t)
            # Verify source event timing independently, not just aggregate count.
            observed=np.asarray(d["event"][t],bool)
            if observed.shape!=(4,) or not np.array_equal(observed,np.full(4,t%8==0)):
                raise ValueError("STATIC_ORACLE_FUNDING_CALENDAR_HOUR_"+str(t))
            f=0.
            if t%8==0:
                events+=4
                mark=np.where(q*d["rate"][t]>0,d["mark_upper"][t],d["mark_lower"][t])
                f=-float(np.dot(q,d["rate"][t]*mark))
                cash+=f
            funding+=f
            checks+=close_enough(float(row["funding"]),f,"funding",t)
            target=np.zeros(4)
            if t==744:
                target=np.array(BOOKS[book],float)
            if t in (744,HOURS-1):
                desired=target*cash/op
                delta=desired-q
                if np.any((np.abs(delta)>1e-12)&(d["q"][t]<=0)):
                    raise ValueError("STATIC_ORACLE_ZERO_VOLUME_FILL")
                traded=float(np.dot(np.abs(delta),op))
                fee=.001*traded
                cash-=fee;q=desired
            else:
                traded=fee=0.
            fees+=fee
            checks+=close_enough(vec("target_weight"),target,"target_weight",t)
            checks+=close_enough(float(row["trade_notional"]),traded,"notional",t)
            checks+=close_enough(float(row["cost"]),fee,"fee",t)
            checks+=close_enough(vec("qty"),q,"quantity",t)
            intra=float(np.dot(q,cl-op))
            cash+=intra
            checks+=close_enough(float(row["intrahour_pnl"]),intra,"intrahour",t)
            checks+=close_enough(float(row["cash_after"]),cash,"cash_after",t)
            checks+=close_enough(float(row["equity_after"]),cash,"equity_after",t)
            if cash<=0 or float(np.dot(np.abs(q),cl))>cash*(1+1e-8):
                raise ValueError("STATIC_ORACLE_HIDDEN_LEVERAGE")
            previous_close=cl
            n+=1
    if expected_result["passed"]:
        if n!=HOURS or events!=13524 or np.any(np.abs(q)>1e-10):
            raise ValueError("STATIC_ORACLE_INCOMPLETE")
        checks+=close_enough(cash,expected_result["final_equity"],"final",n)
        checks+=close_enough(fees,expected_result["fees_spread_impact"],"fees",n)
        checks+=close_enough(funding,expected_result["signed_funding"],"funding_total",n)
        decision="PASS_STATIC_INDEPENDENT_EXPOSED_ACCOUNTING_NOT_ENGINE"
    else:
        if n!=expected_result["hour"]:
            raise ValueError("STATIC_ORACLE_PARTIAL_LENGTH")
        decision="PARTIAL_STATIC_INDEPENDENT_SURVIVAL_FAILURE_NOT_ENGINE"
    return {"book":book,"decision":decision,"hours":n,"funding_events":events,
            "accounting_identities":checks,"cash_at_stop":cash,
            "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False,
            "2026_accessed":False,"holdout_accessed":False,"paper_live_authorized":False}

def run(d,outdir):
    out=Path(outdir)
    receipt=json.loads((out/"static_diagnostic.json").read_text())
    if receipt.get("decision")!="STATIC_DIAGNOSTIC_EXPOSED_ONLY_NOT_ENGINE" or len(receipt.get("cells",[]))!=36:
        raise ValueError("STATIC_ORACLE_RECEIPT")
    results=[]
    for book in BOOKS:
        base=next(x for x in receipt["cells"] if x["book"]==book and x["tier"]=="base"
                  and x["order"]=="carried_before_fill")
        path=out/("static_"+book+"_base_hourly.csv")
        result=audit(d,path,book,base)
        with tempfile.TemporaryDirectory() as td:
            bad=Path(td)/"bad.csv"
            with path.open(newline="") as src,bad.open("w",newline="") as dst:
                rd=csv.DictReader(src);wr=csv.DictWriter(dst,fieldnames=rd.fieldnames)
                wr.writeheader()
                for row in rd:
                    if int(row["hour"])==744:
                        row["cash_after"]=str(float(row["cash_after"])+1.)
                    wr.writerow(row)
            try:audit(d,bad,book,base)
            except ValueError as exc:
                if "STATIC_INDEPENDENT_MISMATCH" not in str(exc):raise
                result["tampered_cash_detected"]=True
            else:raise ValueError("STATIC_ORACLE_TAMPER_NOT_DETECTED")
        results.append(result)
        print("STATIC_INDEPENDENT",json.dumps(result,sort_keys=True),flush=True)
    (out/"static_independent_oracle.json").write_text(json.dumps(results,indent=2,sort_keys=True)+"\n")
    return results

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("old-root","old-envelope","new-root","corrected-root","out-dir"):
        p.add_argument("--"+name,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
