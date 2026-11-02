#!/usr/bin/env python3
"""Independent WH 2023-25 exposed source/signal/cash/funding oracle; no WH strategy imports."""
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
        raise ValueError("WH_INDEPENDENT_MISMATCH_"+label+"_HOUR_"+str(t))
    return 1
def independent_signal(d,t):
    # Reconstruct scalar asset-by-asset, no WH target, score or allocator imports.
    scores=[];r24=[];r168=[];ratios=[]
    for j in range(4):
        numerator=denominator=total_range=0.
        history=[]
        for h in range(t-167,t+1):
            o=float(d["o"][h,j]);c=float(d["c"][h,j])
            hi=float(d["h"][h,j]);lo=float(d["l"][h,j])
            relrange=(hi-lo)/max(c,1e-12)
            history.append(relrange)
            if h>=t-23:
                q=float(d["q"][h,j])
                rejection=(min(o,c)-lo-hi+max(o,c))/max(hi-lo,1e-12)
                numerator+=rejection*q;denominator+=q
                total_range+=relrange
        if denominator<=0:raise ValueError("WH_ORACLE_ZERO_VOLUME")
        scores.append(numerator/denominator)
        r24.append(math.log(d["c"][t,j]/d["c"][t-24,j]))
        r168.append(math.log(d["c"][t,j]/d["c"][t-168,j]))
        ratios.append(total_range/max(float(np.median(history)),1e-12))
    slots=np.zeros((4,4))
    j=sorted(range(4),key=lambda k:(-abs(scores[k]),k))[0]
    slots[0,j]=.35*np.sign(scores[j])
    if sum(r168)<0:slots[0]*=.65
    j=sorted(range(4),key=lambda k:(-ratios[k],k))[0]
    if ratios[j]>=1.5:slots[1,j]=-.10*np.sign(r24[j])
    top=sorted(range(4),key=lambda k:(-scores[k],k))[0]
    bot=sorted(range(4),key=lambda k:(scores[k],k))[0]
    if top!=bot and scores[top]-scores[bot]>=.10:
        slots[2,top]=+.08;slots[2,bot]=-.08
    if sum(r24)/4.<-.035:
        j=sorted(range(4),key=lambda k:(r24[k],k))[0];slots[3,j]=-.08
    elif sum(r24)/4.>.035:
        j=sorted(range(4),key=lambda k:(-r24[k],k))[0];slots[3,j]=+.08
    room=max(0.,.75-float(np.abs(slots[0]).sum()))
    for i in (1,2,3):
        gross=float(np.abs(slots[i]).sum())
        if gross>room and gross>0:slots[i]*=room/gross
        room=max(0.,room-float(np.abs(slots[i]).sum()))
    return slots.sum(axis=0)
def audit(d,ledger_path,receipt_path):
    source_gate(d)
    receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get("architecture")!="WH" or len(receipt.get("cells",[]))!=30:
        raise ValueError("WH_ORACLE_RECEIPT")
    base=next(x for x in receipt["cells"] if x["book"]=="WH_full"
              and x["tier"]=="base" and x["order"]=="carried_before_fill")
    cash=10000.;q=np.zeros(4);checks=events=decisions=0;costs=fund_total=0.;n=0
    with Path(ledger_path).open(newline="") as handle:
        reader=csv.DictReader(handle)
        if tuple(reader.fieldnames)!=COLS:raise ValueError("WH_ORACLE_COLUMNS")
        for row in reader:
            t=int(row["hour"])
            if t!=n or t>=HOURS:raise ValueError("WH_ORACLE_HOUR")
            v={k:np.asarray(json.loads(row[k]),float) for k in VECTORS}
            if any(v[k].shape!=(4,) for k in VECTORS):raise ValueError("WH_ORACLE_VECTOR")
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
                    raise ValueError("WH_ORACLE_ZERO_FILL_VOLUME")
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
                raise ValueError("WH_ORACLE_HIDDEN_LEVERAGE")
            n+=1
    if base["passed"]:
        if n!=HOURS or events!=13524 or decisions!=1096 or np.any(np.abs(q)>1e-10):
            raise ValueError("WH_ORACLE_INCOMPLETE")
        checks+=equal(cash,base["final_equity"],"final",HOURS)
        checks+=equal(costs,base["fees_spread_impact"],"fees",HOURS)
        checks+=equal(fund_total,base["signed_funding"],"funding",HOURS)
        decision="PASS_WH_INDEPENDENT_EXPOSED_ACCOUNTING_NOT_VALIDATION"
    else:
        if n!=base["hour"]:raise ValueError("WH_ORACLE_PARTIAL_LENGTH")
        decision="PARTIAL_WH_INDEPENDENT_ACCOUNTING_SURVIVAL_FAILURE_NOT_APPROVED"
    return {"decision":decision,"hours_reconciled":n,"funding_events_reconciled":events,
            "decisions_reconciled":decisions,"identities":checks,"cash_at_stop":cash,
            "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False,
            "2026_accessed":False,"holdout_accessed":False,"paper_live_authorized":False}
def run(d,outdir):
    out=Path(outdir);ledger=out/"wh_base_full_hourly_ledger.csv"
    receipt=out/"wh_exposed_physical.json"
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
            if "WH_INDEPENDENT_MISMATCH" not in str(exc):raise
            result["tampered_cash_detected"]=True
        else:raise ValueError("WH_TAMPER_NOT_DETECTED")
    (out/"wh_independent_oracle.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("WH_INDEPENDENT",json.dumps(result,sort_keys=True),flush=True)
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
