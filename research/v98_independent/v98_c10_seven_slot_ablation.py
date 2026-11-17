"""V98 C10 preregistered seven-slot marginal diagnostics, training only."""
import argparse
import json
import math
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import ASSETS, HOUR_MS
from .v98_composed_c10 import composed_c10_sleeves, efficiency_router, c10_allocator
from .v98_b0_next_open_execution import replay_next_open
from . import v98_b0_next_open_execution as execution

SLOTS=("growth_core","opportunity","relative_value","stress_recovery",
       "regime_router","dynamic_allocator","risk_governor")
BUDGETS=(.32,.16,.12,.12)

def sleeve_factory(disabled):
    original=composed_c10_sleeves()
    def compute(history):
        result=original(history)
        if disabled in SLOTS[:4]:
            slot=SLOTS.index(disabled)
            return {a:tuple(0. if j==slot else v for j,v in enumerate(result[a]))
                    for a in ASSETS}
        if disabled=="dynamic_allocator":
            # Counterfactual equal-weight within each sleeve, same budget.
            eligible=[[a for a in ASSETS if result[a][j]>0] for j in range(4)]
            return {a:tuple(BUDGETS[j]/len(eligible[j]) if a in eligible[j] else 0.
                            for j in range(4)) for a in ASSETS}
        return result
    return compute

def evaluate(prices,manifest,funding):
    data=load(prices,manifest,funding)
    indexed={a:{} for a in ASSETS}
    for a in ASSETS:
        for stamp,rate in data["funding"][a].items():
            offset=stamp-START_MS
            if offset%HOUR_MS or not 0<=offset<data["hours"]*HOUR_MS:
                raise ValueError("C10_INVALID_FUNDING_TIMESTAMP")
            indexed[a][offset//HOUR_MS]=rate
    results={}
    for disabled in ("baseline",)+SLOTS:
        scenarios={}
        for scale in (1.,2.,4.):
            with ExitStack() as stack:
                stack.enter_context(patch.object(execution,"regime_multiplier",
                    (lambda _h:1.) if disabled=="regime_router" else efficiency_router))
                stack.enter_context(patch.object(execution,"compose_weights",c10_allocator))
                if disabled=="risk_governor":
                    stack.enter_context(patch.object(execution,"governor_multiplier",
                                                    lambda _e,_p:1.))
                summary,ledger=replay_next_open(data["bars"],indexed,
                    sleeve_factory(disabled),cost_scale=scale)
            if summary["hours"]!=data["hours"] or len(ledger)!=data["hours"]-1:
                raise ValueError("C10_INCOMPLETE_REPLAY")
            if not all(math.isfinite(float(summary[k])) for k in
                       ("final_equity","max_drawdown","total_turnover","funding_return_sum")):
                raise ValueError("C10_NONFINITE")
            scenarios[str(int(scale))+"x"]={
                "final_equity":summary["final_equity"],
                "max_drawdown":summary["max_drawdown"],
                "turnover":summary["total_turnover"],
                "funding_return_sum":summary["funding_return_sum"]}
        results[disabled]=scenarios
    for slot in SLOTS:
        for key in ("1x","2x","4x"):
            results[slot][key]["marginal_equity"]=(
                results["baseline"][key]["final_equity"]-results[slot][key]["final_equity"])
    alpha_slots=SLOTS[:6]
    passed=all(results[s][k]["marginal_equity"]>0 for s in alpha_slots
               for k in ("1x","2x","4x"))
    return {"status":"C10_TRAINING_ONLY_NOT_INDEPENDENT_VALIDATION",
            "source":"AUTHENTICATED_CLEAN4","holdout_accessed":False,
            "price_manifest_sha256":data["price_manifest_sha256"],
            "funding_manifest_sha256":data["funding_manifest_sha256"],
            "results":results,
            "alpha_gate_passed":passed,
            "decision":"ELIGIBLE_FOR_SEPARATE_CHRONOLOGICAL_VALIDATION" if passed
                       else "REJECT_C10_ALPHA_GATE",
            "governor_note":"Risk governor is a survival constraint, not an alpha gate; disabled counterfactual is nondeployable."}

def main():
    p=argparse.ArgumentParser()
    for name in ("prices","manifest","funding","output"):
        p.add_argument("--"+name,type=Path,required=True)
    args=p.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=evaluate(args.prices,args.manifest,args.funding)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="results"},sort_keys=True))

if __name__=="__main__":
    main()
