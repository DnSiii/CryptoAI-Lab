"""C8 preregistered leave-one-sleeve-out marginal replay; no tuning or promotion."""
import argparse
import json
import math
from pathlib import Path
from .v98_composed_c8_authenticated_runner import run as full_run
from .v98_composed_c8 import composed_c8_sleeves
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import HOUR_MS, ASSETS
from .v98_b0_next_open_execution import replay_next_open

SLOTS=("growth","opportunity","relative_value","stress_recovery")

def masked_sleeves(slot):
    base=composed_c8_sleeves()
    def compute(history):
        result=base(history)
        return {asset:tuple(0. if j==slot else v for j,v in enumerate(result[asset]))
                for asset in ASSETS}
    return compute

def run(prices,manifest,funding):
    data=load(prices,manifest,funding)
    indexed={a:{} for a in ASSETS}
    for a in ASSETS:
        for stamp,rate in data["funding"][a].items():
            offset=stamp-START_MS
            if offset%HOUR_MS or not 0<=offset<data["hours"]*HOUR_MS:
                raise ValueError("C8_INVALID_FUNDING_TIMESTAMP")
            indexed[a][offset//HOUR_MS]=rate
    full=full_run(prices,manifest,funding)
    output={}
    for j,slot in enumerate(SLOTS):
        output[slot]={}
        for scale in (1.,2.,4.):
            summary,ledger=replay_next_open(data["bars"],indexed,masked_sleeves(j),cost_scale=scale)
            key=f"{int(scale)}x"
            baseline=full["results"][key]["final_equity"]
            if summary["hours"]!=data["hours"] or len(ledger)!=data["hours"]-1:
                raise ValueError("C8_ABLATION_INCOMPLETE")
            if not all(math.isfinite(float(summary[k])) for k in ("final_equity","max_drawdown","total_turnover","funding_return_sum")):
                raise ValueError("C8_ABLATION_NONFINITE")
            output[slot][key]={"without_final_equity":summary["final_equity"],
                "full_final_equity":baseline,
                "marginal_final_equity":baseline-summary["final_equity"],
                "without_max_drawdown":summary["max_drawdown"],
                "without_total_turnover":summary["total_turnover"],
                "without_funding_return_sum":summary["funding_return_sum"]}
    return {"status":"C8_ABLATIONS_TRAINING_ONLY_NO_PROMOTION","holdout_accessed":False,
        "source":"AUTHENTICATED_CLEAN4","hours":data["hours"],
        "price_manifest_sha256":data["price_manifest_sha256"],
        "funding_manifest_sha256":data["funding_manifest_sha256"],
        "slots":output}

def main():
    p=argparse.ArgumentParser()
    for name in ("prices","manifest","funding","output"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    if "v98_independent" not in a.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=run(a.prices,a.manifest,a.funding)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"status":result["status"],"slots":result["slots"]},sort_keys=True))
if __name__=="__main__":
    main()
