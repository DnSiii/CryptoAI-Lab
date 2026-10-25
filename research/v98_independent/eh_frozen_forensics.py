#!/usr/bin/env python3
"""EH immutable artifact-only capital displacement diagnosis; no sources, backtest or 2025."""
import argparse,glob,json,math
from pathlib import Path

PATHS=("EH_core_only","EH_full","EH_minus_opportunity","EH_minus_RV","EH_minus_stress")
def run(root):
    rows={}
    for f in glob.glob(str(Path(root)/"eh30-ubuntu-24.04-EH_*"/"*.json")):
        p=json.load(open(f))
        if p.get("path") not in PATHS or p["path"] in rows:
            raise ValueError("EH_ARTIFACT_DUPLICATE")
        assert p.get("source_manifest_sha256")
        assert p.get("decision")=="PASS_EH_MECHANICAL_ONLY"
        assert len(p.get("cells",[]))==6
        rows[p["path"]]={(c["fee"],c["order"]):c for c in p["cells"]}
    if set(rows)!=set(PATHS):raise ValueError("EH_MISSING_IMMUTABLE_RECEIPT")
    result={}
    for fee in ("base","severe"):
        for order in ("carrieh_before_fill","new_after_fill"):
            key=(fee,order)
            full=rows["EH_full"][key]
            core=rows["EH_core_only"][key]
            assert all(c.get("validation_2025_read") is False and
                       c.get("external_benchmarks_used") is False and
                       c.get("trading_authorized") is False
                       for p in PATHS for c in rows[p].values())
            if any(not rows[p][key]["passed"] for p in PATHS):
                raise ValueError("EH_NONPHYSICAL_CELL")
            d={"full_cagr":full["two_year_cagr"],"core_cagr":core["two_year_cagr"],
               "full_final_nav":full["final_nav"],"core_final_nav":core["final_nav"],
               "full_minus_core_final_nav":full["final_nav"]-core["final_nav"],
               "full_minus_core_turnover":full["turnover"]-core["turnover"],
               "full_minus_core_funding":full["funding"]-core["funding"],
               "full_minus_core_fees_slippage":full["fees"]+full["slippage"]-core["fees"]-core["slippage"],
               "sleeves":{}}
            for label,path in (("Opportunity","EH_minus_opportunity"),
                               ("RelativeValue","EH_minus_RV"),
                               ("StressRecovery","EH_minus_stress")):
                other=rows[path][key]
                d["sleeves"][label]={
                    "marginal_final_nav":full["final_nav"]-other["final_nav"],
                    "marginal_turnover":full["turnover"]-other["turnover"],
                    "marginal_funding":full["funding"]-other["funding"],
                    "marginal_fees_slippage":full["fees"]+full["slippage"]-other["fees"]-other["slippage"],
                    "marginal_annual_log_growth":{yr:
                        full["annual"][yr]["net_log_growth"]-other["annual"][yr]["net_log_growth"]
                        for yr in ("2023","2024")}}
            result[fee+"|"+order]=d
    return {"architecture":"EH","frozen_official_run":40223214834,
            "artifact_only":True,"training_only":True,
            "validation_2025_read":False,"trading_authorized":False,
            "decision":"EH_REMAINS_PERMANENTLY_REJECTEH","results":result}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();out=run(a.root)
    with open(a.output,"w") as f:json.dump(out,f,indent=2,sort_keys=True,allow_nan=False)
    for key,v in out["results"].items():
        print("EH_FROZEN_ECONOMIC",key,"full_cagr",v["full_cagr"],
              "core_cagr",v["core_cagr"],"full_minus_core_nav",v["full_minus_core_final_nav"],
              "extra_turnover",v["full_minus_core_turnover"])
        for sleeve,s in v["sleeves"].items():
            print("EH_FROZEN_SLEEVE",key,sleeve,
                  "marginal_nav",s["marginal_final_nav"],
                  "annual",s["marginal_annual_log_growth"],
                  "extra_turnover",s["marginal_turnover"])
