"""C8 fixed execution-policy A/B on authenticated Clean-4 training only."""
import argparse
import json
import math
from pathlib import Path
from .v98_phase243_training_reader import load,START_MS
from .phase243_native_funding_cashflow import HOUR_MS,ASSETS
from .v98_composed_c8 import composed_c8_sleeves
from .v98_b0_next_open_execution import replay_next_open
from .v98_c8_daily_risk_execution import replay_c8_daily_risk

def run(prices,manifest,funding):
    data=load(prices,manifest,funding)
    indexed={a:{} for a in ASSETS}
    for a in ASSETS:
        for stamp,rate in data["funding"][a].items():
            offset=stamp-START_MS
            if offset%HOUR_MS or not 0<=offset<data["hours"]*HOUR_MS:
                raise ValueError("INVALID_FUNDING_TIMESTAMP")
            indexed[a][offset//HOUR_MS]=rate
    results={}
    for scale in (1.,2.,4.):
        base,base_ledger=replay_next_open(data["bars"],indexed,composed_c8_sleeves(),cost_scale=scale)
        alt,alt_ledger=replay_c8_daily_risk(data["bars"],indexed,composed_c8_sleeves(),cost_scale=scale)
        if base["hours"]!=27048 or alt["hours"]!=27048 or len(base_ledger)!=27047 or len(alt_ledger)!=27047:
            raise ValueError("INCOMPLETE_HISTORY")
        for label,summary,ledger in (("baseline",base,base_ledger),("daily_risk",alt,alt_ledger)):
            if not all(math.isfinite(float(summary[k])) for k in ("final_equity","max_drawdown","total_turnover","funding_return_sum")):
                raise ValueError("NONFINITE_RESULT")
            final_weights=ledger[-1]["weights_after_fill"]
            last_mark=1+sum(final_weights[a]*(data["bars"][a][-1][3]/data["bars"][a][-1][0]-1) for a in ASSETS)
            if not math.isclose(ledger[-1]["equity"]*last_mark,summary["final_equity"],rel_tol=1e-12,abs_tol=1e-8):
                raise ValueError("FAILED_RECONCILIATION_"+label)
        def attribution(ledger):
            return dict(intraday_turnover=sum(e["turnover"] for e in ledger if e["index"]%24),
                intraday_cost_return_sum=sum(e["cost_return"] for e in ledger if e["index"]%24),
                intraday_fills=sum(e["turnover"]>1e-12 for e in ledger if e["index"]%24),
                daily_fills=sum(e["turnover"]>1e-12 for e in ledger if not e["index"]%24))
        results[str(int(scale))+"x"]=dict(baseline=base,daily_risk=alt,
            baseline_execution=attribution(base_ledger),daily_risk_execution=attribution(alt_ledger),
            final_equity_delta=alt["final_equity"]-base["final_equity"],
            max_drawdown_delta=alt["max_drawdown"]-base["max_drawdown"],
            turnover_delta=alt["total_turnover"]-base["total_turnover"],
            intraday_turnover_delta=attribution(alt_ledger)["intraday_turnover"]-attribution(base_ledger)["intraday_turnover"],
            intraday_cost_return_delta=attribution(alt_ledger)["intraday_cost_return_sum"]-attribution(base_ledger)["intraday_cost_return_sum"])
    return dict(status="C8_EXECUTION_AB_TRAINING_ONLY_NO_PROMOTION",
        source="AUTHENTICATED_CLEAN4",holdout_accessed=False,
        price_manifest_sha256=data["price_manifest_sha256"],
        funding_manifest_sha256=data["funding_manifest_sha256"],results=results)

def main():
    p=argparse.ArgumentParser()
    for key in ("prices","manifest","funding","output"):
        p.add_argument("--"+key,type=Path,required=True)
    args=p.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=run(args.prices,args.manifest,args.funding)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
