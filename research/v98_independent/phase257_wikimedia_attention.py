#!/usr/bin/env python3
"""V98 Phase257 Wikimedia public-attention DATA_ONLY acquisition.

Zero crypto price joins, zero signal direction, zero PnL, zero parameter search.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,time,urllib.parse,urllib.request
from pathlib import Path

START=dt.date(2023,1,1)
END=dt.date(2025,12,31)
EXPECTED=(END-START).days+1
ASSET_ARTICLE={
    "BTCUSDT":"Bitcoin",
    "ETHUSDT":"Ethereum",
    "BNBUSDT":"BNB_Smart_Chain_(blockchain_platform)",
    "SOLUSDT":"Solana_(blockchain_platform)",
}
BASE="https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user"
UA="CryptoAI-Lab-V98-Phase257/1.0 (https://github.com/DnSiii/CryptoAI-Lab)"

def sha256_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def endpoint(article:str,year:int)->str:
    title=urllib.parse.quote(article,safe="")
    return f"{BASE}/{title}/daily/{year}010100/{year}123100"

def fetch(url:str,attempts:int=3,timeout:int=45)->bytes:
    err=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.read()
        except Exception as e:
            err=e
            if i+1<attempts:
                time.sleep(1+i)
    raise err

def parse_items(asset:str,article:str,raw:bytes):
    obj=json.loads(raw)
    rows=[]
    for item in obj.get("items",[]):
        ts=str(item.get("timestamp",""))
        if len(ts)<8:
            continue
        try:
            day=dt.datetime.strptime(ts[:8],"%Y%m%d").date()
            views=int(item["views"])
        except Exception:
            continue
        if START<=day<=END:
            rows.append({"asset":asset,"article":article,"date":day.isoformat(),"views":views})
    return rows

def asset_stats(rows):
    dates=[dt.date.fromisoformat(r["date"]) for r in rows]
    unique=sorted(set(dates))
    dup=len(dates)-len(unique)
    gaps=[(b-a).days-1 for a,b in zip(unique,unique[1:]) if (b-a).days>1]
    return {
        "rows":len(rows),
        "unique_days":len(unique),
        "coverage":len(unique)/EXPECTED,
        "duplicates":dup,
        "max_gap_days":max(gaps,default=0),
        "first_date":unique[0].isoformat() if unique else None,
        "last_date":unique[-1].isoformat() if unique else None,
        "nonnegative_integer_views":bool(rows) and all(isinstance(r["views"],int) and r["views"]>=0 for r in rows),
    }

def csv_bytes(rows):
    from io import StringIO
    s=StringIO(newline="")
    w=csv.DictWriter(s,fieldnames=["asset","article","date","views"],lineterminator="\n")
    w.writeheader()
    for r in sorted(rows,key=lambda x:(x["asset"],x["date"])):
        w.writerow(r)
    return s.getvalue().encode("utf-8")

def build(attempts=3):
    all_rows=[]
    request_hashes={}
    errors={}
    for asset,article in ASSET_ARTICLE.items():
        for year in (2023,2024,2025):
            key=f"{asset}:{year}"
            url=endpoint(article,year)
            try:
                raw=fetch(url,attempts=attempts)
                request_hashes[key]={"url":url,"raw_sha256":sha256_bytes(raw),"raw_bytes":len(raw)}
                all_rows.extend(parse_items(asset,article,raw))
            except Exception as e:
                errors[key]=f"{type(e).__name__}: {e}"
    stats={asset:asset_stats([r for r in all_rows if r["asset"]==asset]) for asset in ASSET_ARTICLE}
    key_pairs=[(r["asset"],r["date"]) for r in all_rows]
    global_dups=len(key_pairs)-len(set(key_pairs))
    fixed_mapping_present=all(stats[a]["unique_days"]>0 for a in ASSET_ARTICLE)
    no_outside=all(START<=dt.date.fromisoformat(r["date"])<=END for r in all_rows)
    gates={
        "all_requests_succeeded":not errors and len(request_hashes)==12,
        "coverage_ge_99pct_each":all(x["coverage"]>=.99 for x in stats.values()),
        "no_duplicate_asset_date":global_dups==0,
        "views_nonnegative_integer":all(x["nonnegative_integer_views"] for x in stats.values()),
        "no_gap_gt_3_days_each":all(x["max_gap_days"]<=3 for x in stats.values()),
        "start_boundary_each":all(x["first_date"] is not None and x["first_date"]<="2023-01-02" for x in stats.values()),
        "end_boundary_each":all(x["last_date"] is not None and x["last_date"]>="2025-12-30" for x in stats.values()),
        "training_boundary_enforced":no_outside and bool(all_rows),
        "all_fixed_mappings_present":fixed_mapping_present,
        "response_hashes_recorded":len(request_hashes)==12 and all(v["raw_sha256"] for v in request_hashes.values()),
    }
    normalized=csv_bytes(all_rows)
    decision="PASS_DATA_ONLY" if all(gates.values()) else "FAIL_DATA_NO_ALPHA"
    manifest={
        "engine":"V98 Independent","phase":257,"kind":"DATA_ONLY_PUBLIC_ATTENTION",
        "decision":decision,
        "source":"Wikimedia Pageviews REST API",
        "project":"en.wikipedia.org","access":"all-access","agent":"user","granularity":"daily",
        "period_utc":[START.isoformat(),END.isoformat()],"expected_days_per_asset":EXPECTED,
        "asset_article_mapping":ASSET_ARTICLE,
        "asset_stats":stats,"request_hashes":request_hashes,"request_errors":errors,
        "normalized_rows":len(all_rows),"normalized_csv_sha256":sha256_bytes(normalized),
        "gates":gates,
        "alpha_executed":False,"pnl_executed":False,"crypto_price_join":False,
        "direction_selected":False,"parameter_search":False,
        "validation_accessed":False,"holdout_accessed":False,
        "phase083_selection_use":False,"v14_used":False,"v15_used":False,"v99_used":False,
        "preregistration":"research/v98_independent/phase257_wikimedia_attention_prereg.md",
    }
    return normalized,manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",type=Path,default=Path("research/v98_independent/data/phase257_wikimedia_attention"))
    ap.add_argument("--manifest",type=Path,default=Path("research/v98_independent/phase257_wikimedia_attention_manifest.json"))
    ap.add_argument("--attempts",type=int,default=3)
    a=ap.parse_args()
    normalized,manifest=build(attempts=a.attempts)
    a.out_dir.mkdir(parents=True,exist_ok=True)
    (a.out_dir/"pageviews_daily.csv").write_bytes(normalized)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "phase":257,"decision":manifest["decision"],"normalized_rows":manifest["normalized_rows"],
        "normalized_csv_sha256":manifest["normalized_csv_sha256"],
        "asset_stats":manifest["asset_stats"],"gates":manifest["gates"],"errors":manifest["request_errors"]
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
