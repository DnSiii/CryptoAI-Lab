"""Independent read-only chronological diagnostic of a V98 composed replay ledger.

No parameter selection, benchmark comparison, holdout, or promotion.
"""
import argparse
import datetime as dt
import json
import math
from pathlib import Path
from .v98_phase243_training_reader import START_MS
from .phase243_native_funding_cashflow import HOUR_MS

def audit(summary_path):
    summary=json.loads(Path(summary_path).read_text())
    if summary.get("source")!="AUTHENTICATED_CLEAN4" or summary.get("holdout_accessed") is not False:
        raise ValueError("INVALID_TRAINING_PROVENANCE")
    output={"status":"DIAGNOSTIC_ONLY_NOT_VALIDATION_OR_PROMOTION","scenarios":{}}
    for scenario in ("1x","2x","4x"):
        result=summary["results"][scenario]
        if result["hours"]!=27048:
            raise ValueError("INCOMPLETE_CLEAN4")
        ledger_path=Path(summary_path).with_name(Path(summary_path).stem+"_"+scenario+"_ledger.jsonl")
        by_year={str(y):[] for y in (2023,2024,2025)}
        daily={}
        prev=10000.
        last_index=0
        count=0
        for line in ledger_path.open():
            e=json.loads(line)
            i=e["index"]
            if i!=last_index+1 or not math.isfinite(e["equity"]) or e["equity"]<=0:
                raise ValueError("NONCONTIGUOUS_OR_INVALID_LEDGER")
            stamp=dt.datetime.fromtimestamp((START_MS+i*HOUR_MS)/1000,dt.timezone.utc)
            if stamp.year>2025:
                raise ValueError("HOLDOUT_FIREWALL_BREACH")
            net=e["equity"]/prev-1
            if stamp.year in (2023,2024,2025):
                by_year[str(stamp.year)].append(net)
                daily[stamp.date().isoformat()]=e["equity"]
            prev=e["equity"]
            last_index=i
            count+=1
        if count!=27047:
            raise ValueError("LEDGER_INCOMPLETE")
        # Final close is separate from the final post-fill equity.
        final=result["final_equity"]
        if not math.isfinite(final) or final<=0:
            raise ValueError("INVALID_FINAL_MARK")
        year_metrics={}
        for year,returns in by_year.items():
            if not returns:
                raise ValueError("MISSING_CHRONOLOGICAL_YEAR")
            compounded=math.prod(1+r for r in returns)-1
            profits=sum(r for r in returns if r>0)
            losses=-sum(r for r in returns if r<0)
            positives=[r for r in returns if r>0]
            negatives=[r for r in returns if r<0]
            year_metrics[year]={"hours":len(returns),"return":compounded,
                "profit_factor_hourly":profits/losses if losses else None,
                "payoff_hourly":(profits/len(positives))/(losses/len(negatives)) if positives and negatives else None,
                "win_rate_hourly":len(positives)/len(returns)}
        dates=sorted(daily)
        positive_days=0
        for d0,d1 in zip(dates,dates[1:]):
            positive_days+=daily[d1]>daily[d0]
        output["scenarios"][scenario]={"annual_chronological":year_metrics,
            "positive_days":positive_days,"daily_comparisons":max(0,len(dates)-1),
            "final_equity":final,"max_drawdown":result["max_drawdown"],
            "total_turnover":result["total_turnover"],
            "native_funding_return_sum":result["funding_return_sum"]}
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--summary",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if "v98_independent" not in args.output.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=audit(args.summary)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"status":result["status"],"scenarios":list(result["scenarios"])},sort_keys=True))
if __name__=="__main__":
    main()
