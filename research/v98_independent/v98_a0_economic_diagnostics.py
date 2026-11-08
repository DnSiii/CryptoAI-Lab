#!/usr/bin/env python3
"""Read-only chronological economic diagnostics for V98 A0. Never promotes candidates."""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

def evaluate(rows):
    if not rows:
        raise ValueError("EMPTY_LEDGER")
    equity=[float(r["ending_equity_usd"]) for r in rows]
    initial=float(rows[0]["starting_equity_usd"])
    if initial<=0 or any(not math.isfinite(x) or x<=0 for x in equity):
        raise ValueError("INVALID_EQUITY_PATH")
    previous=[initial]+equity[:-1]
    returns=[x/y-1 for x,y in zip(equity,previous)]
    peak=initial
    drawdown=0.
    for value in equity:
        peak=max(peak,value)
        drawdown=min(drawdown,value/peak-1)
    wins=sum(x for x in returns if x>0)
    losses=-sum(x for x in returns if x<0)
    days={}
    for r in rows:
        day=datetime.fromtimestamp(r["hour_open_ms"]/1000,timezone.utc).date().isoformat()
        days.setdefault(day,[]).append(r)
    positive_days=sum(v[-1]["ending_equity_usd"]>v[0]["starting_equity_usd"] for v in days.values())
    years=len(rows)/(24*365.25)
    return {"hours":len(rows),"start_equity_usd":initial,"final_equity_usd":equity[-1],
            "total_return":equity[-1]/initial-1,
            "cagr":math.exp(math.log(equity[-1]/initial)/years)-1,
            "max_drawdown":drawdown,"profit_factor_hourly":wins/losses if losses else None,
            "win_rate_hourly":sum(x>0 for x in returns)/len(returns),
            "positive_days":positive_days,"total_days":len(days),
            "execution_cost_usd":sum(float(r["execution_cost_usd"]) for r in rows),
            "funding_cashflow_usd":sum(float(r["funding_cashflow_usd"]) for r in rows)}

def run(directory,output):
    if any("v98_independent" not in p.absolute().parts for p in (directory,output)):
        raise ValueError("V98_NAMESPACE_REQUIRED")
    result={"status":"DIAGNOSTIC_ONLY_NOT_INDEPENDENT_VALIDATION",
            "holdout_accessed":False,"scenarios":{}}
    for scenario in ("1.0","2.0","4.0"):
        path=directory/("compound_ledger_"+scenario+".json")
        rows=json.loads(path.read_text())
        stamps=[r["hour_open_ms"] for r in rows]
        if len(rows)!=27048 or len(set(stamps))!=len(rows) or any(b-a!=3600000 for a,b in zip(stamps,stamps[1:])):
            raise ValueError("INCOMPLETE_OR_NONCHRONOLOGICAL_LEDGER")
        # Calendar years are diagnostic slices, never selection folds.
        years={}
        for row in rows:
            year=datetime.fromtimestamp(row["hour_open_ms"]/1000,timezone.utc).year
            years.setdefault(year,[]).append(row)
        result["scenarios"][scenario]={"full":evaluate(rows),
            "calendar_slices":{str(y):evaluate(part) for y,part in years.items() if y>=2023}}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--replay",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(run(a.replay,a.output),sort_keys=True))
