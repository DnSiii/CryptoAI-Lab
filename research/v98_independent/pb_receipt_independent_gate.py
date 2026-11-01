#!/usr/bin/env python3
"""Independent PB receipt arithmetic and binding economic gate verifier.
Reads only a pinned immutable PB training result JSON; never imports strategy or reselects it.
"""
import json,math,sys
from pathlib import Path
EXPECTED_BOOKS={"PB_full","PB_core_only","PB_minus_opportunity","PB_minus_RV","PB_minus_stress"}
TIERS=("base","severe","supersevere")
ORDERS=("carried_before_fill","new_after_fill")
SLOTS=(("Opportunity","PB_minus_opportunity"),("Relative_Value","PB_minus_RV"),
       ("Stress_Recovery","PB_minus_stress"))

def audit(receipt):
    assert receipt["architecture"]=="PB" and receipt["training_only"] and receipt["year_2025_exposed"]
    assert not any(receipt[k] for k in ("holdout_accessed","benchmarks_accessed","paper_or_live_authorized","exact_event_mark_attested"))
    assert receipt["weekly_decisions"]==157 and receipt["source"]["events"]==13524
    assert receipt["independent_decision_oracle"]["signal_and_allocation_mismatches"]==0
    assert receipt["audit"]["cash_identity_mismatches"]==0
    assert receipt["independent_fill_oracle"]["independent_fee_slippage_funding_mismatches"]==0
    rows=receipt["cells"]
    assert len(rows)==30
    observed={(r["tier"],r["order"],r["book"]):r for r in rows}
    expected={(tier,order,book) for tier in TIERS for order in ORDERS for book in EXPECTED_BOOKS}
    assert len(observed)==30 and set(observed)==expected
    errors=0;max_error=0.;failures=[];marginals={}
    for tier in TIERS:
        for order in ORDERS:
            group={book:observed[tier,order,book] for book in EXPECTED_BOOKS}
            for row in group.values():
                assert row["tier"]==tier and row["order"]==order
                if row["passed"]:
                    eq=float(row["final_equity"])
                    assert math.isfinite(eq) and eq>0
                    growth=math.log(eq/10000.)
                    cagr=(eq/10000.)**(365.25/1096.)-1
                    err=max(abs(growth-row["log_growth"]),abs(cagr-row["cagr"]))
                    max_error=max(max_error,err)
                    if err>1e-10:errors+=1
                    assert all(math.isfinite(v) for v in row["year_returns"].values())
            key=tier+"/"+order
            if not all(row["passed"] for row in group.values()):
                failures.append(key+":physical");continue
            full=group["PB_full"]
            marginals[key]={slot:full["log_growth"]-group[book]["log_growth"] for slot,book in SLOTS}
            if tier=="supersevere":continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(key+":CAGR")
            if full["turnover"]>1_000_000:failures.append(key+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(key+":DD")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(key+":annual")
            for slot,book in SLOTS:
                if marginals[key][slot]<=.02:failures.append(key+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    annual_diff=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if annual_diff<-.03:failures.append(key+":"+slot+":"+year+":annual_marginal")
    if receipt["audit"]["cash_identity_mismatches"]:failures.append("independent_accounting")
    if receipt["independent_fill_oracle"]["independent_fee_slippage_funding_mismatches"]:
        failures.append("independent_fills")
    assert errors==0,errors
    assert failures==receipt["gate_failures"],{"expected":failures,"recorded":receipt["gate_failures"]}
    assert receipt["decision"]==("REJECT_PB_TRAINING" if failures else "PASS_PROVISIONAL_PB_TRAINING_NOT_VALIDATED")
    for key,slots in marginals.items():
        for slot,v in slots.items():
            assert abs(v-receipt["marginals"][key][slot])<1e-10
    return {"decision":"PASS_INDEPENDENT_PB_RECEIPT_RECONCILIATION_NOT_ENGINE",
            "cells":len(rows),"arithmetic_checks":len([r for r in rows if r["passed"]])*2,
            "gate_failures_rederived":len(failures),"max_arithmetic_error":max_error,
            "engine_decision":receipt["decision"],"training_only":True}

if __name__=="__main__":
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path("pb_full_training_result.json")
    print(json.dumps(audit(json.loads(path.read_text())),sort_keys=True))
