#!/usr/bin/env python3
"""Independent WJ 2023-25 exposed source/signal/cash/funding oracle; no WJ strategy imports."""
from __future__ import annotations
import argparse,csv,json,math,tempfile
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS,source_gate
CLOCK=tuple(range(743,HOURS-1,24))
COLS=("hour","cash_before","cash_after","equity_before","equity_after","gap_pnl",
      "intrahour_pnl","funding","cost","trade_notional","qty","open","close",
      "rate","lower","upper","target_weight")
VECTORS=("qty","open","close","rate","lower","upper","target_weight")
def equal(a,b,label,t,atol=1e-6):
    if not np.allclose(a,b,rtol=1e-11,atol=atol,equal_nan=True):
        raise ValueError("WJ_INDEPENDENT_MISMATCH_"+label+"_HOUR_"+str(t))
    return 1
def independent_signal(d,t):
    # Separate source-to-target implementation; never imports WJ strategy.
    # Construct hourly log returns from a bounded, strictly past window.
    lp=np.log(np.asarray(d["c"][t-672:t+1],float))
    h=lp[1:]-lp[:-1]
    c_long=np.corrcoef(h,rowvar=False)
    c_short=np.corrcoef(h[-72:],rowvar=False)
    if not np.isfinite(c_long).all() or not np.isfinite(c_short).all():
        raise ValueError("WJ_ORACLE_NONFINITE_CORRELATION")
    pairs=[(i,j) for i in range(4) for j in range(i+1,4)]
    corr=float(sum(c_long[i,j] for i,j in pairs)/6.)
    recent_corr=float(sum(c_short[i,j] for i,j in pairs)/6.)
    r336=lp[-1]-lp[-337]
    r72=lp[-1]-lp[-73]
    r24=lp[-1]-lp[-25]
    f336=float(r336.mean());f72=float(r72.mean());f24=float(r24.mean())
    w=np.zeros((4,4),float)
    v=np.std(h,axis=0)
    if f336!=0.:
        weights=1./np.maximum(v,1e-8)
        weights=weights/float(weights.sum())
        amount=.56 if f336*f72>0 else .28
        if corr<.50:amount*=.75
        w[0]=np.sign(f336)*amount*weights
    residual=r72-f72
    best=sorted(range(4),key=lambda j:(-abs(residual[j]),j))[0]
    if corr-recent_corr>=.20 and abs(residual[best])>.02:
        w[1,best]=.12*np.sign(residual[best])
    _,a,b=sorted([(float(c_long[i,j]),i,j) for i,j in pairs],
                 key=lambda row:(-row[0],row[1],row[2]))[0]
    if c_long[a,b]>0:
        ra=h[:,a];rb=h[:,b]
        aa=ra-ra.mean()
        den=float(np.dot(aa,aa))
        beta=float(np.dot(aa,rb-rb.mean())/den) if den>1e-15 else 0.
        resid=lp[-168:,b]-beta*lp[-168:,a]
        s=float(np.std(resid))
        z=(float(resid[-1])-float(np.mean(resid)))/max(s,1e-12)
        if abs(z)>=1.25:
            w[2,a]=.08*np.sign(z)
            w[2,b]=-.08*np.sign(z)
    if corr>=.50:
        if f24<=-.05:w[3,0]=-.12
        elif f24>=+.05:w[3,0]=+.08
    if float(np.std(h[-24:].mean(axis=1)))>2.*max(float(np.std(h.mean(axis=1))),1e-12):
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
    if receipt.get("architecture")!="WJ" or len(receipt.get("cells",[]))!=30:
        raise ValueError("WJ_ORACLE_RECEIPT")
    base=next(x for x in receipt["cells"] if x["book"]=="WJ_full"
              and x["tier"]=="base" and x["order"]=="carried_before_fill")
    cash=10000.;q=np.zeros(4);checks=events=decisions=0;costs=fund_total=0.;n=0
    with Path(ledger_path).open(newline="") as handle:
        reader=csv.DictReader(handle)
        if tuple(reader.fieldnames)!=COLS:raise ValueError("WJ_ORACLE_COLUMNS")
        for row in reader:
            t=int(row["hour"])
            if t!=n or t>=HOURS:raise ValueError("WJ_ORACLE_HOUR")
            v={k:np.asarray(json.loads(row[k]),float) for k in VECTORS}
            if any(v[k].shape!=(4,) for k in VECTORS):raise ValueError("WJ_ORACLE_VECTOR")
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
                    raise ValueError("WJ_ORACLE_ZERO_FILL_VOLUME")
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
                raise ValueError("WJ_ORACLE_HIDDEN_LEVERAGE")
            n+=1
    if base["passed"]:
        if n!=HOURS or events!=13524 or decisions!=1096 or np.any(np.abs(q)>1e-10):
            raise ValueError("WJ_ORACLE_INCOMPLETE")
        checks+=equal(cash,base["final_equity"],"final",HOURS)
        checks+=equal(costs,base["fees_spread_impact"],"fees",HOURS)
        checks+=equal(fund_total,base["signed_funding"],"funding",HOURS)
        decision="PASS_WJ_INDEPENDENT_EXPOSED_ACCOUNTING_NOT_VALIDATION"
    else:
        if n!=base["hour"]:raise ValueError("WJ_ORACLE_PARTIAL_LENGTH")
        decision="PARTIAL_WJ_INDEPENDENT_ACCOUNTING_SURVIVAL_FAILURE_NOT_APPROVED"
    return {"decision":decision,"hours_reconciled":n,"funding_events_reconciled":events,
            "decisions_reconciled":decisions,"identities":checks,"cash_at_stop":cash,
            "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False,
            "2026_accessed":False,"holdout_accessed":False,"paper_live_authorized":False}
def run(d,outdir):
    out=Path(outdir);ledger=out/"wj_base_full_hourly_ledger.csv"
    receipt=out/"wj_exposed_physical.json"
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
            if "WJ_INDEPENDENT_MISMATCH" not in str(exc):raise
            result["tampered_cash_detected"]=True
        else:raise ValueError("WJ_TAMPER_NOT_DETECTED")
    (out/"wj_independent_oracle.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("WJ_INDEPENDENT",json.dumps(result,sort_keys=True),flush=True)
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
