#!/usr/bin/env python3
"""BX independent artifact-only 90-cell reconciliation and ringfence invariance.
No BX source, allocator, execution, or governor imports.
"""
from __future__ import annotations
import argparse,glob,json,math
from collections import defaultdict
from pathlib import Path
PATHS=("BX_core_only","BX_full","BX_minus_opportunity","BX_minus_RV","BX_minus_stress")
MODES=("immediate","capacity_1m","capacity_10m")
FEES=("base","severe","supersevere")
ORDERS=("carried_before_fill","new_after_fill")
OS=("ubuntu-22.04","ubuntu-24.04")
GRID={(m,f,o) for m in MODES for f in FEES for o in ORDERS}
ACTIVE={"BX_core_only":(0,),"BX_full":(0,1,2,3),
        "BX_minus_opportunity":(0,2,3),"BX_minus_RV":(0,1,3),
        "BX_minus_stress":(0,1,2)}
def close(a,b):
    return math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-5)
def run(root):
    files=sorted(glob.glob(str(Path(root)/'*'/'*.json')))
    errors=[];groups=defaultdict(dict)
    for file in files:
        artifact=Path(file).parent.name
        os=next((s for s in OS if s in artifact),None)
        a=json.load(open(file));p=a.get("path")
        if not os or p not in PATHS or os in groups[p]:
            errors.append(("BAD_ARTIFACT",str(file)));continue
        groups[p][os]=a
    if len(files)!=10 or set(groups)!=set(PATHS):
        errors.append(("INVENTORY",len(files),sorted(groups)))
    reps={}
    for p in PATHS:
        if set(groups.get(p,{}))!=set(OS):
            errors.append(("OS_MISSING",p));continue
        a,b=(groups[p][s] for s in OS)
        if a["source_manifest_sha256"]!=b["source_manifest_sha256"]:
            errors.append(("SOURCE_OS",p))
        if len(a.get("cells",[]))!=18 or len(b.get("cells",[]))!=18:
            errors.append(("CELL_COUNT",p));continue
        ca={(c["mode"],c["fee"],c["order"]):c for c in a["cells"]}
        cb={(c["mode"],c["fee"],c["order"]):c for c in b["cells"]}
        if set(ca)!=GRID or set(cb)!=GRID:
            errors.append(("GRID",p));continue
        for key in GRID:
            x,y=ca[key],cb[key]
            if x["passed"]!=y["passed"]:
                errors.append(("OS_SURVIVAL",p,key))
            if x["passed"] and y["passed"]:
                for field in ("final_nav","fees","slippage","funding","turnover",
                              "two_year_cagr","max_drawdown"):
                    if not close(x[field],y[field]):
                        errors.append(("OS_NUMERIC",p,key,field))
                for year in ("2023","2024"):
                    if not close(x["annual"][year]["end_nav"],y["annual"][year]["end_nav"]):
                        errors.append(("OS_YEAR",p,key,year))
        reps[p]=ca
    manifests={v["source_manifest_sha256"] for v in groups.values() for v in v.values()}
    if len(manifests)!=1:errors.append(("CROSS_PATH_SOURCE",))
    survived=sum(int(c["passed"]) for a in reps.values() for c in a.values())
    full=reps.get("BX_full",{})
    for p,rows in reps.items():
        for key,c in rows.items():
            if not c["passed"]:continue
            if not close(c["final_nav"],sum(c["book_final_nav"])):
                errors.append(("BOOK_NAV_SUM",p,key))
            for f in ("fees","slippage","funding","turnover"):
                if not close(c[f],sum(c["book_"+f])):
                    errors.append(("BOOK_COST_SUM",p,key,f))
            for year in ("2023","2024"):
                y=c["annual"][year]
                if not close(y["start_nav"],sum(y["book_start_nav"])) or not close(y["end_nav"],sum(y["book_end_nav"])):
                    errors.append(("BOOK_YEAR_SUM",p,key,year))
                for i in range(4):
                    if i not in ACTIVE[p] and not close(y["book_start_nav"][i],y["book_end_nav"][i]):
                        errors.append(("ABLATION_NOT_CASH",p,key,year,i))
    # New structural gate: removing one sleeve MUST NOT change any other
    # book's NAV or costs. This exposes BW-style hidden core coupling.
    for key,c in full.items():
        if not c["passed"]:continue
        for p,rows in reps.items():
            other=rows.get(key)
            if not other or not other["passed"]:continue
            for i in ACTIVE[p]:
                for field in ("book_final_nav","book_fees","book_slippage",
                              "book_funding","book_turnover"):
                    if not close(c[field][i],other[field][i]):
                        errors.append(("CROSS_BOOK_CONTAMINATION",p,key,i,field))
                for year in ("2023","2024"):
                    for field in ("book_start_nav","book_end_nav"):
                        if not close(c["annual"][year][field][i],
                                     other["annual"][year][field][i]):
                            errors.append(("CROSS_BOOK_YEAR",p,key,i,year,field))
    growth={};marginal={}
    for fee in ("base","severe"):
        for order in ORDERS:
            key=("immediate",fee,order)
            c=full.get(key,{})
            growth["|".join(key)]=bool(c.get("passed") and all(
                c["annual"][yr]["net_log_growth"]>0 for yr in ("2023","2024")))
    for sleeve,p in (("Opportunity","BX_minus_opportunity"),
                     ("RV","BX_minus_RV"),("Stress","BX_minus_stress")):
        marginal[sleeve]={}
        for key,c in full.items():
            other=reps.get(p,{}).get(key,{})
            if not c.get("passed") or not other.get("passed"):continue
            marginal[sleeve]["|".join(key)]={yr:(
                c["annual"][yr]["net_log_growth"]-
                other["annual"][yr]["net_log_growth"])
                for yr in ("2023","2024")}
    sleeve_gates={s:all(marginal[s].get(key,{}).get(yr,float("-inf"))>0
                    for key in growth for yr in ("2023","2024"))
                  for s in marginal}
    reproducible=not errors and len(reps)==5 and survived==90
    if errors:decision="BLOCKED_BX_ACCOUNTING_OR_REPRODUCIBILITY"
    elif survived!=90:decision="REJECT_BX_PHYSICAL_SURVIVAL"
    elif not all(growth.values()) or not all(sleeve_gates.values()):
        decision="REJECT_BX_ECONOMIC_GROWTH_OR_MARGINAL"
    else:decision="PASS_BX_TRAINING_ONLY_REQUIRES_SEPARATE_VALIDATION"
    base=full.get(("immediate","base","carried_before_fill"),{})
    return {"architecture":"BX","historical_training_only":True,
        "validation_2025_read":False,"external_benchmarks_used":False,
        "source_manifest_sha256":next(iter(manifests)) if len(manifests)==1 else None,
        "cross_os_reproducible":not errors and len(reps)==5,
        "errors":errors[:40],"cells_total":sum(len(x) for x in reps.values()),
        "cells_survived":survived,"full_10k_base":base if base.get("passed") else None,
        "growth_gates_10k":growth,"marginal_log_growth":marginal,
        "sleeve_gates_10k":sleeve_gates,"decision":decision}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",default="receipts")
    p.add_argument("--output",default="bx90_official_economic_summary.json")
    a=p.parse_args();result=run(a.root)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    print("BX_CROSS_OS",result["cross_os_reproducible"])
    print("BX_SURVIVAL",result["cells_survived"],"/",result["cells_total"])
    if result["full_10k_base"]:
        c=result["full_10k_base"]
        print("BX_BASE",json.dumps({"cagr":c["two_year_cagr"],
            "2023":c["annual"]["2023"]["net_return"],
            "2024":c["annual"]["2024"]["net_return"],
            "drawdown":c["max_drawdown"],"fees":c["fees"],
            "slippage":c["slippage"],"funding":c["funding"]}))
    print("BX_GROWTH_GATES",result["growth_gates_10k"])
    print("BX_SLEEVE_GATES",result["sleeve_gates_10k"])
    print("BX_DECISION",result["decision"])
    raise SystemExit(2 if result["errors"] else 0)
