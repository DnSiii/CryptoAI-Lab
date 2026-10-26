#!/usr/bin/env python3
"""GJ frozen artifact-only economic attribution; never rerun or tune rejected engine."""
from __future__ import annotations
import argparse,glob,json,math
from pathlib import Path
PATHS=("GJ_core_only","GJ_full","GJ_minus_opportunity","GJ_minus_RV","GJ_minus_stress")
FEES=("base","severe","supersevere")
ORDERS=("carried_before_fill","new_after_fill")

def run(root,official):
    summary=json.load(open(official))
    if summary["decision"]!="REJECT_GJ_HISTORICAL_GROWTH_OR_MARGINAL" or summary["cells_survived"]!=30 or summary["errors"]:
        raise ValueError("GJ_NOT_FROZEN_REJECTED_30CELL")
    files=glob.glob(str(Path(root)/"**"/"*.json"),recursive=True)
    if len(files)!=5:raise ValueError(("GJ_EXPECT_FIVE_FROZEN_PATHS",files))
    rows={}
    hashes=set()
    for filename in files:
        p=json.load(open(filename))
        if p["path"] not in PATHS or p["path"] in rows or len(p["cells"])!=6:
            raise ValueError("GJ_INVALID_FROZEN_PATH")
        hashes.add(p["source_manifest_sha256"])
        rows[p["path"]]={(c["fee"],c["order"]):c for c in p["cells"]}
    if len(rows)!=5 or len(hashes)!=1 or next(iter(hashes))!=summary["source_manifest_sha256"]:
        raise ValueError("GJ_FROZEN_SOURCE_OR_PATH_MISMATCH")
    out={"architecture":"GJ","historical_training_only":True,
         "validation_2025_read":False,"economic_strategy_changed":False,
         "source_manifest_sha256":next(iter(hashes)),
         "decision":"FROZEN_GJ_REJECTED_FUNDING_ORDER_SENSITIVITY",
         "comparisons":{}}
    for sleeve,path in (("Opportunity","GJ_minus_opportunity"),
                        ("RelativeValue","GJ_minus_RV"),
                        ("StressRecovery","GJ_minus_stress")):
        out["comparisons"][sleeve]={}
        for fee in FEES:
            for order in ORDERS:
                full=rows["GJ_full"][(fee,order)]
                without=rows[path][(fee,order)]
                if not full["passed"] or not without["passed"]:
                    raise ValueError("GJ_INVALID_PHYSICAL_CELL")
                key=fee+"|"+order
                delta={k:round(float(full[k]-without[k]),8)
                       for k in ("final_nav","fees","slippage","funding","turnover")}
                delta["annual_marginal_log_growth"]={
                    y:round(float(full["annual"][y]["net_log_growth"]-
                                  without["annual"][y]["net_log_growth"]),10)
                    for y in ("2023","2024")}
                out["comparisons"][sleeve][key]=delta
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--official",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=run(a.root,a.official)
    with open(a.output,"w") as f:json.dump(result,f,sort_keys=True,indent=2)
    for sleeve,rows in result["comparisons"].items():
        for key,c in rows.items():
            if key in ("base|carried_before_fill","base|new_after_fill",
                       "severe|carried_before_fill","severe|new_after_fill"):
                print("GJ_FROZEN_COMPONENT",sleeve,key,json.dumps(c,sort_keys=True))
    print("GJ_FROZEN_ATTRIBUTION_PASS_NO_STRATEGY_CHANGE")
