"""Training-only C27 governor opportunity-cost and survival attribution.

No strategy selection, holdout access, or change to the frozen C27 rules.
The governor-off book is an unsafe diagnostic, not a deployable candidate.
"""
import argparse
import json
import math
from pathlib import Path
from .v98_c27_sleeve_ablation import indexed_funding, replay_without_control
from .v98_phase243_training_reader import load
from . import v98_c27_authenticated_runner as engine

def analyze(prices, manifest, funding):
    data=load(prices,manifest,funding)
    bars=data["bars"]
    carry=indexed_funding(data)
    base,base_rows=engine.replay(bars,carry,4.)
    off,off_rows=replay_without_control(bars,carry,"governor")
    if len(base_rows)!=27047 or len(off_rows)!=27047:
        raise ValueError("GOVERNOR_FORENSICS_INCOMPLETE")
    active=0
    base_limited=0
    off_limited=0
    exposure_deltas=[]
    for a,b in zip(base_rows,off_rows):
        if a["index"]!=b["index"]:
            raise ValueError("GOVERNOR_FORENSICS_MISALIGNED")
        wa=sum(a["weights_after_fill"].values())
        wb=sum(b["weights_after_fill"].values())
        if abs(wa-wb)>1e-10:
            active+=1
            exposure_deltas.append(wb-wa)
        base_limited+=wa>0.90+1e-9 or max(a["weights_after_fill"].values())>0.40+1e-9
        off_limited+=wb>0.90+1e-9 or max(b["weights_after_fill"].values())>0.40+1e-9
    if min(base["final_equity"],off["final_equity"])<=0:
        raise ValueError("GOVERNOR_FORENSICS_INSOLVENT")
    return {
        "status":"TRAINING_ONLY_GOVERNOR_DIAGNOSTIC_NO_SELECTION",
        "holdout_accessed":False,
        "cost_scale":"4x",
        "hours_compared":len(base_rows),
        "hours_different_post_fill_exposure":active,
        "baseline_final_equity":base["final_equity"],
        "governor_off_final_equity":off["final_equity"],
        "governor_marginal_log_wealth":math.log(base["final_equity"]/off["final_equity"]),
        "baseline_max_drawdown":base["max_drawdown"],
        "governor_off_max_drawdown":off["max_drawdown"],
        "drawdown_reduction":off["max_drawdown"]-base["max_drawdown"],
        "baseline_hard_cap_breach_hours":base_limited,
        "governor_off_hard_cap_breach_hours":off_limited,
        "mean_off_minus_on_gross_exposure_when_different":sum(exposure_deltas)/len(exposure_deltas) if exposure_deltas else 0.,
        "baseline_turnover":base["total_turnover"],
        "governor_off_turnover":off["total_turnover"],
        "limitations":"Governor-off is not deployable. This is already inspected training; no chronological independent validation, no holdout, no promotion."
    }

def main():
    p=argparse.ArgumentParser()
    for name in ("prices","manifest","funding","output"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    if "v98_independent" not in a.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    d=analyze(a.prices,a.manifest,a.funding)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(d,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps(d,sort_keys=True,allow_nan=False))
if __name__=="__main__":
    main()
