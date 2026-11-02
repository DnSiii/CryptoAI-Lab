#!/usr/bin/env python3
"""Independent V98 VY source, fill, signed funding and cash replay from frozen ledger.
Never imports VY physical simulator. Exposed training only, not live or future validation.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS,CLOCK,source_gate

INITIAL=10000.
COLS=("hour","cash_before","cash_after","equity_before","equity_after",
      "gap_pnl","intrahour_pnl","funding","cost","trade_notional",
      "qty","open","close","rate","lower","upper","target_weight")
VECTORS=("qty","open","close","rate","lower","upper","target_weight")
def check(a,b,name,t,atol=1e-6):
    if not np.allclose(a,b,rtol=1e-11,atol=atol,equal_nan=True):
        raise ValueError("VY_INDEPENDENT_MISMATCH_"+name+"_HOUR_"+str(t))
    return 1

def audit(d,ledger_path,receipt_path):
    source_gate(d)
    receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get("architecture")!="VY" or len(receipt.get("cells",[]))!=30:
        raise ValueError("VY_ORACLE_RECEIPT")
    expected=next((r for r in receipt["cells"] if r["book"]=="VY_full" and r["tier"]=="base" and r["order"]=="carried_before_fill"),None)
    if not expected or not expected["passed"] or receipt.get("2026_accessed") or receipt.get("holdout_accessed") or receipt.get("paper_live_authorized"):
        raise ValueError("VY_ORACLE_BASE_RECEIPT")
    cash=INITIAL;q=np.zeros(4);n=0;checks=0;events=0;total_cost=total_funding=0.
    with Path(ledger_path).open(newline="") as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames)!=COLS:raise ValueError("VY_ORACLE_LEDGER_COLUMNS")
        for row in reader:
            t=int(row["hour"])
            if t!=n or t>=HOURS:raise ValueError("VY_ORACLE_HOUR_CLOCK")
            v={k:np.asarray(json.loads(row[k]),float) for k in VECTORS}
            for k in VECTORS:
                if v[k].shape!=(4,):raise ValueError("VY_ORACLE_VECTOR_SHAPE_"+k)
            checks+=check(v["open"],d["o"][t],"open",t)
            checks+=check(v["close"],d["c"][t],"close",t)
            checks+=check(v["rate"],d["rate"][t],"rate",t)
            checks+=check(v["lower"],d["mark_lower"][t],"lower",t)
            checks+=check(v["upper"],d["mark_upper"][t],"upper",t)
            checks+=check(float(row["cash_before"]),cash,"cash_before",t)
            gap=float(np.dot(q,d["o"][t]-(d["c"][t-1] if t else d["o"][t])))
            cash+=gap
            checks+=check(float(row["gap_pnl"]),gap,"gap",t)
            funding=0.
            if t%8==0:
                events+=4
                marks=np.where(q*d["rate"][t]>0,d["mark_upper"][t],d["mark_lower"][t])
                funding=-float(np.dot(q,d["rate"][t]*marks))
                cash+=funding
            total_funding+=funding
            checks+=check(float(row["funding"]),funding,"funding",t)
            if t==HOURS-1 or t-1 in CLOCK:
                w=v["target_weight"]
                if t==HOURS-1 and np.any(w):raise ValueError("VY_ORACLE_TERMINAL_TARGET")
                if np.abs(w).sum()>.90+1e-9 or abs(float(w.sum()))>1e-9:
                    raise ValueError("VY_ORACLE_TARGET_RISK")
                newq=w*cash/d["o"][t]
                delta=newq-q
                if np.any((np.abs(delta)>1e-12)&(d["q"][t]<=0)):
                    raise ValueError("VY_ORACLE_ZERO_VOLUME")
                notional=float(np.dot(np.abs(delta),d["o"][t]))
                cost=.001*notional
                cash-=cost
                q=newq
            else:
                if np.any(v["target_weight"]):raise ValueError("VY_ORACLE_UNSCHEDULED_TARGET")
                notional=0.;cost=0.
            checks+=check(float(row["trade_notional"]),notional,"notional",t)
            checks+=check(float(row["cost"]),cost,"cost",t)
            total_cost+=cost
            checks+=check(v["qty"],q,"position",t,atol=1e-9)
            intrahour=float(np.dot(q,d["c"][t]-d["o"][t]))
            cash+=intrahour
            checks+=check(float(row["intrahour_pnl"]),intrahour,"intrahour",t)
            checks+=check(float(row["cash_after"]),cash,"cash_after",t)
            checks+=check(float(row["equity_after"]),cash,"equity_after",t)
            gross=float(np.dot(np.abs(q),d["c"][t]))
            if cash<=0 or gross>cash*(1+1e-8):raise ValueError("VY_ORACLE_HIDDEN_LEVERAGE")
            n+=1
    if n!=HOURS or events!=13524 or np.any(np.abs(q)>1e-10):
        raise ValueError("VY_ORACLE_COMPLETENESS")
    checks+=check(cash,expected["final_equity"],"final_NAV",HOURS)
    checks+=check(total_cost,expected["fees_spread_impact"],"total_cost",HOURS)
    checks+=check(total_funding,expected["signed_funding"],"total_funding",HOURS)
    return {"decision":"PASS_INDEPENDENT_VY_EXPOSED_ACCOUNTING_NOT_VALIDATION",
            "hours":n,"funding_events":events,"independent_identities":checks,
            "final_NAV":cash,"cost":total_cost,"signed_funding":total_funding,
            "2026_accessed":False,"holdout_accessed":False,"paper_live_authorized":False,
            "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","ledger","receipt"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    d=load(a.old_root,a.old_envelope,a.new_root,a.corrected_root)
    result=audit(d,a.ledger,a.receipt)
    print("VY_INDEPENDENT",json.dumps(result,sort_keys=True),flush=True)
