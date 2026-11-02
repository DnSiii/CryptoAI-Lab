#!/usr/bin/env python3
"""Independent WK 2023-25 exposed source/signal/cash/funding oracle; no WK strategy imports."""
from __future__ import annotations
import argparse,csv,json,math,tempfile
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS,source_gate
CLOCK=tuple(range(743,HOURS-1,48))
COLS=("hour","cash_before","cash_after","equity_before","equity_after","gap_pnl",
      "intrahour_pnl","funding","cost","trade_notional","qty","open","close",
      "rate","lower","upper","target_weight")
VECTORS=("qty","open","close","rate","lower","upper","target_weight")
def equal(a,b,label,t,atol=1e-6):
    if not np.allclose(a,b,rtol=1e-11,atol=atol,equal_nan=True):
        raise ValueError("WK_INDEPENDENT_MISMATCH_"+label+"_HOUR_"+str(t))
    return 1
def independent_signal(d,t):
    # Independent WK target reconstruction from source, no WK strategy import.
    lp=np.log(np.asarray(d["c"][t-336:t+1],float))
    hourly=lp[1:]-lp[:-1]
    recent=hourly[-24:]
    def independent_lag_corr(series):
        a=series[1:].copy();b=series[:-1].copy()
        a-=float(a.mean());b-=float(b.mean())
        den=math.sqrt(float(a@a)*float(b@b))
        return float(a@b)/den if den>1e-15 else 0.
    persistence=np.array([independent_lag_corr(hourly[:,j]) for j in range(4)])
    intraday=np.array([independent_lag_corr(recent[:,j]) for j in range(4)])
    r72=lp[-1]-lp[-73]
    r24=lp[-1]-lp[-25]
    w=np.zeros((4,4))
    score=persistence*r72
    main=sorted(range(4),key=lambda j:(-abs(score[j]),j))[0]
    if score[main]!=0:w[0,main]=.52*np.sign(score[main])
    mean_p=float(persistence.mean())
    if mean_p<=0:w[0]*=.75
    change=intraday-persistence
    best=sorted(range(4),key=lambda j:(-abs(change[j]),j))[0]
    if abs(change[best])>=.10 and intraday[best]*r24[best]!=0:
        w[1,best]=.12*np.sign(intraday[best]*r24[best])
    high=sorted(range(4),key=lambda j:(-persistence[j],j))[0]
    low=sorted(range(4),key=lambda j:(persistence[j],j))[0]
    if high!=low and persistence[high]-persistence[low]>=.10:
        w[2,high]=.08;w[2,low]=-.08
    market=float(r24.mean())
    if market<=-.04 and mean_p>0:w[3,0]=-.10
    elif market>=+.04 and mean_p<0:w[3,0]=-.08
    if float(np.std(recent,axis=0).mean())>2.*max(float(np.std(hourly,axis=0).mean()),1e-12):
        w*=.65
    free=max(0.,.80-float(np.abs(w[0]).sum()))
    for slot in (1,2,3):
        size=float(np.abs(w[slot]).sum())
        if size>free and size>0:w[slot]*=free/size
        free=max(0.,free-float(np.abs(w[slot]).sum()))
    return w.sum(axis=0)

