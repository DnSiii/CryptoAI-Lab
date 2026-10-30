#!/usr/bin/env python3
"""V98 Independent Phase119: aggregate stablecoin supply DATA_ONLY feasibility. Never emits observation values."""
from __future__ import annotations
import hashlib, json, math, time, urllib.request
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

START=date(2023,1,1); END=date(2025,12,31)
URL="https://stablecoins.llama.fi/stablecoincharts/all"
OUT=Path("reports/v98_independent_phase119_stablecoin_supply_feasibility.json")

def expected_days():
    n=(END-START).days+1
    return [START+timedelta(days=i) for i in range(n)]

def fetch_payload():
    last=None
    for attempt in range(4):
        try:
            req=urllib.request.Request(URL,headers={"User-Agent":"CryptoAI-Lab-V98-Independent/1.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=90) as r: return r.status,r.read()
        except Exception as exc:
            last=exc
            if attempt<3: time.sleep(2**attempt)
    raise RuntimeError(f"Phase119 source transport failed after deterministic retries: {type(last).__name__}") from last

def canonical_date(x):
    if isinstance(x,(int,float)):
        return datetime.fromtimestamp(int(x),tz=timezone.utc).date()
    s=str(x).strip()
    if s.isdigit(): return datetime.fromtimestamp(int(s),tz=timezone.utc).date()
    return date.fromisoformat(s[:10])

def finite_supply(row):
    # Schema may expose totalCirculatingUSD as a scalar or per-chain mapping. Validate only; never persist value.
    v=row.get("totalCirculatingUSD",row.get("totalCirculating"))
    if isinstance(v,dict):
        vals=[]
        for x in v.values():
            if isinstance(x,dict): x=x.get("peggedUSD",x.get("usd",x.get("value")))
            try: f=float(x)
            except Exception: continue
            if math.isfinite(f): vals.append(f)
        return bool(vals)
    try: return math.isfinite(float(v))
    except Exception: return False

def main():
    status,payload=fetch_payload(); obj=json.loads(payload.decode("utf-8")); rows=obj if isinstance(obj,list) else obj.get("data",[])
    dates=[]; invalid=0; outside=0
    for row in rows:
        if not isinstance(row,dict): invalid+=1; continue
        try: d=canonical_date(row.get("date"))
        except Exception: invalid+=1; continue
        if not (START<=d<=END): outside+=1; continue
        if not finite_supply(row): invalid+=1; continue
        dates.append(d)
    unique=sorted(set(dates)); dup=len(dates)-len(unique); exp=expected_days(); exp_set=set(exp); usable=[d for d in unique if d in exp_set]
    coverage=len(usable)/len(exp); idx_hash=hashlib.sha256("\n".join(d.isoformat() for d in usable).encode()).hexdigest()
    decision="PASS_DATA_ONLY" if status==200 and coverage>=.95 and invalid==0 and dup==0 else "REJECT_DATA_SOURCE_NO_RESCUE"
    report={"engine":"V98 Independent","phase":"119","purpose":"aggregate stablecoin supply DATA_ONLY feasibility; ZERO VALUES/ZERO ALPHA/ZERO RETURNS/ZERO PNL","source":"DefiLlama stablecoins public API","source_url":URL,"http_status":status,"training_only":True,"training_start":START.isoformat(),"training_end":END.isoformat(),"validation_accessed":False,"final_holdout_accessed":False,"v16_used":False,"v99_used":False,"values_exposed":False,"descriptives_computed":False,"returns_computed":False,"correlations_computed":False,"alpha_computed":False,"pnl_computed":False,"parameter_search":False,"raw_rows":len(rows),"expected_days":len(exp),"usable_expected_days":len(usable),"coverage":coverage,"missing_expected_days":len(exp)-len(usable),"invalid_records":invalid,"postcanonical_duplicate_dates":dup,"outside_training_rows":outside,"canonicalization":"UTC date + finite aggregate stablecoin supply presence; frozen training frame; no fill/interpolation/smoothing","payload_sha256":hashlib.sha256(payload).hexdigest(),"canonical_date_index_sha256":idx_hash,"gate":">=95% daily coverage; zero invalid canonical records; zero duplicate dates; deterministic hashes; outside rows excluded before evaluated canonical frame","decision":decision}
    OUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ["phase","coverage","invalid_records","postcanonical_duplicate_dates","decision"]}))
if __name__=="__main__": main()
