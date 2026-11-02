#!/usr/bin/env python3
"""WM preregistered full seven-slot physical exposed training, never live/paper."""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS,source_gate
from wm_beta_residual_engine import targets,books_from_decisions,incidence,synthetic_test,SLOTS
from wl_funding_buffer_physical import simulate,TIERS,ORDERS,HEADER

def run(d,outdir):
    source_gate(d)
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    dec=targets(d);books=books_from_decisions(dec);counts=incidence(dec)
    source={"decision":"PASS_WM_SOURCE_ONLY_NOT_PNL","hours":HOURS,
            "funding_events":int(d["event"].sum()),"decisions":len(dec),
            "sleeve_incidence":counts,"2026_accessed":False,
            "holdout_accessed":False}
    (out/"wm_source.json").write_text(json.dumps(source,indent=2,sort_keys=True)+"\n")
    # This pre-PnL economic-testability gate is immutable.
    insufficient={k:v for k,v in counts.items() if v<30}
    if insufficient:
        result={"architecture":"WM","decision":"REJECT_WM_PRE_PNL_INCIDENCE",
                "insufficient":insufficient,"sleeve_incidence":counts,
                "cells":[],"pnl_computed":False,"paper_live_authorized":False}
        (out/"wm_exposed_physical.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print("WM_DECISION",result["decision"],json.dumps(insufficient),flush=True)
        return result
    cells=[];ledger=None
    for tier in TIERS:
        for order in ORDERS:
            for name,target in books.items():
                keep=(tier=="base" and order=="carried_before_fill" and name=="WM_full")
                r,rows=simulate(d,target,tier,order,record=keep)
                r["book"]=name;cells.append(r)
                if keep:ledger=rows
                print("WM_PHYSICAL",tier,order,name,r.get("passed"),r.get("cagr"),
                      r.get("reason"),r.get("hour"),flush=True)
    failures=[];marginals={}
    for tier in TIERS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["WM_full"]
            marginals[label]={slot:full["log_growth"]-group[other]["log_growth"]
                              for slot,other in (("Opportunity","WM_minus_opportunity"),
                                                 ("Relative_Value","WM_minus_RV"),
                                                 ("Stress_Recovery","WM_minus_stress"))}
            if tier in ("base","severe"):
                if full["cagr"]<=(.80 if tier=="base" else .60):
                    failures.append(label+":cagr")
                if tier=="severe" and full["max_dd"]<=-.45:
                    failures.append(label+":drawdown")
                if tier=="severe" and any(v<=0 for v in full["annual_returns"].values()):
                    failures.append(label+":negative_year")
                for slot,value in marginals[label].items():
                    if value<=0:failures.append(label+":"+slot+":marginal")
    result={"architecture":"WM","decision":"REJECT_WM_EXPOSED_TRAINING" if failures
            else "PASS_WM_EXPOSED_TRAINING_ONLY_NOT_VALIDATED",
            "cells":cells,"failures":failures,"marginals":marginals,
            "sleeve_incidence":counts,"pnl_computed":True,
            "2026_accessed":False,"holdout_accessed":False,
            "account_costs_authenticated":False,
            "exact_exchange_marks_authenticated":False,
            "independent_ledger_audit_pending":True,"paper_live_authorized":False}
    (out/"wm_exposed_physical.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    if ledger:
        with (out/"wm_base_full_hourly_ledger.csv").open("w",newline="") as f:
            w=csv.writer(f,lineterminator="\n");w.writerow(HEADER)
            for row in ledger:
                w.writerow([json.dumps(v.tolist(),separators=(",",":")) if isinstance(v,np.ndarray)
                            else format(v,".16g") if isinstance(v,float) else v for v in row])
    print("WM_DECISION",result["decision"],"failed_gates",len(failures),flush=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):
        p.add_argument("--"+k)
    a=p.parse_args()
    if a.self_test:print(json.dumps(synthetic_test(),sort_keys=True))
    else:
        for k in ("old_root","old_envelope","new_root","corrected_root","out_dir"):
            if not getattr(a,k):p.error("--"+k.replace("_","-")+" required")
        run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
