#!/usr/bin/env python3
"""V98 DY immutable artifact-only forensics; no model or future data imports."""
import json,math
from pathlib import Path

def run(root):
    root=Path(root)
    summary=json.loads((root/"summary"/"dy30_official_economic_summary.json").read_text())
    core=json.loads((root/"core"/"dy30_DY_core_only.json").read_text())
    if summary["decision"]!="REJECT_DY_HISTORICAL_GROWTH_OR_MARGINAL":
        raise ValueError("DY_FROZEN_DECISION_MISMATCH")
    if not summary["cross_os_reproducible"] or summary["cells_survived"]!=30 or summary["errors"]:
        raise ValueError("DY_ARTIFACT_INTEGRITY")
    cells={(x["fee"],x["order"]):x for x in core["cells"]}
    rows={}
    for fee in ("base","severe","supersevere"):
        for order in ("carried_before_fill","new_after_fill"):
            c=cells[(fee,order)]
            rows[fee+"|"+order]={
                "core_cagr":c["two_year_cagr"],
                "core_max_dd":c["max_drawdown"],
                "core_2023_net":c["annual"]["2023"]["net_return"],
                "core_2024_net":c["annual"]["2024"]["net_return"],
                "core_funding":c["funding"],
                "core_costs":c["fees"]+c["slippage"],
                "core_turnover":c["turnover"]}
    result={"architecture":"DY","historical_training_only":True,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "source_manifest_sha256":summary["source_manifest_sha256"],
            "frozen_decision":summary["decision"],
            "core_only":rows,
            "full_base":summary["full_10k_base"],
            "full_severe":summary["full_10k_severe"],
            "marginal_log_growth":summary["marginal_log_growth_10k"],
            "marginal_gates":summary["marginal_gates_10k"]}
    base=summary["full_10k_base"]
    severe=summary["full_10k_severe"]
    for fee,full in (("base",base),("severe",severe)):
        c=rows[fee+"|carried_before_fill"]
        print("DY_FROZEN_COMPARE",fee,"core_cagr",c["core_cagr"],
              "full_cagr",full["two_year_cagr"],
              "core_2024",c["core_2024_net"],
              "full_2024",full["annual"]["2024"]["net_return"],
              "core_dd",c["core_max_dd"],"full_dd",full["max_drawdown"],
              "core_costs",c["core_costs"],
              "full_costs",full["fees"]+full["slippage"])
    for book,values in summary["marginal_log_growth_10k"].items():
        print("DY_FROZEN_MARGINAL",book,json.dumps(values,sort_keys=True))
    print("DY_FROZEN_DECISION",summary["decision"],"repro",summary["cross_os_reproducible"])
    return result

if __name__=="__main__":
    out=run("frozen-receipts")
    with open("dy_frozen_forensics.json","w") as f:
        json.dump(out,f,sort_keys=True,indent=2,allow_nan=False)
