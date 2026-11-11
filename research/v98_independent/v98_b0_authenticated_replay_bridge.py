"""B0 Clean-4 authenticated historical replay bridge; research only.

This is a diagnostic CLOSE-to-CLOSE model, not an executable next-open fill.
A3 remains frozen; B0 sleeve budgets are the preregistered four-slot definitions.
"""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import HOUR_MS, ASSETS
from .v98_b0_stream_integration import HourBar, replay_b0

def preregistered_sleeves():
    """Weekly rebalance of four A3-defined sleeve hypotheses, with B0 overlays."""
    last = {a: (0., 0., 0., 0.) for a in ASSETS}
    def compute(history):
        nonlocal last
        i = len(history[ASSETS[0]]) - 1
        if i < 720 or i % 168:
            return last
        momentum = {a: history[a][i]/history[a][i-720]-1 for a in ASSETS}
        weekly = {a: history[a][i]/history[a][i-168]-1 for a in ASSETS}
        growth = {a for a in ASSETS if momentum[a] > 0}
        opportunity = {a for a in ASSETS if weekly[a] > 0 and history[a][i] >= max(history[a][i-168:i+1])}
        eligible = [a for a in ASSETS if momentum[a] > 0 and weekly[a] < 0]
        relative = {min(eligible, key=lambda a:(weekly[a],a))} if eligible else set()
        recovery = {a for a in ASSETS if momentum[a] > 0 and -0.25 < history[a][i]/max(history[a][i-336:i+1])-1 < -0.10}
        last = {a:(0.40/len(growth) if a in growth else 0.,
                   0.15/len(opportunity) if a in opportunity else 0.,
                   0.15 if a in relative else 0.,
                   0.10/len(recovery) if a in recovery else 0.) for a in ASSETS}
        return last
    return compute

def run(prices, manifest, funding):
    data = load(prices, manifest, funding)
    def rows():
        for i in range(data["hours"]):
            t = START_MS + i*HOUR_MS
            yield HourBar(datetime.fromtimestamp(t/1000, tz=timezone.utc),
                          {a: data["bars"][a][i][3] for a in ASSETS},
                          {a: data["funding"][a].get(t,0.) for a in ASSETS})
    results = {}
    for scale in (1., 2., 4.):
        state, entries = replay_b0(rows(), preregistered_sleeves(), cost_scale=scale)
        if len(entries) != data["hours"]-1:
            raise ValueError("INCOMPLETE_REPLAY")
        results[str(int(scale))+"x"] = {
            "final_equity":state.equity,
            "max_drawdown":max((e["drawdown"] for e in entries), default=0.),
            "total_turnover":sum(e["turnover"] for e in entries),
            "funding_return_sum":sum(e["funding_return"] for e in entries),
            "hours":len(entries)}
    return {"status":"EXPLORATORY_CLOSE_MODEL_NOT_EXECUTABLE_NOT_VALIDATED",
            "holdout_accessed":False, "source": "AUTHENTICATED_CLEAN4",
            "price_manifest_sha256":data["price_manifest_sha256"],
            "funding_manifest_sha256":data["funding_manifest_sha256"],
            "results":results}

def main():
    p=argparse.ArgumentParser()
    for name in ("prices","manifest","funding","output"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    if "v98_independent" not in a.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=run(a.prices,a.manifest,a.funding)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
