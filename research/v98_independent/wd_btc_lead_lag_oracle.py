#!/usr/bin/env python3
"""V98 WD independent source-signal and physical cash/funding oracle, no WD imports."""
from __future__ import annotations
import argparse,csv,json,math,tempfile
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS,CLOCK,source_gate
INITIAL=10000.
COLS=("hour","cash_before","cash_after","equity_before","equity_after",
      "gap_pnl","intrahour_pnl","funding","cost","trade_notional",
      "qty","open","close","rate","lower","upper","target_weight")
VECTORS=("qty","open","close","rate","lower","upper","target_weight")
def eq(a,b,label,t,atol=1e-6):
    if not np.allclose(a,b,rtol=1e-11,atol=atol,equal_nan=True):
        raise ValueError("WD_INDEPENDENT_MISMATCH_"+label+"_HOUR_"+str(t))
    return 1

def independent_targets(d):
    # Separate implementation: independently estimate BTC-alts covariance and rank.
    close=np.asarray(d["c"],float)
    logs=np.log(close)
    output={}
    for t in CLOCK:
        history=np.diff(logs[t-719:t+1],axis=0)
        var=float(np.var(history[:,0],ddof=1))
        betas=[1.]
        for asset in (1,2,3):
            cov=float(np.cov(history[:,0],history[:,asset],ddof=1)[0,1])
            betas.append(float(np.clip(cov/var,.5,2.5)) if var>1e-15 else 1.)
        r72=logs[t]-logs[t-72]
        r24=logs[t]-logs[t-24]
        signal=float(r72[0])
        residual72={j:float(r72[j]-betas[j]*signal) for j in (1,2,3)}
        residual24={j:float(r24[j]-betas[j]*r24[0]) for j in (1,2,3)}
        side=1. if signal>=0 else -1.
        lagger=min((1,2,3),key=lambda j:(side*residual72[j],j))
        slots=np.zeros((4,4))
        scale=.75 if logs[t,0]<logs[t-168,0] else 1.
        slots[0,0]=side*.18*scale
        slots[0,lagger]=side*.24*scale
        impulse=float(logs[t,0]-logs[t-12,0])
        if abs(impulse)>=.025:
            impulse_side=1. if impulse>0 else -1.
            lag=min((1,2,3),key=lambda j:(impulse_side*residual24[j],j))
            slots[1,lag]=impulse_side*.10
        low=min((1,2,3),key=lambda j:(residual24[j],j))
        high=min((1,2,3),key=lambda j:(-residual24[j],j))
        if low!=high:
            slots[2,low]=.07
            slots[2,high]=-.07
        current_vol=float(np.std(np.diff(logs[t-23:t+1,0])))
        past_vol=[float(np.std(np.diff(logs[k-23:k+1,0])))
                  for k in range(t-720,t-23,24)]
        high_vol=current_vol>float(np.median(past_vol))
        max_beta=min((1,2,3),key=lambda j:(-betas[j],j))
        slots[3,max_beta]=-.10 if high_vol else .07
        remaining=.90-float(np.abs(slots[0]).sum())
        for k in (1,2,3):
            g=float(np.abs(slots[k]).sum())
            if g>remaining and g>0:slots[k]*=remaining/g
            remaining=max(0.,remaining-float(np.abs(slots[k]).sum()))
        output[t]=slots.sum(axis=0)
    return output

