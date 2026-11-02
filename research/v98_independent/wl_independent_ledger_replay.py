#!/usr/bin/env python3
"""WL independent hourly ledger replay: arithmetic only, no strategy imports."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
import numpy as np
HOURS=27048
def check_rows(rows,mutate=False):
    prev_q=np.zeros(4);prev_close=None;prev_cash=10000.
    count=0;max_error=0.;trims=0;total_funding=0.;total_fees=0.
    for row in rows:
        t=int(row["hour"])
        if t!=count:raise ValueError("WL_ORACLE_HOUR_SEQUENCE")
        q=np.array(json.loads(row["qty"]),dtype=float)
        op=np.array(json.loads(row["open"]),dtype=float)
        cl=np.array(json.loads(row["close"]),dtype=float)
        rate=np.array(json.loads(row["rate"]),dtype=float)
        lower=np.array(json.loads(row["lower"]),dtype=float)
        upper=np.array(json.loads(row["upper"]),dtype=float)
        if any(x.shape!=(4,) for x in (q,op,cl,rate,lower,upper)):
            raise ValueError("WL_ORACLE_ARRAY_GEOMETRY")
        before=float(row["cash_before"]);after=float(row["cash_after"])
        gap=float(np.dot(prev_q,op-(prev_close if prev_close is not None else op)))
        funding_qty=prev_q # carried-before-fill base ledger
        if t%8==0:
            mark=np.where(funding_qty*rate>0,upper,lower)
            funding=-float(np.dot(funding_qty,rate*mark))
        else:funding=0.
        notional=float(np.dot(np.abs(q-prev_q),op))
        fees=.001*notional
        intrahour=float(np.dot(q,cl-op))
        if mutate and t==min(900,HOURS-1):after+=1.
        expected=before+gap+funding-fees+intrahour
        vals=((before,prev_cash),(float(row["gap"]),gap),
              (float(row["funding"]),funding),(float(row["fees"]),fees),
              (float(row["intrahour"]),intrahour),
              (float(row["trade_notional"]),notional),(after,expected))
        for a,b in vals:
            err=abs(a-b);max_error=max(max_error,err)
            if not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-6):
                raise ValueError("WL_ORACLE_LEDGER_MISMATCH_AT_"+str(t))
        if float(np.dot(np.abs(q),cl))>after*(1+1e-8):
            raise ValueError("WL_ORACLE_CLOSE_LEVERAGE_"+str(t))
        trims+=int(row["governor_trim"])
        total_funding+=funding;total_fees+=fees
        prev_cash=after;prev_q=q;prev_close=cl;count+=1
    if count==0:raise ValueError("WL_ORACLE_EMPTY")
    return {"hours_reconciled":count,"complete_history":count==HOURS,
            "max_abs_arithmetic_error":max_error,"governor_trims":trims,
            "independent_signed_funding":total_funding,
            "independent_fees":total_fees,"terminal_cash":prev_cash}
def run(outdir):
    out=Path(outdir)
    path=out/"wl_base_full_hourly_ledger.csv"
    receipt=json.loads((out/"wl_exposed_physical.json").read_text())
    with path.open(newline="") as f:rows=list(csv.DictReader(f))
    audit=check_rows(rows)
    tamper_detected=False
    if len(rows)>900:
        try:check_rows(rows,mutate=True)
        except ValueError as e:
            tamper_detected=str(e).startswith("WL_ORACLE_LEDGER_MISMATCH_AT_")
    if len(rows)>900 and not tamper_detected:raise ValueError("WL_ORACLE_TAMPER_UNDETECTED")
    base=next(x for x in receipt["cells"]
              if x["book"]=="WL_full" and x["tier"]=="base"
              and x["order"]=="carried_before_fill")
    if base["passed"] and (not audit["complete_history"]
        or not math.isclose(base["final_equity"],audit["terminal_cash"],rel_tol=1e-10,abs_tol=1e-6)
        or not math.isclose(base["signed_funding"],audit["independent_signed_funding"],rel_tol=1e-10,abs_tol=1e-6)
        or not math.isclose(base["fees_spread_impact"],audit["independent_fees"],rel_tol=1e-10,abs_tol=1e-6)):
        raise ValueError("WL_ORACLE_FULL_RECEIPT_MISMATCH")
    audit.update({"decision":"PASS_WL_INDEPENDENT_LEDGER_REPLAY_NOT_VALIDATION",
                  "tamper_detected":tamper_detected,
                  "2026_accessed":False,"holdout_accessed":False,
                  "exact_marks_authenticated":False,"account_costs_authenticated":False,
                  "paper_live_authorized":False})
    (out/"wl_independent_oracle.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    print("WL_ORACLE",json.dumps(audit,sort_keys=True),flush=True)
    return audit
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out-dir",required=True)
    a=p.parse_args();run(a.out_dir)
