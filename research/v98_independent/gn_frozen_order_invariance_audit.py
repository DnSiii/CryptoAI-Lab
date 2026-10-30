#!/usr/bin/env python3
"""GN artifact-only proof of funding-order-invariant conservative risk targets.
No rejected strategy is rerun or modified; compare frozen official 30-cell receipts.
"""
from __future__ import annotations
import argparse,glob,json,math
from pathlib import Path
PATHS=("GN_core_only","GN_full","GN_minus_opportunity","GN_minus_RV","GN_minus_stress")
FEES=("base","severe","supersevere")
FIELDS=("final_nav","funding","turnover","fees","slippage",
        "max_drawdown","max_gross_to_nav","physical_fill_hours",
        "forced_risk_ratchets")
def close(a,b):
    return math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-8)
def run(root):
    files=glob.glob(str(Path(root)/"**"/"*.json"),recursive=True)
    if len(files)!=5:raise ValueError(("GN_EXPECT_5_RECEIPTS",files))
    seen=set();mismatches=[];pairs=0;source=set()
    for filename in files:
        a=json.load(open(filename))
        path=a["path"]
        if path not in PATHS or path in seen:raise ValueError("GN_INVALID_PATH")
        seen.add(path);source.add(a["source_manifest_sha256"])
        by={(c["fee"],c["order"]):c for c in a["cells"]}
        if len(by)!=6:raise ValueError("GN_INVALID_GRID")
        for fee in FEES:
            old=by[(fee,"carried_before_fill")]
            new=by[(fee,"new_after_fill")]
            if not old["passed"] or not new["passed"]:raise ValueError("GN_FAILED_CELL")
            pairs+=1
            for field in FIELDS:
                if not close(old[field],new[field]):
                    mismatches.append((path,fee,field,old[field],new[field]))
            for year in ("2023","2024"):
                for field in ("end_nav","net_log_growth","max_drawdown"):
                    if not close(old["annual"][year][field],new["annual"][year][field]):
                        mismatches.append((path,fee,year,field))
    if len(seen)!=5 or len(source)!=1 or pairs!=15 or mismatches:
        raise ValueError(("GN_ORDER_INVARIANCE_NOT_PROVED",pairs,mismatches[:20]))
    return {"architecture":"GN","training_only":True,"validation_2025_read":False,
            "candidate_modified":False,"paths":len(seen),"costs":len(FEES),
            "funding_order_pairs_equal":pairs,"mismatches":mismatches,
            "source_manifest_sha256":next(iter(source)),
            "decision":"PASS_GN_15_ORDER_INVARIANT_PHYSICAL_PAIRS_ONLY_NOT_ALPHA"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True)
    p.add_argument("--output",required=True);a=p.parse_args()
    r=run(a.root)
    with open(a.output,"w") as f:json.dump(r,f,sort_keys=True,indent=2)
    print("GN_ORDER_INVARIANT_PHYSICAL_PAIRS",r["funding_order_pairs_equal"])
    print(r["decision"])
