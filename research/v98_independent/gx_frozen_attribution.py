#!/usr/bin/env python3
"""Read-only frozen GX artifact attribution; never changes signals or economic gates."""
import argparse,json
def run(path):
    with open(path,encoding="utf-8") as f:a=json.load(f)
    if a["architecture"]!="GX" or a["cells_survived"]!=30 or a["errors"]:
        raise ValueError("GX_FROZEN_ARTIFACT_NOT_RECONCILED")
    result={"decision":a["decision"],"growth":a["growth_gates_10k"],
            "marginal_gates":a["marginal_gates_10k"],
            "marginal_log_growth":a["marginal_log_growth_10k"],
            "cagr_base":a["full_10k_base"]["two_year_cagr"],
            "cagr_severe":a["full_10k_severe"]["two_year_cagr"],
            "drawdown_severe":a["full_10k_severe"]["max_drawdown"],
            "turnover_base":a["full_10k_base"]["turnover"],
            "turnover_severe":a["full_10k_severe"]["turnover"],
            "funding_base":a["full_10k_base"]["funding"],
            "fees_base":a["full_10k_base"]["fees"],
            "slippage_base":a["full_10k_base"]["slippage"],
            "validation_2025_read":False,"strategy_modified":False,
            "trading_authorized":False}
    print("GX_FROZEN_ATTRIBUTION",json.dumps(result,sort_keys=True))
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    with open(a.output,"w",encoding="utf-8") as f:
        json.dump(run(a.input),f,sort_keys=True,indent=2,allow_nan=False)
