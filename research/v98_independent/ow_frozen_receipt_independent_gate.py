#!/usr/bin/env python3
"""V98 OW post-freeze independent read-only receipt arithmetic and gate audit.
Does not import OW signals, allocator, physical runner, or recompute strategy PnL.
"""
import json,math
from pathlib import Path

BOOKS=("OW_full","OW_core_only","OW_minus_opportunity","OW_minus_RV","OW_minus_stress")
TIERS=("base","severe","supersevere")
ORDERS=("carried_before_fill","new_after_fill")
ABLATIONS=(("Opportunity","OW_minus_opportunity"),("Relative_Value","OW_minus_RV"),
           ("Stress_Recovery","OW_minus_stress"))
COSTS={"base":(.0004,.0002),"severe":(.001,.001),"supersevere":(.0015,.002)}

def audit(path):
    data=json.loads(Path(path).read_text())
    if data["decision"]!="REJECT_OW_TRAINING" or data["architecture"]!="OW":
        raise ValueError("OW_FROZEN_DECISION")
    if (data["original_workflow_run"]!=41245178372
        or data["original_prereg_commit"]!="95aad8c5bd57f76b61dd9490c4da55f72f6ed073"
        or data["original_engine_commit"]!="7354065288d4bbecab710051eada8fd9d9d0382c"
        or data["original_artifact_id"]!=13058542416):
        raise ValueError("OW_FROZEN_PROVENANCE")
    if data["source"]["hours"]!=27048 or data["source"]["events"]!=13524 or data["weekly_decisions"]!=157:
        raise ValueError("OW_FROZEN_SOURCE_CLOCK")
    if (not data["training_only"] or not data["year_2025_exposed"]
        or data["exact_event_mark_attested"] or data["holdout_accessed"]
        or data["benchmarks_accessed"] or data["paper_or_live_authorized"]):
        raise ValueError("OW_FROZEN_ACCESS")
    o=data["independent_decision_oracle"];f=data["independent_fill_oracle"];cash=data["audit"]
    if o["decisions"]!=157 or o["books"]!=5 or o["signal_and_allocation_mismatches"]!=0 or o["max_weight_error"]>1e-10:
        raise ValueError("OW_FROZEN_ORACLE")
    if (f["hours"]!=26303 or f["independent_fee_slippage_funding_mismatches"]
        or cash["hours_reconciled"]!=26303 or cash["cash_identity_mismatches"]):
        raise ValueError("OW_FROZEN_CASH")
    cells={(c["tier"],c["order"],c["book"]):c for c in data["cells"]}
    expected={(tier,order,book) for tier in TIERS for order in ORDERS for book in BOOKS}
    if len(data["cells"])!=30 or set(cells)!=expected or not all(c["passed"] for c in cells.values()):
        raise ValueError("OW_FROZEN_PHYSICAL")
    failures=[];max_error=0.;cost_checks=0
    for tier in TIERS:
        fee,slip=COSTS[tier]
        for order in ORDERS:
            group={book:cells[(tier,order,book)] for book in BOOKS}
            for book,c in group.items():
                final=c["final_equity"]
                if not math.isfinite(final) or final<=0:raise ValueError("OW_FROZEN_EQUITY")
                for label,expected_value in (
                    ("log_growth",math.log(final/10000.)),
                    ("cagr",(final/10000.)**(365.25/1096.)-1),
                    ("fees",c["turnover"]*fee),
                    ("slippage",c["turnover"]*slip)):
                    error=abs(c[label]-expected_value)
                    max_error=max(max_error,error)
                    if error>max(1e-8,abs(expected_value)*1e-10):
                        raise ValueError("OW_FROZEN_ARITHMETIC_"+label)
                    cost_checks+=1
            full=group["OW_full"];key=tier+"/"+order
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in ABLATIONS:
                marginal=math.log(full["final_equity"]/group[book]["final_equity"])
                recorded=data["marginals"][key][slot]
                if abs(marginal-recorded)>1e-10:raise ValueError("OW_FROZEN_MARGINAL_ARITHMETIC")
                if marginal<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    annual=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if annual<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if sorted(failures)!=sorted(data["gate_failures"]) or len(failures)!=24:
        raise ValueError("OW_FROZEN_GATE_MISMATCH")
    return {"decision":"PASS_INDEPENDENT_OW_FROZEN_REJECTION_AUDIT_NOT_ENGINE",
            "physical_cells":30,"economic_failures_rederived":24,
            "cost_and_growth_identity_checks":cost_checks,
            "max_arithmetic_error":max_error,
            "independent_decisions":157,"independent_hours":26303,
            "training_only":True,"exact_event_marks_attested":False,
            "paper_or_live_authorized":False}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--receipt",default="ow_full_training_frozen_result_20261031.json")
    args=p.parse_args()
    print(json.dumps(audit(args.receipt),sort_keys=True))
