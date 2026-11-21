"""Independent C27 daily compounded-performance and downside diagnostics, training only.

These are DAILY return diagnostics, not trade-level Profit Factor or win rate.
No candidate selection, holdout reads, or strategy parameter changes.
"""
import argparse
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

def evaluate(summary_path):
    summary_path=Path(summary_path)
    summary=json.loads(summary_path.read_text())
    if summary.get("source")!="AUTHENTICATED_CLEAN4" or summary.get("holdout_accessed") is not False:
        raise ValueError("SOURCE_OR_HOLDOUT")
    result={}
    for scenario in ("1x","2x","4x"):
        p=summary_path.with_name(summary_path.stem+"_"+scenario+"_ledger.jsonl")
        rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
        if len(rows)!=27047 or any(r["index"]!=i for i,r in enumerate(rows,1)):
            raise ValueError("INCOMPLETE_OR_NONCHRONOLOGICAL_LEDGER")
        daily={}
        epoch=datetime(2022,12,1,tzinfo=timezone.utc)
        for row in rows:
            day=(epoch+timedelta(hours=row["index"])).date().isoformat()
            daily[day]=float(row["equity"])
        days=sorted(daily)
        if len(days)<1095:
            raise ValueError("INSUFFICIENT_DAYS")
        daily[days[-1]]=float(summary["results"][scenario]["final_equity"])
        equity=[10000.]+[daily[d] for d in days]
        returns=[equity[i]/equity[i-1]-1 for i in range(1,len(equity))]
        if not all(math.isfinite(r) for r in returns):
            raise ValueError("NONFINITE_DAILY_RETURN")
        gains=sum(r for r in returns if r>0)
        losses=-sum(r for r in returns if r<0)
        positive=sum(r>0 for r in returns)
        negative=sum(r<0 for r in returns)
        streak=worst_streak=0
        for r in returns:
            streak=streak+1 if r<0 else 0
            worst_streak=max(worst_streak,streak)
        ordered=sorted(returns)
        n=len(returns)
        if not math.isclose(math.prod(1+r for r in returns),equity[-1]/10000,rel_tol=1e-9):
            raise ValueError("DAILY_COMPOUND_MISMATCH")
        result[scenario]=dict(
            definition="DAILY_MARK_TO_MARK_NOT_TRADE_LEVEL",
            days=n,positive_days=positive,negative_days=negative,
            daily_win_rate=positive/n,
            daily_profit_factor=(gains/losses if losses>0 else None),
            daily_payoff=(gains/positive)/(losses/negative) if positive and negative else None,
            worst_daily_return=ordered[0],
            bottom_1pct_daily_return=ordered[max(0,math.ceil(n*.01)-1)],
            longest_negative_day_streak=worst_streak,
            final_equity=equity[-1])
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--summary",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if "v98_independent" not in args.summary.resolve().parts or "v98_independent" not in args.output.resolve().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result=evaluate(args.summary)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
