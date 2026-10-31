#!/usr/bin/env python3
"""Independent read-only OV frozen economic gate audit.
Never imports OV strategy or physical runner; does not run new PnL or tune.
"""
import json,math
from pathlib import Path

BOOKS=("OV_full","OV_core_only","OV_minus_opportunity","OV_minus_RV","OV_minus_stress")
TIERS=("base","severe","supersevere")
ORDERS=("carried_before_fill","new_after_fill")
ABLATIONS=(("Opportunity","OV_minus_opportunity"),("Relative_Value","OV_minus_RV"),
           ("Stress_Recovery","OV_minus_stress"))

def audit(path):
    data=json.loads(Path(path).read_text())
    if data["decision"]!="REJECT_OV_TRAINING" or data["architecture"]!="OV":
        raise ValueError("OV_FROZEN_DECISION")
    if data["original_workflow_run"]!=41240698895 or data["original_prereg_commit"]!="a01fed933685d9d0fb92e16c752963e8f8f52b5f":
        raise ValueError("OV_FROZEN_PROVENANCE")
    if data["source"]["hours"]!=27048 or data["source"]["events"]!=13524 or data["weekly_decisions"]!=157:
        raise ValueError("OV_FROZEN_SOURCE_CLOCK")
    if not data["training_only"] or not data["year_2025_exposed"] or data["exact_event_mark_attested"] or data["holdout_accessed"] or data["benchmarks_accessed"] or data["paper_or_live_authorized"]:
        raise ValueError("OV_FROZEN_ACCESS_CONTRACT")
    o=data["independent_decision_oracle"];f=data["independent_fill_oracle"];cash=data["audit"]
    if o["independent_weekly_decisions"]!=157 or o["signal_and_allocation_mismatches"]!=0 or o["max_absolute_weight_error"]>1e-10:
        raise ValueError("OV_FROZEN_DECISION_ORACLE")
    if f["hours"]!=26303 or f["independent_fee_slippage_funding_mismatches"] or cash["hours_reconciled"]!=26303 or cash["cash_identity_mismatches"]:
        raise ValueError("OV_FROZEN_CASH_ORACLE")
    cells={(c["tier"],c["order"],c["book"]):c for c in data["cells"]}
    expected={(tier,order,book) for tier in TIERS for order in ORDERS for book in BOOKS}
    if len(data["cells"])!=30 or set(cells)!=expected or not all(c["passed"] for c in cells.values()):
        raise ValueError("OV_FROZEN_PHYSICAL_CELLS")
    fail=[];marginal_errors=0;max_marginal_error=0.
    for tier in TIERS:
        for order in ORDERS:
            group={book:cells[(tier,order,book)] for book in BOOKS}
            full=group["OV_full"]
            key=tier+"/"+order
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):fail.append(key+":CAGR")
            if full["turnover"]>1_000_000:fail.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:fail.append(key+":DD")
                if any(value<=0 for value in full["year_returns"].values()):fail.append(key+":annual")
            for slot,book in ABLATIONS:
                delta=math.log(full["final_equity"]/group[book]["final_equity"])
                recorded=data["marginals"][key][slot]
                err=abs(delta-recorded)
                max_marginal_error=max(max_marginal_error,err)
                if err>1e-10:marginal_errors+=1
                if delta<=.02:fail.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    yearly=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if yearly<-.03:fail.append(key+":"+slot+":"+year+":annual_marginal")
    if marginal_errors or sorted(fail)!=sorted(data["gate_failures"]):
        raise ValueError("OV_FROZEN_INDEPENDENT_GATE_MISMATCH")
    if len(fail)!=32:raise ValueError("OV_FROZEN_EXPECTED_FAILURES")
    return {"decision":"PASS_INDEPENDENT_OV_FROZEN_REJECTION_AUDIT_NOT_ENGINE",
            "cells_verified":len(cells),"economic_failures_rederived":len(fail),
            "independent_decisions":157,"independent_hours":26303,
            "max_marginal_log_error":max_marginal_error,
            "training_only":True,"exact_event_marks_attested":False,
            "paper_or_live_authorized":False}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--receipt",default="ov_full_training_frozen_result_20261031.json")
    args=p.parse_args()
    print(json.dumps(audit(args.receipt),sort_keys=True))
