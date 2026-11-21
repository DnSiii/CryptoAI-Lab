"""Preregistered C27 marginal sleeve ablations on authenticated Clean-4 TRAINING ONLY.

Fixed comparison: exact same data, fills, funding and 4x costs; remove one sleeve
without redistributing its budget. This is NOT an independent validation or
a new strategy-selection gate. No holdout or external benchmark access.
"""
import argparse
import json
import math
from pathlib import Path
from . import v98_c27_authenticated_runner as engine
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import ASSETS, HOUR_MS

SLEEVES=("growth_core","opportunity","relative_value","stress_recovery")

def indexed_funding(data):
    result={a:{} for a in ASSETS}
    for a in ASSETS:
        for stamp, rate in data["funding"][a].items():
            offset=stamp-START_MS
            if offset%HOUR_MS or not 0<=offset<data["hours"]*HOUR_MS:
                raise ValueError("C27_ABLATION_BAD_FUNDING_TIMESTAMP")
            result[a][offset//HOUR_MS]=rate
    return result

def replay_without_sleeve(bars, funding, slot):
    original=engine.c26_model
    def ablated_model():
        compute,router=original()
        def ablated(history):
            base=compute(history)
            return {a:tuple(0. if j==slot else v for j,v in enumerate(base[a]))
                    for a in ASSETS}
        return ablated,router
    try:
        engine.c26_model=ablated_model
        return engine.replay(bars,funding,4.)
    finally:
        engine.c26_model=original

def run(prices, manifest, funding):
    data=load(prices,manifest,funding)
    bars=data["bars"]
    carry=indexed_funding(data)
    baseline,baseline_rows=engine.replay(bars,carry,4.)
    if baseline["hours"]!=27048 or len(baseline_rows)!=27047:
        raise ValueError("C27_ABLATION_INCOMPLETE_TRAINING")
    scenarios={}
    for slot,name in enumerate(SLEEVES):
        summary,rows=replay_without_sleeve(bars,carry,slot)
        if len(rows)!=len(baseline_rows):
            raise ValueError("C27_ABLATION_MISALIGNED")
        scenarios[name]={
            "without_equity":summary["final_equity"],
            "full_minus_without_equity":baseline["final_equity"]-summary["final_equity"],
            "full_minus_without_log_wealth":math.log(baseline["final_equity"]/summary["final_equity"]),
            "without_max_drawdown":summary["max_drawdown"],
            "without_total_turnover":summary["total_turnover"],
            "without_funding_return_sum":summary["funding_return_sum"],
            "without_positive_days":sum(rows[i]["equity"]>rows[i-1]["equity"] for i in range(1,len(rows))),
            "marginal_positive":baseline["final_equity"]>summary["final_equity"]
        }
    return {
        "status":"TRAINING_ONLY_ABLATION_NOT_VALIDATION_NOT_PROMOTION",
        "method":"leave_one_sleeve_out_no_budget_redistribution",
        "cost_scale":"4x",
        "holdout_accessed":False,
        "price_manifest_sha256":data["price_manifest_sha256"],
        "funding_manifest_sha256":data["funding_manifest_sha256"],
        "baseline_final_equity":baseline["final_equity"],
        "baseline_max_drawdown":baseline["max_drawdown"],
        "scenarios":scenarios,
        "limitations":"Router, allocator and governor are held fixed; these four ablations cannot prove all seven slots' marginal value. Historical training is already inspected, not independent validation."
    }

def main():
    parser=argparse.ArgumentParser()
    for name in ("prices","manifest","funding","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("C27_ABLATION_NAMESPACE_REQUIRED")
    report=run(args.prices,args.manifest,args.funding)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,sort_keys=True,allow_nan=False))

if __name__=="__main__":
    main()
