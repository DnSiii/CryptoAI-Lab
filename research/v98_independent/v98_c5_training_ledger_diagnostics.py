"""C5 training-only ledger diagnostics. Hourly equity changes are NOT trade PnL."""
import argparse, json, math
from pathlib import Path

def audit(summary_path):
    summary=json.loads(Path(summary_path).read_text())
    if summary.get("status")!="C5_EXPLORATORY_TRAINING_ONLY_PREREG_UNVERIFIED_NO_PROMOTION":
        raise ValueError("C5_EXPLORATORY_STATUS_REQUIRED")
    output={"status":"C5_TRAINING_DIAGNOSTICS_NO_PROMOTION","holdout_accessed":False,"scenarios":{}}
    for scenario in ("1x","2x","4x"):
        ledger_path=Path(summary_path).with_name(Path(summary_path).stem+"_"+scenario+"_ledger.jsonl")
        rows=[json.loads(s) for s in ledger_path.read_text().splitlines()]
        if len(rows)!=27047 or [r["index"] for r in rows]!=list(range(1,27048)):
            raise ValueError("C5_LEDGER_INDEX_GAP")
        equities=[10000.]+[float(r["equity"]) for r in rows]
        if any(not math.isfinite(x) or x<=0 for x in equities):
            raise ValueError("C5_NONFINITE_LEDGER")
        hourly=[equities[i]-equities[i-1] for i in range(1,len(equities))]
        gains=[x for x in hourly if x>0]
        losses=[-x for x in hourly if x<0]
        day_groups={}
        for r in rows:
            day=(r["index"]//24)
            day_groups.setdefault(day,[]).append(r)
        day_pnls=[]
        previous=10000.
        for day in sorted(day_groups):
            end=day_groups[day][-1]["equity"]
            day_pnls.append(end-previous)
            previous=end
        year_metrics={}
        for year,start,end in ((2023,744,9504),(2024,9504,18288),(2025,18288,27048)):
            segment=[r for r in rows if start<=r["index"]<end]
            if not segment: raise ValueError("C5_EMPTY_YEAR")
            start_eq=equities[start-1]
            end_eq=segment[-1]["equity"]
            year_metrics[str(year)]={"start_equity":start_eq,"end_equity":end_eq,
                "return_pct":100*(end_eq/start_eq-1)}
        top10=sum(sorted(gains,reverse=True)[:10])
        total_net=sum(hourly)
        result={"rows":len(rows),"final_ledger_equity_before_close_mark":equities[-1],
          "hourly_positive_fraction":len(gains)/len(hourly),
          "hourly_profit_factor":sum(gains)/sum(losses) if losses else None,
          "hourly_payoff":(sum(gains)/len(gains))/(sum(losses)/len(losses)) if gains and losses else None,
          "positive_day_fraction":sum(x>0 for x in day_pnls)/len(day_pnls),
          "top10_positive_hour_gains_over_net":top10/total_net if total_net>0 else None,
          "calendar_year_training_segments":year_metrics,
          "final_equity_reported":summary["results"][scenario]["final_equity"]}
        if any(not math.isfinite(v) for v in result.values() if isinstance(v,float)):
            raise ValueError("C5_NONFINITE_METRIC")
        output["scenarios"][scenario]=result
    return output

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--summary",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    if "v98_independent" not in Path(a.output).absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=audit(a.summary)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"status":result["status"],"scenarios":list(result["scenarios"])}))
