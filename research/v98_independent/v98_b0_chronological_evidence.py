"""Independent chronological B0 evidence audit; descriptive, never promotion."""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from .v98_phase243_training_reader import START_MS
from .phase243_native_funding_cashflow import HOUR_MS

def audit(entries, final_equity, initial_equity=10000.):
    if len(entries) != 27047 or any(e["index"] != i for i,e in enumerate(entries,1)):
        raise ValueError("INCOMPLETE_CHRONOLOGY")
    if not math.isfinite(final_equity) or final_equity <= 0:
        raise ValueError("INVALID_FINAL_MARK")
    # An index denotes the next-open fill at START_MS + index hours.
    # The terminal close mark is attributed to the last available UTC hour.
    by_year = {}
    by_month = {}
    for e in entries:
        t = datetime.fromtimestamp((START_MS + e["index"]*HOUR_MS)/1000, tz=timezone.utc)
        equity = float(e["equity"])
        if not math.isfinite(equity) or equity <= 0:
            raise ValueError("INVALID_EQUITY")
        by_year[t.year] = equity
        by_month[t.strftime("%Y-%m")] = equity
    by_year[2025] = final_equity
    by_month["2025-12"] = final_equity
    previous = initial_equity
    annual = {}
    for year, value in sorted(by_year.items()):
        annual[str(year)] = value/previous-1
        previous = value
    previous = initial_equity
    monthly = {}
    for month,value in sorted(by_month.items()):
        monthly[month] = value/previous-1
        previous = value
    if abs(previous-final_equity)>1e-7:
        raise ValueError("TERMINAL_EQUITY_MISMATCH")
    # 2022 is warmup; do not call it an independent validation fold.
    return {"status":"DESCRIPTIVE_TRAINING_ONLY_NO_PROMOTION",
            "utc_annual_returns_including_warmup":annual,
            "utc_monthly_returns_including_warmup":monthly,
            "negative_months":sum(x<0 for x in monthly.values()),
            "positive_months":sum(x>0 for x in monthly.values()),
            "months":len(monthly),
            "chronology_start_ms":START_MS+HOUR_MS,
            "chronology_end_ms":START_MS+len(entries)*HOUR_MS,
            "holdout_accessed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",type=Path,required=True)
    a=p.parse_args()
    if "v98_independent" not in a.directory.absolute().parts:
        raise ValueError("V98_NAMESPACE_REQUIRED")
    summary=json.loads((a.directory/"b0_next_open_summary.json").read_text())
    if summary.get("holdout_accessed") is not False or set(summary["results"])!={"1x","2x","4x"}:
        raise ValueError("INVALID_SOURCE_BOUNDARY")
    results={}
    for scenario in ("1x","2x","4x"):
        with (a.directory/f"b0_next_open_summary_{scenario}_ledger.jsonl").open() as f:
            entries=[json.loads(line) for line in f]
        results[scenario]=audit(entries,summary["results"][scenario]["final_equity"])
    (a.directory/"b0_chronological_evidence.json").write_text(json.dumps(results,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({s:{"annual":r["utc_annual_returns_including_warmup"],"negative_months":r["negative_months"],"months":r["months"]} for s,r in results.items()},sort_keys=True))

if __name__=="__main__":
    main()
