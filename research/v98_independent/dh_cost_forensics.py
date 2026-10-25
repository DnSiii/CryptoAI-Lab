#!/usr/bin/env python3
"""DH rejected-system artifact-only cost and ablation attribution; no engine imports."""
from __future__ import annotations
import glob,json,math,sys
from pathlib import Path

ROOT=Path(sys.argv[1] if len(sys.argv)>1 else "receipts")
OUT=Path(sys.argv[2] if len(sys.argv)>2 else "dh_cost_forensics.json")
paths=("DH_core_only","DH_full","DH_minus_opportunity","DH_minus_RV","DH_minus_stress")
rows={}
for f in glob.glob(str(ROOT/"*"/"*.json")):
    parent=Path(f).parent.name
    if "ubuntu-24.04" not in parent:
        continue
    obj=json.load(open(f))
    path=obj["path"]
    if path not in paths or path in rows:
        raise ValueError(("DUPLICATE_OR_UNKNOWN",f,path))
    cells={(c["fee"],c["order"]):c for c in obj["cells"]}
    if len(cells)!=4 or not all(c["passed"] for c in cells.values()):
        raise ValueError(("MISSING_OR_FAILED_CELLS",f))
    rows[path]=cells
if set(rows)!=set(paths):
    raise ValueError(("MISSING_PATHS",list(rows)))
result={"architecture":"DH","historical_training_only":True,
        "validation_2025_read":False,"external_benchmarks_used":False,
        "source":"immutable DH run 40170863794 native physical artifact receipts",
        "paths":{},"full_minus_core":{},"full_minus_ablations":{},
        "fee_mode_impact":{}}
for path,cells in rows.items():
    result["paths"][path]={}
    for (fee,order),c in cells.items():
        result["paths"][path][fee+"|"+order]={
            k:c[k] for k in ("initial_nav","final_nav","two_year_cagr","max_drawdown",
                            "fees","slippage","funding","turnover",
                            "physical_fill_hours","hourly_net_profit_factor",
                            "hourly_net_payoff","hourly_net_win_rate",
                            "positive_day_fraction","max_gross_to_nav")}
        result["paths"][path][fee+"|"+order]["annual"]={
            y:{k:c["annual"][y][k] for k in
               ("net_return","net_log_growth","max_drawdown")}
            for y in ("2023","2024")}
for fee in ("base","severe"):
    for order in ("carried_before_fill","new_after_fill"):
        key=(fee,order)
        full=rows["DH_full"][key]
        core=rows["DH_core_only"][key]
        result["full_minus_core"][fee+"|"+order]={
            "final_nav_delta_usd":full["final_nav"]-core["final_nav"],
            "total_fee_slippage_delta_usd":(full["fees"]+full["slippage"]-
                                           core["fees"]-core["slippage"]),
            "signed_funding_delta_usd":full["funding"]-core["funding"],
            "turnover_delta_usd":full["turnover"]-core["turnover"]}
        for name,p in (("Opportunity","DH_minus_opportunity"),
                       ("RelativeValue","DH_minus_RV"),
                       ("StressRecovery","DH_minus_stress")):
            other=rows[p][key]
            result["full_minus_ablations"][name+"|"+fee+"|"+order]={
                "final_nav_delta_usd":full["final_nav"]-other["final_nav"],
                "fee_slippage_delta_usd":(full["fees"]+full["slippage"]-
                                          other["fees"]-other["slippage"]),
                "signed_funding_delta_usd":full["funding"]-other["funding"],
                "2023_net_log_growth_delta":(full["annual"]["2023"]["net_log_growth"]-
                                             other["annual"]["2023"]["net_log_growth"]),
                "2024_net_log_growth_delta":(full["annual"]["2024"]["net_log_growth"]-
                                             other["annual"]["2024"]["net_log_growth"])}
for order in ("carried_before_fill","new_after_fill"):
    base=rows["DH_full"][("base",order)]
    severe=rows["DH_full"][("severe",order)]
    result["fee_mode_impact"][order]={
        "severe_minus_base_final_nav_usd":severe["final_nav"]-base["final_nav"],
        "severe_minus_base_fees_slippage_usd":(severe["fees"]+severe["slippage"]-
                                              base["fees"]-base["slippage"]),
        "severe_minus_base_funding_usd":severe["funding"]-base["funding"],
        "base_total_fee_slippage_usd":base["fees"]+base["slippage"],
        "severe_total_fee_slippage_usd":severe["fees"]+severe["slippage"],
        "base_turnover_usd":base["turnover"],
        "severe_turnover_usd":severe["turnover"]}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
for order,v in result["fee_mode_impact"].items():
    print("DH_COST_FORENSICS",order,json.dumps(v,sort_keys=True))
for name,v in result["full_minus_ablations"].items():
    if "|severe|carried_before_fill" in name:
        print("DH_SEVERE_MARGINAL",name,json.dumps(v,sort_keys=True))
