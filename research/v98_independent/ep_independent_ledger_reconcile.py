#!/usr/bin/env python3
"""EP independent full-history physical ledger vs official native receipts.
No source/governor/settle_hour imports; artifact-only comparison.
Does NOT override preregistered economic or future-validation gates.
"""
from __future__ import annotations
import argparse,glob,json,math
from pathlib import Path
PATHS=("EP_core_only","EP_full","EP_minus_opportunity","EP_minus_RV","EP_minus_stress")
FEES=("base","severe","supersevere")
ORDERS=("carried_before_fill","new_after_fill")
FIELDS=("initial_nav","final_nav","net_log_growth","two_year_cagr",
        "max_drawdown","fees","slippage","funding","turnover",
        "max_gross_to_nav","max_single_asset_gross_concentration")
def close(a,b):
    return math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-6)
def run(root):
    root=Path(root)
    comparisons={};failures=[]
    for path in PATHS:
        official=glob.glob(str(root/"official"/("ep30-ubuntu-24.04-"+path)/"*.json"))
        oracle=glob.glob(str(root/"oracle"/("ep-independent-ledger-"+path)/"*.json"))
        if len(official)!=1 or len(oracle)!=1:
            failures.append(("MISSING_ARTIFACT",path,len(official),len(oracle)))
            continue
        o=json.load(open(official[0]));v=json.load(open(oracle[0]))
        if (o.get("path")!=path or v.get("path")!=path or
            o.get("source_manifest_sha256")!=v.get("source_manifest_sha256") or
            v.get("validation_2025_read") is not False or
            v.get("trading_authorized") is not False):
            failures.append(("SOURCE_OR_FIREWALL",path));continue
        a={(c["fee"],c["order"]):c for c in o["cells"]}
        b={(c["fee"],c["order"]):c for c in v["physical_cells"]}
        keys={(fee,order) for fee in FEES for order in ORDERS}
        if set(a)!=keys or set(b)!=keys:
            failures.append(("CELL_GRID",path));continue
        for key in keys:
            x,y=a[key],b[key]
            if x.get("passed") is not True or y.get("passed") is not True:
                failures.append(("PHYSICAL_SURVIVAL",path,key));continue
            for field in FIELDS:
                if not close(x[field],y[field]):
                    failures.append(("ORACLE_NUMERIC",path,key,field))
            for yr in ("2023","2024"):
                for field in ("end_nav","net_log_growth","max_drawdown"):
                    if not close(x["annual"][yr][field],y["annual"][yr][field]):
                        failures.append(("ORACLE_YEAR",path,key,yr,field))
        counter=v.get("oracle",{})
        if (counter.get("settled_hours",0)<10000 or
            counter.get("funding_event_hours",0)<1000 or
            not counter.get("sha256")):
            failures.append(("LEDGER_COVERAGE",path))
        comparisons[path]={"settled_hours":counter.get("settled_hours"),
            "funding_event_hours":counter.get("funding_event_hours"),
            "ledger_sha256":counter.get("sha256")}
    decision=("PASS_EP_INDEPENDENT_FULL_HISTORICAL_LEDGER_ONLY_NOT_ECONOMIC"
              if len(comparisons)==5 and not failures else "BLOCK_EP_LEDGER_ORACLE")
    return {"architecture":"EP","training_only":True,
            "validation_2025_read":False,"trading_authorized":False,
            "independent_ledger_comparisons":comparisons,"errors":failures[:30],
            "decision":decision}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True)
    p.add_argument("--output",required=True);a=p.parse_args()
    result=run(a.root)
    with open(a.output,"w") as f:json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)
    print("EP_INDEPENDENT_LEDGER_AUDIT",result["decision"],
          "paths",len(result["independent_ledger_comparisons"]),
          "errors",result["errors"])
    raise SystemExit(0 if not result["errors"] and
                     len(result["independent_ledger_comparisons"])==5 else 2)