def audit(d,ledger_path,receipt_path):
    source_gate(d)
    receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get("architecture")!="WK" or len(receipt.get("cells",[]))!=30:
        raise ValueError("WK_ORACLE_RECEIPT")
    base=next(x for x in receipt["cells"] if x["book"]=="WK_full"
              and x["tier"]=="base" and x["order"]=="carried_before_fill")
    cash=10000.;q=np.zeros(4);checks=events=decisions=0;costs=fund_total=0.;n=0
    with Path(ledger_path).open(newline="") as handle:
        reader=csv.DictReader(handle)
        if tuple(reader.fieldnames)!=COLS:raise ValueError("WK_ORACLE_COLUMNS")
        for row in reader:
            t=int(row["hour"])
            if t!=n or t>=HOURS:raise ValueError("WK_ORACLE_HOUR")
            v={k:np.asarray(json.loads(row[k]),float) for k in VECTORS}
            if any(v[k].shape!=(4,) for k in VECTORS):raise ValueError("WK_ORACLE_VECTOR")
            for k,source in (("open","o"),("close","c"),("rate","rate"),
                             ("lower","mark_lower"),("upper","mark_upper")):
                checks+=equal(v[k],d[source][t],k,t)
            checks+=equal(float(row["cash_before"]),cash,"cash_before",t)
            op=d["o"][t];cl=d["c"][t]
            gap=float(np.dot(q,op-(d["c"][t-1] if t else op)))
            cash+=gap;checks+=equal(float(row["gap_pnl"]),gap,"gap",t)
            f=0.
            if t%8==0:
                events+=4
                mark=np.where(q*d["rate"][t]>0,d["mark_upper"][t],d["mark_lower"][t])
                f=-float(np.dot(q,d["rate"][t]*mark))
                cash+=f
            fund_total+=f;checks+=equal(float(row["funding"]),f,"funding",t)
            if t==HOURS-1 or t-1 in CLOCK:
                target=np.zeros(4) if t==HOURS-1 else independent_signal(d,t-1)
                if t!=HOURS-1:decisions+=1
                checks+=equal(v["target_weight"],target,"independent_signal",t,1e-10)
                newq=target*cash/op
                delta=newq-q
                if np.any((np.abs(delta)>1e-12)&(d["q"][t]<=0)):
                    raise ValueError("WK_ORACLE_ZERO_FILL_VOLUME")
                notional=float(np.dot(np.abs(delta),op))
                fee=.001*notional
                cash-=fee;q=newq
            else:
                checks+=equal(v["target_weight"],np.zeros(4),"no_trade",t,1e-10)
                notional=fee=0.
            checks+=equal(float(row["trade_notional"]),notional,"trade_notional",t)
            checks+=equal(float(row["cost"]),fee,"cost",t)
            costs+=fee
            checks+=equal(v["qty"],q,"position",t,1e-9)
            intra=float(np.dot(q,cl-op));cash+=intra
            checks+=equal(float(row["intrahour_pnl"]),intra,"intrahour",t)
            checks+=equal(float(row["cash_after"]),cash,"cash_after",t)
            if cash<=0 or np.dot(np.abs(q),cl)>cash*(1+1e-8):
                raise ValueError("WK_ORACLE_HIDDEN_LEVERAGE")
            n+=1
    if base["passed"]:
        if n!=HOURS or events!=13524 or decisions!=548 or np.any(np.abs(q)>1e-10):
            raise ValueError("WK_ORACLE_INCOMPLETE")
        checks+=equal(cash,base["final_equity"],"final",HOURS)
        checks+=equal(costs,base["fees_spread_impact"],"fees",HOURS)
        checks+=equal(fund_total,base["signed_funding"],"funding",HOURS)
        decision="PASS_WK_INDEPENDENT_EXPOSED_ACCOUNTING_NOT_VALIDATION"
    else:
        if n!=base["hour"]:raise ValueError("WK_ORACLE_PARTIAL_LENGTH")
        decision="PARTIAL_WK_INDEPENDENT_ACCOUNTING_SURVIVAL_FAILURE_NOT_APPROVED"
    return {"decision":decision,"hours_reconciled":n,"funding_events_reconciled":events,
            "decisions_reconciled":decisions,"identities":checks,"cash_at_stop":cash,
            "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False,
            "2026_accessed":False,"holdout_accessed":False,"paper_live_authorized":False}
def run(d,outdir):
    out=Path(outdir);ledger=out/"wk_base_full_hourly_ledger.csv"
    receipt=out/"wk_exposed_physical.json"
    result=audit(d,ledger,receipt)
    with tempfile.TemporaryDirectory() as tmp:
        bad=Path(tmp)/"tampered.csv"
        with ledger.open(newline="") as src,bad.open("w",newline="") as dest:
            reader=csv.DictReader(src);writer=csv.DictWriter(dest,fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                if int(row["hour"])==744:row["cash_after"]=str(float(row["cash_after"])+1.)
                writer.writerow(row)
        try:audit(d,bad,receipt)
        except ValueError as exc:
            if "WK_INDEPENDENT_MISMATCH" not in str(exc):raise
            result["tampered_cash_detected"]=True
        else:raise ValueError("WK_TAMPER_NOT_DETECTED")
    (out/"wk_independent_oracle.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("WK_INDEPENDENT",json.dumps(result,sort_keys=True),flush=True)
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
