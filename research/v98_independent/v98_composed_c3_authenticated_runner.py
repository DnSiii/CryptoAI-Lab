"""Authenticated Clean-4 V98 C3 research replay; no validation/promotion."""
import argparse
import json
import math
from pathlib import Path
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import HOUR_MS, ASSETS
from .v98_composed_c3 import composed_c3_sleeves
from .v98_b0_next_open_execution import replay_next_open

def run(prices, manifest, funding):
    data=load(prices,manifest,funding)
    indexed={a:{} for a in ASSETS}
    for a in ASSETS:
        for stamp,rate in data["funding"][a].items():
            offset=stamp-START_MS
            if offset % HOUR_MS or not 0 <= offset < data["hours"]*HOUR_MS:
                raise ValueError("C3_INVALID_FUNDING_TIMESTAMP")
            indexed[a][offset//HOUR_MS]=rate
    results={}
    ledgers={}
    for scale in (1.,2.,4.):
        summary,entries=replay_next_open(data["bars"],indexed,composed_c3_sleeves(),cost_scale=scale)
        if summary["hours"] != data["hours"] or len(entries)!=data["hours"]-1:
            raise ValueError("C3_INCOMPLETE_REPLAY")
        if any(not math.isfinite(float(summary[k])) for k in
               ("final_equity","max_drawdown","total_turnover","funding_return_sum")):
            raise ValueError("C3_NONFINITE_RESULT")
        key=str(int(scale))+"x"
        results[key]=summary
        ledgers[key]=entries
    return dict(status="C3_PREREGISTERED_TRAINING_ONLY_NO_PROMOTION",
                holdout_accessed=False,source="AUTHENTICATED_CLEAN4",
                price_manifest_sha256=data["price_manifest_sha256"],
                funding_manifest_sha256=data["funding_manifest_sha256"],
                results=results,ledgers=ledgers)

def main():
    p=argparse.ArgumentParser()
    for name in ("prices","manifest","funding","output"):
        p.add_argument("--"+name,type=Path,required=True)
    args=p.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=run(args.prices,args.manifest,args.funding)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    ledgers=result.pop("ledgers")
    for scenario,entries in ledgers.items():
        path=args.output.with_name(args.output.stem+"_"+scenario+"_ledger.jsonl")
        with path.open("w") as out:
            for entry in entries:
                out.write(json.dumps(entry,sort_keys=True,allow_nan=False)+"\n")
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
