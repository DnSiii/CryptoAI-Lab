#!/usr/bin/env python3
"""CK artifact-only independent 20-cell economic and reproducibility gate.
No CK signal, allocation, risk governor or settlement imports.
"""
from __future__ import annotations
import argparse,glob,json,math
from pathlib import Path
PATHS=("CK_core_only","CK_full","CK_minus_opportunity","CK_minus_RV","CK_minus_stress")
MODES=("immediate",)
FEES=("base","severe")
ORDERS=("carried_before_fill","new_after_fill")
OS=("ubuntu-22.04","ubuntu-24.04")
GRID={(m,f,o) for m in MODES for f in FEES for o in ORDERS}

def near(a,b):
    return math.isclose(float(a),float(b),rel_tol=1e-8,abs_tol=1e-5)

def run(root):
    files=sorted(glob.glob(str(Path(root)/'*'/'*.json')))
    errors=[];by_path={}
    for path in PATHS:
        by_path[path]={}
    for filename in files:
        os=next((s for s in OS if s in Path(filename).parent.name),None)
        try:payload=json.load(open(filename))
        except Exception as exc:
            errors.append(("INVALID_JSON",filename,str(exc)));continue
        p=payload.get("path")
        if os not in OS or p not in PATHS or os in by_path[p]:
            errors.append(("ARTIFACT_INVENTORY",filename));continue
        by_path[p][os]=payload
    if len(files)!=10:errors.append(("FILE_COUNT",len(files)))
    all_source=set()
    reps={}
    for path in PATHS:
        pair=by_path[path]
        if set(pair)!=set(OS):
            errors.append(("OS_MISSING",path));continue
        a,b=(pair[o] for o in OS)
        all_source.update((a.get("source_manifest_sha256"),b.get("source_manifest_sha256")))
        if a.get("source_manifest_sha256")!=b.get("source_manifest_sha256"):
            errors.append(("SOURCK_SHA",path))
        x,y=(z.get("cells",[]) for z in (a,b))
        if len(x)!=4 or len(y)!=4:
            errors.append(("CKLL_COUNT",path));continue
        aa={(z["mode"],z["fee"],z["order"]):z for z in x}
        bb={(z["mode"],z["fee"],z["order"]):z for z in y}
        if set(aa)!=GRID or set(bb)!=GRID:
            errors.append(("GRID",path));continue
        for key in GRID:
            one,two=aa[key],bb[key]
            if one["passed"]!=two["passed"]:
                errors.append(("OS_SURVIVAL",path,key));continue
            if one["passed"]:
                for field in ("final_nav","fees","slippage","funding","turnover",
                              "two_year_cagr","max_drawdown","max_gross_to_nav"):
                    if not near(one[field],two[field]):
                        errors.append(("OS_NUMERIC",path,key,field))
                for yr in ("2023","2024"):
                    if not near(one["annual"][yr]["end_nav"],two["annual"][yr]["end_nav"]):
                        errors.append(("OS_YEAR",path,key,yr))
        reps[path]=aa
    if len(all_source)!=1:errors.append(("CROSS_PATH_SOURCK",len(all_source)))
    survival=sum(c.get("passed",False) for a in reps.values() for c in a.values())
    for path,rows in reps.items():
        for key,c in rows.items():
            if not c.get("passed"):continue
            if (c.get("validation_2025_read") is not False or
                c.get("external_benchmarks_used") is not False or
                c.get("trading_authorized") is not False):
                errors.append(("FIREWALL",path,key))
            if not near(c["final_nav"],c["initial_nav"]*(1+c["net_total_return"])):
                errors.append(("NAV",path,key))
            if not near(c["net_log_growth"],math.log(c["final_nav"]/c["initial_nav"])):
                errors.append(("LOG_GROWTH",path,key))
            if not near(c["two_year_cagr"],(c["final_nav"]/c["initial_nav"])**(365.25/731)-1):
                errors.append(("CAGR",path,key))
            if not near(c["annual"]["2023"]["end_nav"],c["annual"]["2024"]["start_nav"]):
                errors.append(("YEAR_CONTINUITY",path,key))
            if not near(c["annual"]["2024"]["end_nav"],c["final_nav"]):
                errors.append(("YEAR_END",path,key))
            if any(c[x]<-1e-8 for x in ("fees","slippage","turnover")):
                errors.append(("NEGATIVE_COST",path,key))
    full=reps.get("CK_full",{})
    growth={};marginal={}
    for fee in ("base","severe"):
        for order in ORDERS:
            key=("immediate",fee,order)
            c=full.get(key,{})
            growth["|".join(key)]=bool(c.get("passed") and
                all(c["annual"][yr]["net_log_growth"]>0 for yr in ("2023","2024")))
    for book,path in (("Opportunity","CK_minus_opportunity"),
                      ("RelativeValue","CK_minus_RV"),
                      ("StressRecovery","CK_minus_stress")):
        marginal[book]={}
        for key,c in full.items():
            other=reps.get(path,{}).get(key,{})
            if not c.get("passed") or not other.get("passed"):continue
            marginal[book]["|".join(key)]={yr:(
                c["annual"][yr]["net_log_growth"]-
                other["annual"][yr]["net_log_growth"])
                for yr in ("2023","2024")}
    marginal_gates={book:all(
        marginal[book].get(key,{}).get(yr,float("-inf"))>1e-9
        for key in growth for yr in ("2023","2024")) for book in marginal}
    high_growth=all(
        full.get(("immediate",fee,order),{}).get("passed") and
        full[("immediate",fee,order)]["two_year_cagr"]>(.50 if fee=="base" else .30)
        for fee in ("base","severe") for order in ORDERS)
    severe_dd=all(full.get(("immediate","severe",order),{}).get("passed") and full[("immediate","severe",order)]["max_drawdown"]<.45 for order in ORDERS)
    if errors:decision="BLOCK_CK_AUDIT_OR_REPRODUCKBILITY"
    elif survival!=20:decision="REJECT_CK_PHYSICAL_SURVIVAL"
    elif not all(growth.values()) or not all(marginal_gates.values()) or not high_growth or not severe_dd:
        decision="REJECT_CK_HISTORICAL_GROWTH_OR_MARGINAL"
    else:decision="PASS_CK_TRAINING_ONLY_NEEDS_SEPARATE_VALIDATION"
    return {"architecture":"CK","historical_training_only":True,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "errors":errors[:40],"source_manifest_sha256":next(iter(all_source)) if len(all_source)==1 else None,
            "cross_os_reproducible":not errors and len(reps)==5,
            "cells_expected":20,"cells_survived":survival,
            "growth_gates_10k":growth,"high_growth_gate_10k":high_growth,"severe_drawdown_gate_10k":severe_dd,
            "marginal_log_growth_10k":marginal,"marginal_gates_10k":marginal_gates,
            "full_10k_base":full.get(("immediate","base","carried_before_fill")),
            "full_10k_severe":full.get(("immediate","severe","carried_before_fill")),
            "decision":decision}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True)
    p.add_argument("--output",required=True);a=p.parse_args()
    out=run(a.root)
    with open(a.output,"w") as f:json.dump(out,f,indent=2,sort_keys=True,allow_nan=False)
    print("CK_AUDIT",out["decision"],"survived",out["cells_survived"],
          "cross_os",out["cross_os_reproducible"],"errors",out["errors"])
    for key in ("full_10k_base","full_10k_severe"):
        x=out[key]
        if x and x.get("passed"):
            print("CK_FULL",key,"CAGR",x["two_year_cagr"],
                  "2023",x["annual"]["2023"]["net_return"],
                  "2024",x["annual"]["2024"]["net_return"],
                  "DD",x["max_drawdown"],"funding",x["funding"])
    print("CK_GROWTH_GATES",out["growth_gates_10k"])
    print("CK_MARGINAL_GATES",out["marginal_gates_10k"])
    raise SystemExit(2 if out["errors"] else 0)
