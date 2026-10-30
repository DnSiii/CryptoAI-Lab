#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,math,time,urllib.request
from collections import defaultdict
from pathlib import Path

URL="https://api.blockchain.info/charts/avg-block-size?start=2023-01-01&timespan=3years&format=json&sampled=false"
START=dt.date(2023,1,1); END=dt.date(2025,12,31); EXPECTED=(END-START).days+1
UA="CryptoAI-Lab-V98-Phase270/1.0"

def sha(b): return hashlib.sha256(b).hexdigest()

def fetch(attempts=3):
    last=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(URL,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=45) as r:
                return r.read()
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(1+i)
    raise last

def parse(raw):
    obj=json.loads(raw); by=defaultdict(list); invalid=0
    for item in obj.get("values",[]):
        try:
            ts=float(item.get("x",item.get("timestamp"))); v=float(item.get("y",item.get("value")))
            if not math.isfinite(v): raise ValueError
            d=dt.datetime.fromtimestamp(ts,dt.timezone.utc).date()
        except Exception:
            invalid+=1; continue
        if START<=d<=END: by[d].append(v)
    rows=[]
    for d in sorted(by):
        vals=by[d]
        rows.append({"date":d.isoformat(),"avg_block_size_mb":sum(vals)/len(vals),"source_points":len(vals)})
    return rows,invalid

def csv_bytes(rows):
    from io import StringIO
    s=StringIO(newline="")
    w=csv.DictWriter(s,fieldnames=["date","avg_block_size_mb","source_points"],lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({"date":r["date"],"avg_block_size_mb":format(r["avg_block_size_mb"],".12g"),"source_points":r["source_points"]})
    return s.getvalue().encode()

def build():
    err=None; raw=b""
    try: raw=fetch()
    except Exception as e: err=f"{type(e).__name__}: {e}"
    rows,invalid=parse(raw) if raw else ([],0)
    dates=[dt.date.fromisoformat(r["date"]) for r in rows]
    gaps=[(b-a).days-1 for a,b in zip(dates,dates[1:]) if (b-a).days>1]
    cov=len(dates)/EXPECTED; norm=csv_bytes(rows)
    gates={
        "source_reacquired_and_hashed":err is None and bool(raw),
        "coverage_ge_95pct":cov>=.95,
        "no_duplicate_normalized_dates":len(dates)==len(set(dates)),
        "values_finite_positive":bool(rows) and all(math.isfinite(r["avg_block_size_mb"]) and r["avg_block_size_mb"]>0 for r in rows),
        "no_gap_gt_3_days":max(gaps,default=0)<=3,
        "start_boundary":bool(dates) and dates[0]<=dt.date(2023,1,3),
        "end_boundary":bool(dates) and dates[-1]>=dt.date(2025,12,29),
        "training_boundary_enforced":bool(dates) and all(START<=d<=END for d in dates),
        "normalized_hash_recorded":bool(norm),
        "confirmed_block_metric_only":True,
    }
    decision="PASS_DATA_ONLY" if all(gates.values()) else "FAIL_DATA_NO_ALPHA"
    m={
        "engine":"V98 Independent","phase":270,"kind":"DATA_ONLY_CONFIRMED_BLOCKSPACE",
        "decision":decision,"source":"Blockchain.com Charts API","source_url":URL,
        "period_utc":[str(START),str(END)],"expected_days":EXPECTED,"observed_days":len(dates),
        "coverage":cov,"first_date":dates[0].isoformat() if dates else None,
        "last_date":dates[-1].isoformat() if dates else None,"max_gap_days":max(gaps,default=0),
        "invalid_source_points":invalid,"multi_point_days":sum(r["source_points"]>1 for r in rows),
        "raw_sha256":sha(raw) if raw else None,"raw_bytes":len(raw),"normalized_csv_sha256":sha(norm),
        "source_error":err,"gates":gates,
        "alpha_executed":False,"pnl_executed":False,"crypto_price_join":False,
        "direction_selected":False,"parameter_search":False,
        "validation_accessed":False,"holdout_accessed":False,"phase083_selection_use":False,
        "v14_used":False,"v15_used":False,"v99_used":False,
        "preregistration":"research/v98_independent/phase270_blockspace_utilization_prereg.md"
    }
    return norm,m

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",type=Path,default=Path("research/v98_independent/data/phase270_blockspace"))
    ap.add_argument("--manifest",type=Path,default=Path("research/v98_independent/phase270_blockspace_manifest.json"))
    a=ap.parse_args()
    data,m=build()
    a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/"avg_block_size_daily.csv").write_bytes(data)
    a.manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:m[k] for k in ("decision","observed_days","coverage","first_date","last_date","max_gap_days","gates","source_error")},indent=2,sort_keys=True))

if __name__=="__main__": main()