def audit(d,ledger_path,receipt_path):
    source_gate(d)
    receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get("architecture")!="WD" or len(receipt.get("cells",[]))!=30:
        raise ValueError("WD_ORACLE_RECEIPT")
    base=next((x for x in receipt["cells"] if x["book"]=="WD_full" and x["tier"]=="base"
               and x["order"]=="carried_before_fill"),None)
    if not base or not base["passed"] or receipt.get("2026_accessed") or receipt.get("holdout_accessed"):
        raise ValueError("WD_ORACLE_BASE")
    expected=independent_targets(d)
    cash=INITIAL;q=np.zeros(4);events=checks=n=0;cost_total=funding_total=0.;decisions=0
    with Path(ledger_path).open(newline="") as handle:
        reader=csv.DictReader(handle)
        if tuple(reader.fieldnames)!=COLS:raise ValueError("WD_ORACLE_COLUMNS")
        for row in reader:
            t=int(row["hour"])
            if t!=n or t>=HOURS:raise ValueError("WD_ORACLE_CLOCK")
            v={k:np.asarray(json.loads(row[k]),float) for k in VECTORS}
            if any(v[k].shape!=(4,) for k in VECTORS):raise ValueError("WD_ORACLE_VECTOR")
            checks+=eq(v["open"],d["o"][t],"open",t)
            checks+=eq(v["close"],d["c"][t],"close",t)
            checks+=eq(v["rate"],d["rate"][t],"rate",t)
            checks+=eq(v["lower"],d["mark_lower"][t],"lower",t)
            checks+=eq(v["upper"],d["mark_upper"][t],"upper",t)
            checks+=eq(float(row["cash_before"]),cash,"before",t)
            op=d["o"][t];cl=d["c"][t]
            gap=float(np.dot(q,op-(d["c"][t-1] if t else op)))
            cash+=gap
            checks+=eq(float(row["gap_pnl"]),gap,"gap",t)
            f=0.
            if t%8==0:
                events+=4
                mark=np.where(q*d["rate"][t]>0,d["mark_upper"][t],d["mark_lower"][t])
                f=-float(np.dot(q,d["rate"][t]*mark))
                cash+=f
            funding_total+=f
            checks+=eq(float(row["funding"]),f,"funding",t)
            if t==HOURS-1 or t-1 in expected:
                target=np.zeros(4) if t==HOURS-1 else expected[t-1]
                checks+=eq(v["target_weight"],target,"signal",t,atol=1e-12)
                if t!=HOURS-1:decisions+=1
                if np.abs(target).sum()>.90+1e-9:raise ValueError("WD_ORACLE_GROSS")
                newq=target*cash/op
                delta=newq-q
                if np.any((np.abs(delta)>1e-12)&(d["q"][t]<=0)):
                    raise ValueError("WD_ORACLE_ZERO_VOLUME")
                notional=float(np.dot(np.abs(delta),op))
                fee=.001*notional
                cash-=fee;q=newq
            else:
                checks+=eq(v["target_weight"],np.zeros(4),"unscheduled",t,atol=1e-12)
                notional=fee=0.
            checks+=eq(float(row["trade_notional"]),notional,"notional",t)
            checks+=eq(float(row["cost"]),fee,"cost",t)
            cost_total+=fee
            checks+=eq(v["qty"],q,"position",t,atol=1e-9)
            intra=float(np.dot(q,cl-op))
            cash+=intra
            checks+=eq(float(row["intrahour_pnl"]),intra,"intrahour",t)
            checks+=eq(float(row["cash_after"]),cash,"after",t)
            if cash<=0 or np.dot(np.abs(q),cl)>cash*(1+1e-8):
                raise ValueError("WD_ORACLE_HIDDEN_LEVERAGE")
            n+=1
    if n!=HOURS or events!=13524 or decisions!=1096 or np.any(np.abs(q)>1e-10):
        raise ValueError("WD_ORACLE_COMPLETENESS")
    checks+=eq(cash,base["final_equity"],"final",HOURS)
    checks+=eq(cost_total,base["fees_spread_impact"],"cost_total",HOURS)
    checks+=eq(funding_total,base["signed_funding"],"funding_total",HOURS)
    return {"decision":"PASS_INDEPENDENT_WD_EXPOSED_ACCOUNTING_NOT_VALIDATION",
            "hours":n,"funding_events":events,"signal_decisions":decisions,
            "independent_identities":checks,"final_NAV":cash,
            "cost":cost_total,"signed_funding":funding_total,
            "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False,
            "2026_accessed":False,"holdout_accessed":False,"paper_live_authorized":False}

def run(d,outdir):
    out=Path(outdir)
    ledger=out/"wd_base_full_hourly_ledger.csv"
    receipt=out/"wd_exposed_physical.json"
    result=audit(d,ledger,receipt)
    with ledger.open(newline="") as handle:rows=list(csv.DictReader(handle))
    with tempfile.TemporaryDirectory() as td:
        bad=Path(td)/"bad.csv"
        rows[744]["cash_after"]=str(float(rows[744]["cash_after"])+1.)
        with bad.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
        try:audit(d,bad,receipt)
        except ValueError as e:
            if "WD_INDEPENDENT_MISMATCH" not in str(e):raise
            result["tampered_cash_detected"]=True
        else:raise ValueError("WD_TAMPER_NOT_DETECTED")
    (out/"wd_independent_oracle.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("WD_INDEPENDENT",json.dumps(result,sort_keys=True),flush=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
