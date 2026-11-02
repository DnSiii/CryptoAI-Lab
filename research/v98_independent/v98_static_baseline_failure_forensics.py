#!/usr/bin/env python3
"""Independent closed-form funding/margin forensic for fixed V98 static controls.

No strategy imports, no alpha, no PnL validation or execution approval.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS, source_gate

BOOKS={
    "cash":(0.,0.,0.,0.),"btc_80":(.80,0.,0.,0.),
    "eth_80":(0.,.80,0.,0.),"bnb_80":(0.,0.,.80,0.),
    "sol_80":(0.,0.,0.,.80),"equal_20":(.20,.20,.20,.20),
}
TIERS={"base":.001,"severe":.002,"supersevere":.0035}
ORDERS=("carried_before_fill","new_after_fill")
FIRST=744

def independent_closed_form(d,book,tier,order):
    if book not in BOOKS or tier not in TIERS or order not in ORDERS:
        raise ValueError("STATIC_FORENSIC_CONTRACT")
    weights=np.array(BOOKS[book],float)
    q=10000.*weights/d["o"][FIRST]
    initial_notional=float(np.dot(np.abs(q),d["o"][FIRST]))
    initial_fee=TIERS[tier]*initial_notional
    buffer=10000.-initial_fee-initial_notional
    cumulative_funding=0.;first=None
    for t in range(FIRST,HOURS,8):
        # No positions existed at the initial funding event if carried-before-fill.
        if t==FIRST and order=="carried_before_fill":
            f=0.
        else:
            marks=np.where(q*d["rate"][t]>0,d["mark_upper"][t],d["mark_lower"][t])
            f=-float(np.dot(q,d["rate"][t]*marks))
        before=buffer
        buffer+=f
        cumulative_funding+=f
        if buffer< -1e-7 or (book!="cash" and buffer<=0):
            first={"hour":t,"buffer_before_funding":before,
                   "funding_at_failure":f,"buffer_after_funding":buffer,
                   "cumulative_signed_funding":cumulative_funding,
                   "funding_only_trigger":before>=-1e-7 and f<0}
            break
    if first is None:
        terminal_notional=float(np.dot(np.abs(q),d["o"][HOURS-1]))
        exit_fee=TIERS[tier]*terminal_notional
        final=10000.-initial_fee+float(np.dot(q,d["o"][HOURS-1]-d["o"][FIRST]))+cumulative_funding-exit_fee
    else:
        final=None
    return {"book":book,"tier":tier,"order":order,"first_gross_violation":first,
            "independent_terminal_equity":final,
            "independent_funding":cumulative_funding,
            "initial_fee":initial_fee,"2026_accessed":False}

def run(d,outdir):
    source_gate(d)
    out=Path(outdir)
    receipt=json.loads((out/"static_diagnostic.json").read_text())
    if len(receipt.get("cells",[]))!=36:
        raise ValueError("STATIC_FORENSIC_CELLS")
    reports=[]
    for cell in receipt["cells"]:
        x=independent_closed_form(d,cell["book"],cell["tier"],cell["order"])
        failure=x["first_gross_violation"]
        if cell["passed"]:
            if failure is not None:
                raise ValueError("STATIC_FORENSIC_UNEXPECTED_VIOLATION")
            if not math.isclose(x["independent_terminal_equity"],cell["final_equity"],rel_tol=1e-10,abs_tol=1e-6):
                raise ValueError("STATIC_FORENSIC_FINAL_EQUITY_MISMATCH")
            if not math.isclose(x["independent_funding"],cell["signed_funding"],rel_tol=1e-10,abs_tol=1e-6):
                raise ValueError("STATIC_FORENSIC_FUNDING_MISMATCH")
            x["decision"]="PASS_STATIC_CLOSED_FORM_TERMINAL_RECONCILIATION_NOT_ENGINE"
        else:
            if cell["reason"]!="CASH_OR_HIDDEN_LEVERAGE":
                x["decision"]="UNHANDLED_OTHER_SURVIVAL_REASON"
                raise ValueError("STATIC_FORENSIC_UNEXPECTED_SURVIVAL_REASON")
            if failure is None or failure["hour"]!=cell["hour"] or not failure["funding_only_trigger"]:
                raise ValueError("STATIC_FORENSIC_FAILURE_CAUSE_MISMATCH")
            x["decision"]="PASS_STATIC_CLOSED_FORM_FUNDING_CAUSE_RECONCILIATION_NOT_ENGINE"
        reports.append(x)
        print("STATIC_FORENSIC",json.dumps(x,sort_keys=True),flush=True)
    result={"decision":"PASS_STATIC_36_CELL_INDEPENDENT_CLOSED_FORM_NOT_ENGINE",
            "cells_reconciled":len(reports),
            "funding_caused_gross_failures":sum(not x["independent_terminal_equity"] for x in reports),
            "source_mark_type":"conservative_envelope_not_exact_exchange_settlement",
            "account_costs_authenticated":False,"exchange_marks_authenticated":False,
            "2026_accessed":False,"holdout_accessed":False,"paper_live_authorized":False,
            "cells":reports}
    (out/"static_failure_forensics.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("STATIC_FORENSIC_DECISION",result["decision"],flush=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("old-root","old-envelope","new-root","corrected-root","out-dir"):
        p.add_argument("--"+name,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
