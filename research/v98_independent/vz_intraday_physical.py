#!/usr/bin/env python3
"""V98 VZ exposed-training economic test; generic cash ledger reused, NEVER VY signals."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_physical import simulate,TIERS,ORDERS,HEADER
from vz_intraday_reversal import targets,books,incidence,SLOTS,CLOCK

def run(d,outdir):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    dec=targets(d)
    counts=incidence(dec)
    threshold=int(.10*len(CLOCK))
    source={"decision":"PASS_VZ_SOURCE_INCIDENCE_NOT_PNL",
            "decisions":len(CLOCK),"sleeve_incidence":counts,
            "min_incidence":threshold,"hours":len(d["time"]),
            "native_funding_events":int(d["event"].sum()),
            "2026_accessed":False,"holdout_accessed":False,"pnl_computed":False}
    failures=[k for k in SLOTS[1:] if counts[k]<threshold]
    if failures:source["decision"]="REJECT_VZ_PRE_PNL_INCIDENCE"
    (out/"vz_source.json").write_text(json.dumps(source,indent=2,sort_keys=True)+"\n")
    print("VZ_SOURCE",json.dumps(source,sort_keys=True),flush=True)
    if failures:
        return {"decision":"REJECT_VZ_PRE_PNL_INCIDENCE","failures":failures}
    book=books(d)
    cells=[];ledger=None
    for tier in TIERS:
        for order in ORDERS:
            for name,target in book.items():
                frozen=tier=="base" and order==ORDERS[0] and name=="VZ_full"
                result,rows=simulate(d,target,tier,order,record=frozen)
                result["book"]=name;cells.append(result)
                if frozen:ledger=rows
                print("VZ_PHYSICAL",tier,order,name,result.get("passed"),
                      result.get("cagr"),result.get("reason"),flush=True)
    failures=[];marginals={}
    for tier in TIERS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["VZ_full"]
            marginals[label]={slot:full["log_growth"]-group[other]["log_growth"]
                for slot,other in (("Opportunity","VZ_minus_opportunity"),
                                   ("Relative_Value","VZ_minus_RV"),
                                   ("Stress_Recovery","VZ_minus_stress"))}
            if tier in ("base","severe"):
                if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(label+":cagr")
                if tier=="severe" and full["max_dd"]<=-.45:failures.append(label+":dd")
                if tier=="severe" and any(x<=0 for x in full["annual_returns"].values()):
                    failures.append(label+":annual")
                for slot,v in marginals[label].items():
                    if v<=.02:failures.append(label+":"+slot+":marginal")
    receipt={"architecture":"VZ","source":source,"cells":cells,"marginals":marginals,
             "failures":failures,"decision":"REJECT_VZ_EXPOSED_TRAINING" if failures else "PASS_VZ_EXPOSED_TRAINING_ONLY_NOT_VALIDATED",
             "independent_physical_audit_pending":True,
             "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False,
             "2026_accessed":False,"holdout_accessed":False,
             "benchmarks_accessed":False,"paper_live_authorized":False}
    (out/"vz_exposed_physical.json").write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
    if ledger is not None:
        with (out/"vz_base_full_hourly_ledger.csv").open("w",newline="") as handle:
            writer=csv.writer(handle,lineterminator="\n");writer.writerow(HEADER)
            for row in ledger:
                writer.writerow([json.dumps(v.tolist(),separators=(",",":")) if isinstance(v,np.ndarray)
                                 else format(v,".16g") if isinstance(v,float) else v for v in row])
    print("VZ_EXPOSED_DECISION",receipt["decision"],len(failures),flush=True)
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
