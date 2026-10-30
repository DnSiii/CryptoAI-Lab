#!/usr/bin/env python3
"""Read-only frozen HC artifact attribution; never changes signals or economic gates."""
import argparse,json
def run(path):
    with open(path,encoding="utf-8") as f:a=json.load(f)
    if a["architecture"]!="HC" or a["cells_survived"]!=30 or a["errors"]:
        raise ValueError("HC_FROZEN_ARTIFACT_NOT_RECONCILED")
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
    # Read-only diagnostics from the already frozen, independently funded full book.
    # Never recompute trades, signals, funding or economic decisions.
    diagnostic_keys=("hourly_net_profit_factor","hourly_net_payoff",
        "hourly_net_win_rate","positive_utc_days","total_utc_days",
        "positive_day_fraction","worst_hour_net_return","hourly_var_1pct",
        "hourly_cvar_1pct","max_single_asset_gross_concentration",
        "max_gross_to_nav","max_abs_net_to_nav","physical_fill_hours")
    annual_keys=("net_return","net_log_growth","max_drawdown",
        "hourly_net_profit_factor","hourly_net_payoff","hourly_net_win_rate",
        "positive_utc_days","total_utc_days","hourly_cvar_1pct")
    for fee in ("base","severe"):
        cell=a["full_10k_"+fee]
        result[fee+"_diagnostics"]={k:cell[k] for k in diagnostic_keys}
        result[fee+"_annual"]={yr:{k:cell["annual"][yr][k]
            for k in annual_keys} for yr in ("2023","2024")}
    print("HC_FROZEN_ATTRIBUTION",json.dumps(result,sort_keys=True))
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    with open(a.output,"w",encoding="utf-8") as f:
        json.dump(run(a.input),f,sort_keys=True,indent=2,allow_nan=False)
