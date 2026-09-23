"""V98 Independent Phase116 — DXY DATA_ONLY feasibility. ZERO alpha/returns/PnL.

Strictly limited to training dates 2023-01-01..2025-12-31.  This probe deliberately
reports metadata/coverage/integrity only and never serializes DXY observations or
value descriptives.
"""
from __future__ import annotations
import csv, hashlib, io, json, math, urllib.request
from datetime import date, timedelta
from pathlib import Path

SERIES = "DTWEXBGS"  # FRED Trade Weighted U.S. Dollar Index: Broad, daily business-day macro USD index
START, END = date(2023,1,1), date(2025,12,31)
OUT = Path("reports/v98_independent_phase116_dxy_feasibility.json")
URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES}&cosd={START.isoformat()}&coed={END.isoformat()}"

def business_days(a: date,b: date)->set[str]:
    out=set(); d=a
    while d<=b:
        if d.weekday()<5: out.add(d.isoformat())
        d += timedelta(days=1)
    return out

def main():
    req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 CryptoAI-Lab-V98-Independent/1.0","Accept":"text/csv,*/*"})
    with urllib.request.urlopen(req,timeout=120) as r:
        payload=r.read(); status=getattr(r,"status",200)
    payload_sha=hashlib.sha256(payload).hexdigest()
    rows=list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    expected=business_days(START,END)
    usable={}; duplicate_dates=0; invalid=0; outside=0
    for row in rows:
        ds=row.get("observation_date") or row.get("DATE")
        raw=row.get(SERIES)
        if not ds: invalid += 1; continue
        try: d=date.fromisoformat(ds)
        except ValueError: invalid += 1; continue
        if d<START or d>END: outside += 1; continue
        if ds in usable: duplicate_dates += 1; continue
        try: x=float(raw); ok=math.isfinite(x)
        except (TypeError,ValueError): ok=False
        if not ok: invalid += 1; continue
        usable[ds]=x
    usable_business=set(usable)&expected
    missing=len(expected-usable_business)
    coverage=len(usable_business)/len(expected) if expected else 0.0
    canonical_sha=hashlib.sha256("\n".join(sorted(usable_business)).encode()).hexdigest()
    passed=(status==200 and coverage>=0.95 and invalid==0 and duplicate_dates==0)
    report={
      "engine":"V98 Independent","phase":"116","purpose":"external USD-index macro-liquidity DATA_ONLY feasibility; ZERO ALPHA/ZERO RETURNS/ZERO PNL",
      "source":"FRED public CSV","series_id":SERIES,"source_url":URL,"http_status":status,
      "training_only":True,"training_start":START.isoformat(),"training_end":END.isoformat(),
      "validation_accessed":False,"final_holdout_accessed":False,"v16_used":False,"v99_used":False,
      "values_exposed":False,"descriptives_computed":False,"returns_computed":False,"correlations_computed":False,"alpha_computed":False,"pnl_computed":False,"parameter_search":False,
      "raw_rows":len(rows),"expected_business_days":len(expected),"usable_business_days":len(usable_business),"coverage":coverage,
      "first_usable_date":min(usable_business) if usable_business else None,"last_usable_date":max(usable_business) if usable_business else None,
      "missing_business_days":missing,"invalid_records":invalid,"postcanonical_duplicate_dates":duplicate_dates,"outside_training_rows":outside,
      "canonicalization":"parse ISO observation_date; retain finite observations inside frozen training window; one record/date; coverage denominator=Mon-Fri calendar business days (federal holidays therefore conservatively count missing)",
      "payload_sha256":payload_sha,"canonical_date_index_sha256":canonical_sha,
      "gate":">=95% expected business-day coverage; zero invalid/nonfinite records after canonicalization; zero postcanonical duplicate dates; deterministic source/hash",
      "decision":"PASS_DATA_ONLY" if passed else "REJECT_DATA_SOURCE"
    }
    OUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:report[k] for k in ["phase","coverage","invalid_records","postcanonical_duplicate_dates","decision"]},indent=2))
if __name__=="__main__": main()
