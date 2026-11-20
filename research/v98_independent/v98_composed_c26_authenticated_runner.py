"""Authenticated Clean-4 V98 C26 research replay; no validation/promotion."""
import argparse
import json
import math
from pathlib import Path
from .v98_phase243_training_reader import load, START_MS
from .phase243_native_funding_cashflow import HOUR_MS, ASSETS
from .v98_composed_c26 import c26_model, c26_allocator, WARMUP
from .v98_b0_next_open_execution import replay_next_open
from unittest.mock import patch
from . import v98_b0_next_open_execution as execution

def run(prices, manifest, funding):
    data=load(prices,manifest,funding)
    indexed={a:{} for a in ASSETS}
    for a in ASSETS:
        for stamp,rate in data["funding"][a].items():
            offset=stamp-START_MS
            if offset % HOUR_MS or not 0 <= offset < data["hours"]*HOUR_MS:
                raise ValueError("C26_INVALID_FUNDING_TIMESTAMP")
            indexed[a][offset//HOUR_MS]=rate
    results={}
    ledgers={}
    for scale in (1.,2.,4.):
        sleeve_model,router=c26_model()
        cache={"index":None,"sleeves":None,"btc_history":()}
        def sleeve_fn(history):
            length=len(history[ASSETS[0]])
            cache["btc_history"]=history["BTCUSDT"]
            if cache["sleeves"] is None or (length >= WARMUP+1 and (length-(WARMUP+1))%168==0):
                cache["sleeves"]=sleeve_model(history)
                cache["index"]=length
            return cache["sleeves"]
        def btc_router(_ignored_asset_history):
            return router(cache["btc_history"])
        with patch.object(execution,"regime_multiplier",btc_router), patch.object(execution,"compose_weights",c26_allocator):
            summary,entries=replay_next_open(data["bars"],indexed,sleeve_fn,cost_scale=scale,
                rebalance_filter=None)
        if summary["hours"] != data["hours"] or len(entries)!=data["hours"]-1:
            raise ValueError("C26_INCOMPLETE_REPLAY")
        if any(not math.isfinite(float(summary[k])) for k in
               ("final_equity","max_drawdown","total_turnover","funding_return_sum")):
            raise ValueError("C26_NONFINITE_RESULT")
        # The ledger ends at the final fill; the replay subsequently marks the
        # last hourly open-to-close without inventing another fill.
        final_weights=entries[-1]["weights_after_fill"]
        last_mark=1+sum(final_weights[a]*(data["bars"][a][-1][3]/data["bars"][a][-1][0]-1)
                        for a in ASSETS)
        reconciled=entries[-1]["equity"]*last_mark
        if not math.isclose(reconciled,summary["final_equity"],rel_tol=1e-12,abs_tol=1e-8):
            raise ValueError("C26_FINAL_MARK_RECONCILIATION_FAILED")
        key=str(int(scale))+"x"
        summary["last_mark_factor"]=last_mark
        results[key]=summary
        ledgers[key]=entries
    return dict(status="C26_PREREGISTERED_TRAINING_ONLY_NO_PROMOTION",
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
