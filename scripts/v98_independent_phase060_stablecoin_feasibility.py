#!/usr/bin/env python3
"""V98 Independent Phase060: stablecoin aggregate liquidity DATA FEASIBILITY ONLY.
No alpha, returns, crypto prices, validation, holdout, V99, or parameter search.
"""
from __future__ import annotations
import json, math, urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://stablecoins.llama.fi/stablecoincharts/all"
DATES = ["2023-03-15","2023-09-15","2024-03-15","2024-09-16","2025-03-17","2025-09-15"]
OUT = Path("reports/v98_independent_phase060_stablecoin_feasibility.json")

def get_total(row):
    for key in ("totalCirculatingUSD", "totalCirculating"):
        v=row.get(key)
        if isinstance(v, dict):
            v=v.get("peggedUSD")
        try:
            x=float(v)
            if math.isfinite(x) and x>0: return x
        except (TypeError, ValueError): pass
    return None

def main():
    req=urllib.request.Request(URL, headers={"User-Agent":"CryptoAI-Lab-V98-Independent/1.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        rows=json.load(r)
    by_day={}
    for row in rows:
        try:
            day=datetime.fromtimestamp(int(row["date"]), tz=timezone.utc).date().isoformat()
        except Exception:
            continue
        total=get_total(row)
        if total is not None: by_day[day]=total
    checks=[]
    for d in DATES:
        total=by_day.get(d)
        checks.append({"date":d,"available":total is not None,"finite_positive":bool(total is not None and math.isfinite(total) and total>0),"aggregate_total_usd":total})
    passed=all(c["finite_positive"] for c in checks)
    report={
      "engine":"V98 Independent","phase":"060","kind":"DATA_FEASIBILITY_ONLY",
      "source":URL,"frozen_dates":DATES,"checks":checks,"passed_data_only":passed,
      "alpha_executed":False,"returns_calculated":False,"crypto_price_joined":False,
      "parameter_search":False,"validation":None,"final_holdout":None,
      "final_holdout_untouched":True,"v99_used":False,
      "decision":"PASS_DATA_ONLY" if passed else "FAIL_DATA_NO_ALPHA",
      "policy":"all six exact UTC dates required; no interpolation/date/source/coin/chain rescue"
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    if not passed: raise SystemExit(2)
if __name__=="__main__": main()
