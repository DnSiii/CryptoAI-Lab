"""V98 B0 annual exposure/cost/funding attribution; descriptive training only."""
import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from .v98_phase243_training_reader import START_MS
from .phase243_native_funding_cashflow import HOUR_MS

def attribute(entries, final_equity, initial_equity=10000.):
    if len(entries) != 27047 or not math.isfinite(final_equity) or final_equity <= 0:
        raise ValueError("INCOMPLETE_TRAINING_LEDGER")
    years = defaultdict(lambda: dict(hours=0, gross_log=0., funding_log=0., cost_log=0., net_log=0., turnover=0., exposure=0., invested_hours=0., assets=defaultdict(float)))
    previous = initial_equity
    for index, e in enumerate(entries, 1):
        if e["index"] != index:
            raise ValueError("NONCONTIGUOUS_LEDGER")
        year = str(datetime.fromtimestamp((START_MS+index*HOUR_MS)/1000, tz=timezone.utc).year)
        gross, funding, cost = (float(e[k]) for k in ("gross_return","funding_return","cost_return"))
        if not all(math.isfinite(x) for x in (gross,funding,cost,e["equity"],e["pre_fill_equity"])) or 1+gross+funding <= 0 or not 0 <= cost < 1:
            raise ValueError("INVALID_LEDGER")
        marked = previous*(1+gross+funding)
        expected = marked*(1-cost)
        if abs(marked-e["pre_fill_equity"]) > 1e-7*max(1,abs(marked)) or abs(expected-e["equity"]) > 1e-7*max(1,abs(expected)):
            raise ValueError("ACCOUNTING_MISMATCH")
        row = years[year]
        gross_parts = e.get("gross_by_asset")
        funding_parts = e.get("funding_by_asset")
        if not isinstance(gross_parts, dict) or not isinstance(funding_parts, dict) or set(gross_parts) != set(e["weights_after_fill"]) or set(funding_parts) != set(gross_parts):
            raise ValueError("MISSING_ASSET_CONTRIBUTION")
        if any(not math.isfinite(float(x)) for x in list(gross_parts.values())+list(funding_parts.values())) or abs(sum(gross_parts.values())-gross)>1e-12 or abs(sum(funding_parts.values())-funding)>1e-12:
            raise ValueError("ASSET_CONTRIBUTION_MISMATCH")
        if "asset_gross_simple" not in row:
            row["asset_gross_simple"] = defaultdict(float)
            row["asset_funding_simple"] = defaultdict(float)
        for asset in gross_parts:
            row["asset_gross_simple"][asset] += gross_parts[asset]
            row["asset_funding_simple"][asset] += funding_parts[asset]
        row["hours"] += 1
        row["gross_log"] += math.log1p(gross)
        row["funding_log"] += math.log1p(funding/(1+gross))
        row["cost_log"] += math.log1p(-cost)
        row["net_log"] += math.log(e["equity"]/previous)
        turnover = float(e["turnover"])
        if not math.isfinite(turnover) or turnover < 0:
            raise ValueError("INVALID_TURNOVER")
        before = e.get("weights_before_fill")
        after = e["weights_after_fill"]
        if not isinstance(before, dict) or set(before) != set(after):
            raise ValueError("INVALID_PRE_FILL_WEIGHTS")
        if any(not math.isfinite(float(w)) or w < -1e-12 for w in before.values()):
            raise ValueError("INVALID_WEIGHTS")
        exposure = sum(abs(w) for w in after.values())
        if not math.isfinite(exposure) or exposure < 0 or exposure > 1+1e-9:
            raise ValueError("INVALID_EXPOSURE")
        if any(float(w) < -1e-12 for w in after.values()):
            raise ValueError("INVALID_WEIGHTS")
        actual_turnover = sum(abs(float(after[a]) - float(before[a])) for a in after)
        if abs(turnover - actual_turnover) > 1e-9 * max(1., actual_turnover):
            raise ValueError("TURNOVER_RECONCILIATION_FAILURE")
        row["turnover"] += turnover
        row["exposure"] += exposure
        row["invested_hours"] += exposure > 1e-12
        for asset,w in e["weights_after_fill"].items():
            row["assets"][asset] += abs(w)
        previous = e["equity"]
    terminal_log = math.log(final_equity/previous)
    terminal_year = str(datetime.fromtimestamp((START_MS+(len(entries)-1)*HOUR_MS)/1000, tz=timezone.utc).year)
    if terminal_year not in years:
        raise ValueError("INVALID_TERMINAL_YEAR")
    years[terminal_year]["terminal_mark_log"] = terminal_log
    years[terminal_year]["net_log"] += terminal_log
    result = {}
    for year,row in sorted(years.items()):
        hours = row["hours"]
        result[year] = {k:(dict(v) if isinstance(v, defaultdict) else v) for k,v in row.items() if k != "assets"}
        result[year]["mean_gross_exposure"] = row["exposure"]/hours
        result[year]["mean_asset_exposure"] = {a:v/hours for a,v in sorted(row["assets"].items())}
        result[year]["net_return"] = math.expm1(row["net_log"])
        residual = row["net_log"]-row["gross_log"]-row["funding_log"]-row["cost_log"]-row.get("terminal_mark_log",0.)
        if abs(residual) > 1e-8:
            raise ValueError("ATTRIBUTION_RECONCILIATION_FAILURE")
        result[year]["log_decomposition_residual"] = residual
    return {"status":"DESCRIPTIVE_TRAINING_ONLY_NO_PROMOTION","holdout_accessed":False,"annual_attribution":result}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--directory",type=Path,required=True)
    args=parser.parse_args()
    if "v98_independent" not in args.directory.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    summary=json.loads((args.directory/"b0_next_open_summary.json").read_text())
    if summary.get("holdout_accessed") is not False or set(summary["results"]) != {"1x","2x","4x"}:
        raise ValueError("INVALID_SOURCE_BOUNDARY")
    result={}
    for scenario in ("1x","2x","4x"):
        with (args.directory/f"b0_next_open_summary_{scenario}_ledger.jsonl").open() as stream:
            entries=[json.loads(line) for line in stream]
        result[scenario]=attribute(entries,summary["results"][scenario]["final_equity"])
    (args.directory/"b0_regime_attribution.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({s:{y:{"net_return":v["net_return"],"mean_gross_exposure":v["mean_gross_exposure"],"turnover":v["turnover"]} for y,v in r["annual_attribution"].items()} for s,r in result.items()},sort_keys=True))

if __name__=="__main__":
    main()
