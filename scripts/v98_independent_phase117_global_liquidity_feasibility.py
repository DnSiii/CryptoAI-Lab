#!/usr/bin/env python3
"""V98 Independent Phase117: WALCL DATA_ONLY feasibility. Never emits observation values."""
from __future__ import annotations
import csv, hashlib, io, json, math, time, urllib.request
from datetime import date, timedelta
from pathlib import Path

START=date(2023,1,1); END=date(2025,12,31)
URL="https://fred.stlouisfed.org/graph/fredgraph.csv?id=WALCL&cosd=2023-01-01&coed=2025-12-31"
OUT=Path("reports/v98_independent_phase117_global_liquidity_feasibility.json")

def expected_wednesdays():
    d=START
    while d.weekday()!=2: d += timedelta(days=1)
    out=[]
    while d<=END: out.append(d); d += timedelta(days=7)
    return out

def fetch_payload():
    """Transport retry only; scientific series/window/gates remain frozen."""
    last=None
    for attempt in range(4):
        try:
            req=urllib.request.Request(URL, headers={"User-Agent":"CryptoAI-Lab-V98-Independent/1.0","Accept":"text/csv"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, r.read()
        except Exception as exc:
            last=exc
            if attempt < 3: time.sleep(2 ** attempt)
    raise RuntimeError(f"Phase117 source transport failed after deterministic retries: {type(last).__name__}") from last

def main():
    status,payload=fetch_payload()
    rows=list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    dates=[]; invalid=0; outside=0
    for row in rows:
        try: d=date.fromisoformat(row["observation_date"])
        except Exception: invalid += 1; continue
        if not (START<=d<=END): outside += 1; continue
        raw=row.get("WALCL","").strip()
        try: v=float(raw)
        except Exception: invalid += 1; continue
        if not math.isfinite(v): invalid += 1; continue
        dates.append(d)
    unique=sorted(set(dates)); dup=len(dates)-len(unique)
    exp=expected_wednesdays(); exp_set=set(exp)
    usable=[d for d in unique if d in exp_set]
    coverage=len(usable)/len(exp) if exp else 0.0
    idx_hash=hashlib.sha256("\n".join(d.isoformat() for d in usable).encode()).hexdigest()
    decision="PASS_DATA_ONLY" if status==200 and coverage>=0.95 and invalid==0 and dup==0 and outside==0 else "REJECT_DATA_SOURCE_NO_RESCUE"
    report={
      "engine":"V98 Independent","phase":"117","purpose":"Fed balance-sheet macro-liquidity DATA_ONLY feasibility; ZERO ALPHA/ZERO RETURNS/ZERO PNL",
      "source":"FRED public CSV","series_id":"WALCL","source_url":URL,"http_status":status,"training_only":True,
      "training_start":START.isoformat(),"training_end":END.isoformat(),"validation_accessed":False,"final_holdout_accessed":False,
      "v16_used":False,"v99_used":False,"values_exposed":False,"descriptives_computed":False,"returns_computed":False,
      "correlations_computed":False,"alpha_computed":False,"pnl_computed":False,"parameter_search":False,
      "raw_rows":len(rows),"expected_wednesdays":len(exp),"usable_expected_wednesdays":len(usable),"coverage":coverage,
      "missing_expected_wednesdays":len(exp)-len(usable),"invalid_records":invalid,"postcanonical_duplicate_dates":dup,"outside_training_rows":outside,
      "canonicalization":"parse ISO observation_date; retain finite WALCL observations in frozen training window; exact Wednesday index only; no fill/interpolation",
      "payload_sha256":hashlib.sha256(payload).hexdigest(),"canonical_date_index_sha256":idx_hash,
      "gate":">=95% expected-Wednesday coverage; zero invalid/nonfinite; zero duplicates; zero outside-training rows; deterministic hashes",
      "decision":decision}
    OUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ["phase","coverage","invalid_records","postcanonical_duplicate_dates","decision"]}))

if __name__=="__main__": main()
