"""Authenticated B0 next-open diagnostic: no model selection or holdout."""
import argparse
import json
from pathlib import Path
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import HOUR_MS, ASSETS
from .v98_b0_authenticated_replay_bridge import preregistered_sleeves
from .v98_b0_next_open_execution import replay_next_open

def run(prices, manifest, funding):
    data = load(prices, manifest, funding)
    indexed = {a:{(stamp-START_MS)//HOUR_MS:rate
                  for stamp,rate in data["funding"][a].items()} for a in ASSETS}
    results = {}
    for scale in (1.,2.,4.):
        result, entries = replay_next_open(data["bars"],indexed,
                                          preregistered_sleeves(),
                                          cost_scale=scale)
        if len(entries) != data["hours"]-1:
            raise ValueError("INCOMPLETE_NEXT_OPEN_REPLAY")
        results[str(int(scale))+"x"] = result
    return dict(status="EXPLORATORY_NEXT_OPEN_NOT_INDEPENDENTLY_VALIDATED",
                holdout_accessed=False,
                price_manifest_sha256=data["price_manifest_sha256"],
                funding_manifest_sha256=data["funding_manifest_sha256"],
                results=results)

def main():
    p=argparse.ArgumentParser()
    for key in ("prices","manifest","funding","output"):
        p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args()
    if "v98_independent" not in a.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=run(a.prices,a.manifest,a.funding)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
