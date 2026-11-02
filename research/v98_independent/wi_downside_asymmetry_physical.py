#!/usr/bin/env python3
"""WI 30-cell exposed 2023-25 physical training; WG reusable ledger arithmetic ONLY, no WG alpha."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
from vy_cross_sectional_spread import HOURS,source_gate
from wg_funding_inventory_physical import simulate,TIERS,ORDERS,HEADER
from wi_downside_asymmetry import targets,books,incidence,SLOTS,CLOCK
def run(d,outdir):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    source_gate(d);dec=targets(d);counts=incidence(dec)
    failures=[k for k in SLOTS[1:] if counts[k]<30]
    source={"decision":"REJECT_WI_PRE_PNL_INCIDENCE" if failures else "PASS_WI_SOURCE_NOT_PNL",
            "hours":HOURS,"funding_events":int(d["event"].sum()),"decisions":len(CLOCK),
            "sleeve_incidence":counts,"minimum_optional_incidence":30,
            "2026_accessed":False,"holdout_accessed":False}
    (out/"wi_source.json").write_text(json.dumps(source,indent=2,sort_keys=True)+"\n")
    print("WI_SOURCE",json.dumps(source,sort_keys=True),flush=True)
    if failures:return {"decision":"REJECT_WI_PRE_PNL_INCIDENCE","failures":failures}
    b=books(d);cells=[];ledger=None
    for tier in TIERS:
        for order in ORDERS:
            for name,tgt in b.items():
                keep=tier=="base" and order=="carried_before_fill" and name=="WI_full"
                r,rows=simulate(d,tgt,tier,order,record=keep)
                r["book"]=name;cells.append(r)
                if keep:ledger=rows
                print("WI_CELL",tier,order,name,r.get("passed"),r.get("cagr"),r.get("reason"),flush=True)
    failures=[];marginals={}
    for tier in TIERS:
        for order in ORDERS:
            group={x["book"]:x for x in cells if x["tier"]==tier and x["order"]==order}
            label=tier+"/"+order
            if not all(x["passed"] for x in group.values()):
                failures.append(label+":survival");continue
            full=group["WI_full"]
            marginals[label]={slot:full["log_growth"]-group[other]["log_growth"]
                for slot,other in (("Opportunity","WI_minus_opportunity"),
                                   ("Relative_Value","WI_minus_RV"),
                                   ("Stress_Recovery","WI_minus_stress"))}
            if tier in ("base","severe"):
                if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(label+":cagr")
                if tier=="severe" and full["max_dd"]<=-.45:failures.append(label+":drawdown")
                if tier=="severe" and any(x<=0 for x in full["annual_returns"].values()):
                    failures.append(label+":annual")
                for slot,v in marginals[label].items():
                    if v<=.02:failures.append(label+":"+slot+":marginal")
    receipt={"architecture":"WI","source":source,"cells":cells,"marginals":marginals,
             "failures":failures,"decision":"REJECT_WI_EXPOSED_TRAINING" if failures else "PASS_WI_EXPOSED_TRAINING_ONLY_NOT_VALIDATED",
             "independent_physical_audit_pending":True,
             "account_costs_authenticated":False,"exact_exchange_marks_authenticated":False,
             "2026_accessed":False,"holdout_accessed":False,"benchmarks_accessed":False,
             "paper_live_authorized":False}
    (out/"wi_exposed_physical.json").write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n")
    if ledger is not None:
        with (out/"wi_base_full_hourly_ledger.csv").open("w",newline="") as f:
            w=csv.writer(f,lineterminator="\n");w.writerow(HEADER)
            for row in ledger:
                w.writerow([json.dumps(v.tolist(),separators=(",",":")) if isinstance(v,np.ndarray)
                            else format(v,".16g") if isinstance(v,float) else v for v in row])
    print("WI_DECISION",receipt["decision"],"failures",len(failures),flush=True)
    return receipt
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("old-root","old-envelope","new-root","corrected-root","out-dir"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    run(load(a.old_root,a.old_envelope,a.new_root,a.corrected_root),a.out_dir)
