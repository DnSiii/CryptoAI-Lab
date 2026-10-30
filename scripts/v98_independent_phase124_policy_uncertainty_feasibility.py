#!/usr/bin/env python3
"""V98 Independent Phase124: US policy-uncertainty DATA_ONLY feasibility. Never emits observation values."""
from __future__ import annotations
import csv, hashlib, io, json, math, time, urllib.request
from datetime import date, timedelta
from pathlib import Path

START=date(2023,1,1); END=date(2025,12,31)
SERIES="USEPUINDXD"
URL=f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES}&cosd=2023-01-01&coed=2025-12-31"
OUT=Path("reports/v98_independent_phase124_policy_uncertainty_feasibility.json")

def expected_days():
    out=[]; d=START
    while d<=END:
        out.append(d); d += timedelta(days=1)
    return out

def fetch_payload():
    last=None
    for attempt in range(4):
        try:
            req=urllib.request.Request(URL,headers={"User-Agent":"CryptoAI-Lab-V98-Independent/1.0","Accept":"text/csv"})
            with urllib.request.urlopen(req,timeout=90) as r: return r.status,r.read()
        except Exception as exc:
            last=exc
            if attempt<3: time.sleep(2**attempt)
    raise RuntimeError(f"Phase124 source transport failed after deterministic retries: {type(last).__name__}") from last

def main():
    status,payload=fetch_payload(); rows=list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    canonical=[]; malformed_dates=0; missing_values=0; outside=0
    for row in rows:
        try: d=date.fromisoformat(row["observation_date"])
        except Exception: malformed_dates+=1; continue
        raw=row.get(SERIES,"").strip()
        try: v=float(raw)
        except Exception: missing_values+=1; continue
        if not math.isfinite(v): missing_values+=1; continue
        if not (START<=d<=END): outside+=1; continue
        canonical.append((d,v))
    dates=[d for d,_ in canonical]; unique_dates=sorted(set(dates)); dup=len(dates)-len(unique_dates)
    exp=expected_days(); exp_set=set(exp); usable=[d for d in unique_dates if d in exp_set]
    coverage=len(usable)/len(exp) if exp else 0.0
    canonical_sorted=sorted(canonical,key=lambda x:x[0])
    canonical_hash=hashlib.sha256("\n".join(f"{d.isoformat()},{v:.17g}" for d,v in canonical_sorted).encode()).hexdigest()
    decision="PASS_DATA_ONLY" if status==200 and coverage>=0.95 and malformed_dates==0 and dup==0 and outside==0 else "REJECT_DATA_SOURCE_NO_RESCUE"
    report={"engine":"V98 Independent","phase":"124","purpose":"US economic-policy uncertainty DATA_ONLY feasibility; ZERO ALPHA/ZERO RETURNS/ZERO PNL","source":"FRED public CSV","series_id":SERIES,"source_url":URL,"http_status":status,"training_only":True,"training_start":START.isoformat(),"training_end":END.isoformat(),"validation_accessed":False,"final_holdout_accessed":False,"v16_used":False,"v99_used":False,"values_exposed":False,"descriptives_computed":False,"returns_computed":False,"correlations_computed":False,"alpha_computed":False,"pnl_computed":False,"parameter_search":False,"raw_rows":len(rows),"expected_calendar_days":len(exp),"usable_calendar_days":len(usable),"coverage":coverage,"missing_calendar_days":len(exp)-len(usable),"source_calendar_missing_values":missing_values,"malformed_date_records":malformed_dates,"postcanonical_duplicate_dates":dup,"outside_training_rows":outside,"canonicalization":"parse ISO observation_date; retain finite USEPUINDXD observations in frozen training window; source-calendar missing values counted separately; no fill/interpolation/imputation","payload_sha256":hashlib.sha256(payload).hexdigest(),"canonical_rows_sha256":canonical_hash,"gate":">=95% calendar-day coverage; zero malformed dates; zero duplicate finite dates; zero finite outside-training rows; deterministic hashes","decision":decision}
    OUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ["phase","coverage","source_calendar_missing_values","malformed_date_records","postcanonical_duplicate_dates","decision"]}))

if __name__=="__main__": main()
