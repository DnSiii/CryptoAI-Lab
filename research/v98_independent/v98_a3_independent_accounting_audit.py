#!/usr/bin/env python3
"""Independent ledger identity and scenario consistency audit; no promotion or OOS claim."""
import argparse
import json
import math
from pathlib import Path
from datetime import datetime, timezone

SCENARIOS=("1.0","2.0","4.0")
START=int(datetime(2022,12,1,tzinfo=timezone.utc).timestamp()*1000)
HOUR=3600000
N=27048
FIELDS=("starting_equity_usd","gap_pnl_usd","funding_cashflow_usd",
        "intrabar_pnl_usd","execution_cost_usd","turnover_usd","ending_equity_usd")

def run(directory, output):
    if any("v98_independent" not in p.absolute().parts for p in (directory,output)):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    summary=json.loads((directory/"compound_summary.json").read_text())
    if summary.get("holdout_accessed") is not False or summary.get("status")!="ECONOMIC_REPLAY_ONLY_NOT_VALIDATED_ENGINE":
        raise ValueError("INVALID_REPLAY_STATUS")
    report={"status":"INDEPENDENT_ACCOUNTING_AUDIT_NOT_OOS","holdout_accessed":False,"scenarios":{}}
    for multiplier in SCENARIOS:
        rows=json.loads((directory/f"compound_ledger_{multiplier}.json").read_text())
        if len(rows)!=N:
            raise ValueError("INCOMPLETE_LEDGER")
        previous=10000.
        max_error=0.
        total_cost=0.
        for i,row in enumerate(rows):
            if int(row["hour_open_ms"])!=START+i*HOUR:
                raise ValueError("NONCHRONOLOGICAL_LEDGER")
            if not all(math.isfinite(float(row[k])) for k in FIELDS):
                raise ValueError("NONFINITE_LEDGER")
            start=float(row["starting_equity_usd"])
            end=float(row["ending_equity_usd"])
            if abs(start-previous)>1e-7*max(1.,abs(previous)):
                raise ValueError("EQUITY_DISCONTINUITY")
            if start<=0 or end<=0 or float(row["execution_cost_usd"])<0 or float(row["turnover_usd"])<0:
                raise ValueError("INVALID_LEDGER_BALANCE")
            calculated=start+sum(float(row[k]) for k in ("gap_pnl_usd","funding_cashflow_usd","intrabar_pnl_usd"))-float(row["execution_cost_usd"])
            error=abs(calculated-end)
            max_error=max(max_error,error)
            if error>1e-7*max(1.,abs(end)):
                raise ValueError("ACCOUNTING_IDENTITY_FAILURE")
            expected_cost=float(row["turnover_usd"])*6.*float(multiplier)/10000.
            if abs(expected_cost-float(row["execution_cost_usd"]))>1e-7*max(1.,abs(expected_cost)):
                raise ValueError("EXECUTION_COST_MISMATCH")
            total_cost+=float(row["execution_cost_usd"])
            previous=end
        expected=float(summary["scenarios"][multiplier]["final_equity_usd"])
        if abs(previous-expected)>1e-7*max(1.,abs(expected)):
            raise ValueError("SUMMARY_LEDGER_MISMATCH")
        report["scenarios"][multiplier]={"hours":N,"final_equity_usd":previous,"total_execution_cost_usd":total_cost,"maximum_accounting_error_usd":max_error}
    report["all_accounting_gates_passed"]=True
    report["promotion_eligible"]=False
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--replay",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.replay,args.output),sort_keys=True))
