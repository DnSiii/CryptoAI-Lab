#!/usr/bin/env python3
"""EA frozen artifact-only capital displacement forensics; no market data or strategy import."""
import json,math
from pathlib import Path

def run(root):
    root=Path(root)
    s=json.loads((root/"summary"/"ea30_official_economic_summary.json").read_text())
    c=json.loads((root/"core"/"ea30_EA_core_only.json").read_text())
    if (s["decision"]!="REJECT_EA_HISTORICAL_GROWTH_OR_MARGINAL" or
        not s["cross_os_reproducible"] or s["cells_survived"]!=30 or s["errors"]):
        raise ValueError("EA_FROZEN_RECEIPT_INVALID")
    core={(x["fee"],x["order"]):x for x in c["cells"]}
    rows={}
    for fee in ("base","severe","supersevere"):
        for order in ("carried_before_fill","new_after_fill"):
            k=(fee,order);b=core[k]
            rows["|".join(k)]={
                "core_cagr":b["two_year_cagr"],
                "core_2023":b["annual"]["2023"]["net_return"],
                "core_2024":b["annual"]["2024"]["net_return"],
                "core_costs":b["fees"]+b["slippage"],
                "core_funding":b["funding"],
                "core_turnover":b["turnover"]}
    for fee,full in (("base",s["full_10k_base"]),("severe",s["full_10k_severe"])):
        c=rows[fee+"|carried_before_fill"]
        print("EA_FROZEN_CORE",fee,"core_cagr",c["core_cagr"],
              "full_cagr",full["two_year_cagr"],
              "core_2024",c["core_2024"],
              "full_2024",full["annual"]["2024"]["net_return"],
              "core_costs",c["core_costs"],
              "full_costs",full["fees"]+full["slippage"],
              "full_turnover",full["turnover"],
              "full_max_gross",full["max_gross_to_nav"],
              "full_PF",full["hourly_net_profit_factor"],
              "full_win_rate",full["hourly_net_win_rate"],
              "full_positive_days",full["positive_utc_days"],
              "full_cvar_1pct",full["hourly_cvar_1pct"])
    for book,values in s["marginal_log_growth_10k"].items():
        for key,yrs in values.items():
            print("EA_FROZEN_MARGINAL",book,key,
                  "2023",yrs["2023"],"2024",yrs["2024"])
    print("EA_FROZEN_DECISION",s["decision"],"cross_os",s["cross_os_reproducible"])
    return {"architecture":"EA","source_manifest_sha256":s["source_manifest_sha256"],
            "historical_training_only":True,"validation_2025_read":False,
            "external_benchmarks_used":False,"frozen_decision":s["decision"],
            "core_only":rows,"marginal":s["marginal_log_growth_10k"],
            "full_base":s["full_10k_base"],"full_severe":s["full_10k_severe"]}
if __name__=="__main__":
    result=run("frozen-receipts")
    Path("ea_frozen_forensics.json").write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))
