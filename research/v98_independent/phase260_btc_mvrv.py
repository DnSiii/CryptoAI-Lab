#!/usr/bin/env python3
"""V98 Phase260 Bitcoin MVRV DATA_ONLY acquisition."""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,math,time,urllib.request
from collections import defaultdict
from pathlib import Path

URL="https://api.blockchain.info/charts/mvrv?start=2023-01-01&timespan=3years&format=json&sampled=false"
UA="CryptoAI-Lab-V98-Phase260/1.0 (https://github.com/DnSiii/CryptoAI-Lab)"
START=dt.date(2023,1,1);END=dt.date(2025,12,31);EXPECTED=(END-START).days+1

def sha(b):return hashlib.sha256(b).hexdigest()

def fetch(attempts=3,timeout=45):
    err=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(URL,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
        except Exception as e:
            err=e
            if i+1<attempts:time.sleep(1+i)
    raise err

def parse(raw:bytes):
    obj=json.loads(raw);by_day=defaultdict(list);invalid=0
    for item in obj.get("values",[]):
        try:
            stamp=item.get("x",item.get("timestamp"))
            value=item.get("y",item.get("value"))
            day=dt.datetime.fromtimestamp(float(stamp),dt.timezone.utc).date()
            value=float(value)
            if not math.isfinite(value):raise ValueError
        except Exception:
            invalid+=1;continue
        if START<=day<=END:by_day[day].append(value)
    rows=[]
    for day in sorted(by_day):
        vals=by_day[day]
        rows.append({"date":day.isoformat(),"mvrv":sum(vals)/len(vals),"source_points":len(vals)})
    return rows,invalid

def csv_bytes(rows):
    from io import StringIO
    s=StringIO(newline="")
    w=csv.DictWriter(s,fieldnames=["date","mvrv","source_points"],lineterminator="\n")
    w.writeheader()
    for r in rows:w.writerow({"date":r["date"],"mvrv":format(r["mvrv"],".12g"),"source_points":r["source_points"]})
    return s.getvalue().encode()

def build(attempts=3):
    error=None;raw=b""
    try:raw=fetch(attempts=attempts)
    except Exception as e:error=f"{type(e).__name__}: {e}"
    rows,invalid=parse(raw) if raw else ([],0)
    dates=[dt.date.fromisoformat(r["date"]) for r in rows]
    gaps=[(b-a).days-1 for a,b in zip(dates,dates[1:]) if (b-a).days>1]
    coverage=len(dates)/EXPECTED;normalized=csv_bytes(rows)
    gates={
      "source_reacquired_and_hashed":error is None and bool(raw),
      "coverage_ge_95pct":coverage>=.95,
      "no_duplicate_normalized_dates":len(dates)==len(set(dates)),
      "values_finite_positive":bool(rows) and all(math.isfinite(r["mvrv"]) and r["mvrv"]>0 for r in rows),
      "no_gap_gt_3_days":max(gaps,default=0)<=3,
      "start_boundary":bool(dates) and dates[0]<=dt.date(2023,1,3),
      "end_boundary":bool(dates) and dates[-1]>=dt.date(2025,12,29),
      "training_boundary_enforced":bool(dates) and all(START<=d<=END for d in dates),
      "normalized_hash_recorded":bool(normalized),
    }
    decision="PASS_DATA_ONLY" if all(gates.values()) else "FAIL_DATA_NO_ALPHA"
    manifest={
      "engine":"V98 Independent","phase":260,"kind":"DATA_ONLY_ONCHAIN_VALUATION",
      "decision":decision,"source":"Blockchain.com Charts & Statistics API","source_url":URL,
      "period_utc":[START.isoformat(),END.isoformat()],"expected_days":EXPECTED,
      "observed_days":len(dates),"coverage":coverage,"first_date":dates[0].isoformat() if dates else None,
      "last_date":dates[-1].isoformat() if dates else None,"max_gap_days":max(gaps,default=0),
      "invalid_source_points":invalid,"multi_point_days":sum(r["source_points"]>1 for r in rows),
      "raw_sha256":sha(raw) if raw else None,"raw_bytes":len(raw),"normalized_csv_sha256":sha(normalized),
      "source_error":error,"gates":gates,
      "alpha_executed":False,"pnl_executed":False,"crypto_price_join":False,
      "direction_selected":False,"parameter_search":False,"validation_accessed":False,"holdout_accessed":False,
      "phase083_selection_use":False,"v14_used":False,"v15_used":False,"v99_used":False,
      "preregistration":"research/v98_independent/phase260_btc_mvrv_prereg.md"
    }
    return normalized,manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",type=Path,default=Path("research/v98_independent/data/phase260_btc_mvrv"))
    ap.add_argument("--manifest",type=Path,default=Path("research/v98_independent/phase260_btc_mvrv_manifest.json"))
    ap.add_argument("--attempts",type=int,default=3);a=ap.parse_args()
    data,manifest=build(a.attempts)
    a.out_dir.mkdir(parents=True,exist_ok=True);(a.out_dir/"mvrv_daily.csv").write_bytes(data)
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:manifest[k] for k in ("phase","decision","observed_days","coverage","first_date","last_date","max_gap_days","raw_sha256","normalized_csv_sha256","source_error","gates")},indent=2,sort_keys=True))
if __name__=="__main__":main()
