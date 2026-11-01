#!/usr/bin/env python3
"""Independent PT receipt arithmetic and preregistered economic gate replay; no PT imports."""
import copy,json,math,sys
from pathlib import Path

BOOKS={"PT_full","PT_core_only","PT_minus_opportunity","PT_minus_RV","PT_minus_stress"}
TIERS=("base","severe","supersevere")
ORDERS=("carried_before_fill","new_after_fill")
SLOTS=(("Opportunity","PT_minus_opportunity"),
       ("Relative_Value","PT_minus_RV"),("Stress_Recovery","PT_minus_stress"))

def audit(r):
    assert r["architecture"]=="PT"
    assert r["preregistration"]=="pt_residual_liquidity_prereg_20261101.md"
    assert r["2025_exposed_training_only"] is True
    assert r["exact_event_mark_attested"] is False
    for k in ("2026_plus_accessed","holdout_accessed","external_benchmarks_accessed",
              "paper_or_live_authorized"):
        assert r[k] is False
    assert r["weekly_decisions"]==157
    assert r["source"]["events"]==13524
    oracle=r["independent_decision_oracle"]
    assert oracle["decisions"]==157 and oracle["books"]==5
    assert oracle["mismatches"]==0 and oracle["independent_implementation"] is True
    accounting=r["independent_accounting"]
    fills=r["independent_fills"]
    assert accounting is not None and accounting["hours_reconciled"]==26303
    assert accounting["cash_identity_mismatches"]==0
    assert fills is not None and fills["hours"]==26303
    assert fills["independent_fee_slippage_funding_mismatches"]==0
    rows=r["cells"]
    assert len(rows)==30
    index={(row["tier"],row["order"],row["book"]):row for row in rows}
    assert len(index)==30
    assert set(index)=={(tier,order,book) for tier in TIERS for order in ORDERS for book in BOOKS}
    failures=[];marginals={};max_error=0.;checks=0
    for tier in TIERS:
        for order in ORDERS:
            group={book:index[(tier,order,book)] for book in BOOKS}
            for row in group.values():
                if not row["passed"]:continue
                equity=float(row["final_equity"])
                assert equity>0 and math.isfinite(equity)
                growth=math.log(equity/10000.)
                cagr=(equity/10000.)**(365.25/1096.)-1
                error=max(abs(growth-row["log_growth"]),abs(cagr-row["cagr"]))
                max_error=max(max_error,error);checks+=2
                assert error<=1e-10
                assert all(math.isfinite(v) for v in row["year_returns"].values())
                assert row["max_pretrade_post_gross_fraction"]<=1.0000001
                assert row["min_intrabar_equity"]>0
                assert 0<=row["positive_days"]<=row["daily_count"]
                assert row["trade_pf_payoff_win_rate_independent"] is False
            label=tier+"/"+order
            if not all(row["passed"] for row in group.values()):
                failures.append(label+":physical");continue
            full=group["PT_full"]
            marginals[label]={slot:full["log_growth"]-group[book]["log_growth"]
                              for slot,book in SLOTS}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(label+":CAGR")
            if full["turnover"]>1000000:failures.append(label+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(label+":drawdown")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(label+":annual")
            for slot,book in SLOTS:
                if marginals[label][slot]<=.02:failures.append(label+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    delta=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if delta<-.03:failures.append(label+":"+slot+":"+year+":annual_marginal")
    if accounting is None or accounting["cash_identity_mismatches"]:failures.append("independent_hourly_accounting")
    if fills is None or fills["independent_fee_slippage_funding_mismatches"]:failures.append("independent_fills_and_funding")
    assert failures==r["gate_failures"],(failures,r["gate_failures"])
    for label,slots in marginals.items():
        for slot,val in slots.items():
            assert abs(val-r["marginals"][label][slot])<1e-10
    expected="REJECT_PT_TRAINING" if failures else "PASS_PROVISIONAL_PT_TRAINING_NOT_VALIDATED"
    assert r["decision"]==expected
    return {"decision":"PASS_PT_INDEPENDENT_RECEIPT_RECONCILIATION_NOT_ENGINE",
            "cells":len(rows),"arithmetic_checks":checks,"gate_failures_rederived":len(failures),
            "max_arithmetic_error":max_error,"engine_decision":r["decision"],
            "training_only":True,"exact_mark_origin_attested":False}

def tamper_checks(r):
    mutations=(
        lambda x:x["cells"][0].__setitem__("cagr",x["cells"][0].get("cagr",0)+.05),
        lambda x:x["gate_failures"].append("invented_gate"),
        lambda x:x["source"].__setitem__("events",9999),
        lambda x:x.__setitem__("exact_event_mark_attested",True),
    )
    rejected=0
    for change in mutations:
        bad=copy.deepcopy(r);change(bad)
        try:audit(bad)
        except (AssertionError,KeyError,ValueError):rejected+=1
        else:raise AssertionError("PT_TAMPER_ACCEPTED")
    return rejected

if __name__=="__main__":
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path("pt_full_training_result.json")
    r=json.loads(path.read_text())
    out=audit(r)
    out["tamper_cases_rejected"]=tamper_checks(r)
    print(json.dumps(out,sort_keys=True))
