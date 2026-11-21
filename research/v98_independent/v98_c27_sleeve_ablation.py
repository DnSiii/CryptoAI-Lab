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

def replay_without_control(bars, funding, control):
    original_model=engine.c26_model
    original_governor=engine.governor_multiplier
    original_allocator=engine.c26_allocator
    def equal_active_allocator(sleeves,routers,governor):
        # Preregistered structural comparator: preserve aggregate routed budget,
        # distribute equally across eligible assets; same external C27 caps/costs.
        active=[a for a in ASSETS if sum(sleeves[a])>0 and routers[a]>0]
        budget=sum(sum(sleeves[a])*routers[a]*governor for a in ASSETS)
        each=budget/len(active) if active else 0.
        return {a:(each if a in active else 0.) for a in ASSETS}
    def no_router_model():
        compute,_=original_model()
        return compute,(lambda history: 1.)
    try:
        if control=="router":
            engine.c26_model=no_router_model
        elif control=="governor":
            engine.governor_multiplier=lambda equity,peak: 1.
        elif control=="allocator_equal_active":
            engine.c26_allocator=equal_active_allocator
        else:
            raise ValueError("UNKNOWN_CONTROL")
        return engine.replay(bars,funding,4.)
    finally:
        engine.c26_model=original_model
        engine.governor_multiplier=original_governor
        engine.c26_allocator=original_allocator

def annual_marginal_log_wealth(baseline_rows, counterfactual_rows):
    """Training-year marginal log-growth, aligned on the prior close, not cherry-picked windows."""
    from datetime import datetime, timezone
    if len(baseline_rows)!=len(counterfactual_rows):
        raise ValueError("C27_ANNUAL_MARGINAL_LEDGER_MISMATCH")
    out={}
    for year in (2023,2024,2025):
        start=int(datetime(year,1,1,tzinfo=timezone.utc).timestamp()*1000)
        end=int(datetime(year+1,1,1,tzinfo=timezone.utc).timestamp()*1000)
        lo=(start-START_MS)//HOUR_MS
        hi=(end-START_MS)//HOUR_MS-1
        # Ledger index 1 is the first observed opening mark after the initial bar.
        # Annual return uses the last prior-hour mark as the beginning equity.
        before=lo-1
        if before<1 or hi>=len(baseline_rows)+1:
            raise ValueError("C27_ANNUAL_MARGINAL_OUT_OF_RANGE")
        def equity_at(index,rows):
            return rows[index-1]["equity"]
        b0,b1=equity_at(before,baseline_rows),equity_at(hi,baseline_rows)
        c0,c1=equity_at(before,counterfactual_rows),equity_at(hi,counterfactual_rows)
        if min(b0,b1,c0,c1)<=0 or not all(math.isfinite(x) for x in (b0,b1,c0,c1)):
            raise ValueError("C27_ANNUAL_MARGINAL_INVALID_EQUITY")
        out[str(year)]=math.log(b1/b0)-math.log(c1/c0)
    return out

def run(prices, manifest, funding):
    data=load(prices,manifest,funding)
    bars=data["bars"]
    carry=indexed_funding(data)
    baseline,baseline_rows=engine.replay(bars,carry,4.)
    if baseline["hours"]!=27048 or len(baseline_rows)!=27047:
        raise ValueError("C27_ABLATION_INCOMPLETE_TRAINING")
    if not math.isfinite(baseline["final_equity"]) or baseline["final_equity"]<=0:
        raise ValueError("C27_ABLATION_INVALID_BASELINE")
    scenarios={}
    for slot,name in enumerate(SLEEVES):
        summary,rows=replay_without_sleeve(bars,carry,slot)
        if len(rows)!=len(baseline_rows) or not math.isfinite(summary["final_equity"]) or summary["final_equity"]<=0:
            raise ValueError("C27_ABLATION_MISALIGNED_OR_INSOLVENT")
        scenarios[name]={
            "without_equity":summary["final_equity"],
            "full_minus_without_equity":baseline["final_equity"]-summary["final_equity"],
            "full_minus_without_log_wealth":math.log(baseline["final_equity"]/summary["final_equity"]),
            "without_max_drawdown":summary["max_drawdown"],
            "without_total_turnover":summary["total_turnover"],
            "without_funding_return_sum":summary["funding_return_sum"],
            "without_positive_ledger_hours":sum(rows[i]["equity"]>rows[i-1]["equity"] for i in range(1,len(rows))),
            "marginal_positive":baseline["final_equity"]>summary["final_equity"],
            "annual_marginal_log_wealth_training_only":annual_marginal_log_wealth(baseline_rows,rows)
        }
    controls={}
    for control in ("router","governor","allocator_equal_active"):
        summary,rows=replay_without_control(bars,carry,control)
        if len(rows)!=len(baseline_rows) or not math.isfinite(summary["final_equity"]) or summary["final_equity"]<=0:
            raise ValueError("C27_CONTROL_ABLATION_MISALIGNED_OR_INSOLVENT")
        controls[control]={
            "without_equity":summary["final_equity"],
            "full_minus_without_log_wealth":math.log(baseline["final_equity"]/summary["final_equity"]),
            "without_max_drawdown":summary["max_drawdown"],
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
        "control_ablations":controls,
        "limitations":"Four sleeve removals, router/governor removals and a preregistered equal-active allocator comparator. Allocator comparator is NOT a pure leave-one-out; its budget is fixed before C27 safety caps. Governor-off is diagnostic only, never deployable. Already inspected training is not independent validation."
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
