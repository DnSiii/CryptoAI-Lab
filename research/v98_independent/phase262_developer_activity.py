#!/usr/bin/env python3
"""V98 Phase262 ecosystem developer activity DATA_ONLY."""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,os,time,urllib.parse,urllib.request
from pathlib import Path

REPOS={
 "BTCUSDT":("bitcoin/bitcoin","master"),
 "ETHUSDT":("ethereum/go-ethereum","master"),
 "BNBUSDT":("bnb-chain/bsc","master"),
 "SOLUSDT":("anza-xyz/agave","master"),
}
START=dt.datetime(2023,1,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
UA="CryptoAI-Lab-V98-Phase262/1.0 (https://github.com/DnSiii/CryptoAI-Lab)"
API="https://api.github.com"

def sha(b):return hashlib.sha256(b).hexdigest()

def month_bounds(year,month):
    s=dt.datetime(year,month,1,tzinfo=dt.timezone.utc)
    if month==12:n=dt.datetime(year+1,1,1,tzinfo=dt.timezone.utc)
    else:n=dt.datetime(year,month+1,1,tzinfo=dt.timezone.utc)
    return s,n

def req(url,token,attempts=3,timeout=45):
    err=None
    headers={"User-Agent":UA,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
    if token:headers["Authorization"]=f"Bearer {token}"
    for i in range(attempts):
        try:
            r=urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(r,timeout=timeout) as x:return x.read()
        except Exception as e:
            err=e
            if i+1<attempts:time.sleep(1+i)
    raise err

def month_commits(repo,branch,start,next_start,token,attempts=3):
    until=next_start-dt.timedelta(seconds=1)
    page=1;seen={};raw_hash=hashlib.sha256();errors=[]
    while True:
        params=urllib.parse.urlencode({
          "sha":branch,
          "since":start.isoformat().replace("+00:00","Z"),
          "until":until.isoformat().replace("+00:00","Z"),
          "per_page":100,"page":page,
        })
        url=f"{API}/repos/{repo}/commits?{params}"
        try:raw=req(url,token,attempts=attempts)
        except Exception as e:
            errors.append(f"page{page}:{type(e).__name__}: {e}");break
        raw_hash.update(raw);raw_hash.update(b"\n--PAGE--\n")
        arr=json.loads(raw)
        if not isinstance(arr,list):
            errors.append(f"page{page}:non_list_response");break
        for item in arr:
            try:
                sh=str(item["sha"])
                stamp=str(item["commit"]["committer"]["date"])
                d=dt.datetime.fromisoformat(stamp.replace("Z","+00:00"))
            except Exception:
                errors.append(f"page{page}:invalid_commit_shape");continue
            seen[sh]=d
        if len(arr)<100:break
        page+=1
        if page>100:
            errors.append("pagination_exceeded_100_pages");break
    violation=sum(not(start<=d<next_start) for d in seen.values())
    dates=sorted(seen.values())
    return {
      "commit_count":len(seen),
      "first_commit":dates[0].isoformat().replace("+00:00","Z") if dates else None,
      "last_commit":dates[-1].isoformat().replace("+00:00","Z") if dates else None,
      "page_count":page,
      "response_pages_sha256":raw_hash.hexdigest(),
      "timestamp_violations":violation,
      "errors":errors,
    }

def csv_bytes(rows):
    from io import StringIO
    s=StringIO(newline="")
    w=csv.DictWriter(s,fieldnames=["asset","repo","branch","month","commit_count","first_commit","last_commit"],lineterminator="\n")
    w.writeheader()
    for r in sorted(rows,key=lambda x:(x["asset"],x["month"])):w.writerow(r)
    return s.getvalue().encode()

def build(attempts=3):
    token=os.getenv("GITHUB_TOKEN","").strip()
    rows=[];ledger={};errors={}
    for asset,(repo,branch) in REPOS.items():
        for year in (2023,2024,2025):
            for month in range(1,13):
                s,n=month_bounds(year,month);key=f"{asset}:{year:04d}-{month:02d}"
                m=month_commits(repo,branch,s,n,token,attempts=attempts)
                ledger[key]={k:m[k] for k in ("page_count","response_pages_sha256","timestamp_violations")}
                if m["errors"]:errors[key]=m["errors"]
                rows.append({"asset":asset,"repo":repo,"branch":branch,"month":f"{year:04d}-{month:02d}",
                             "commit_count":int(m["commit_count"]),"first_commit":m["first_commit"] or "",
                             "last_commit":m["last_commit"] or ""})
    normalized=csv_bytes(rows)
    per_asset={}
    for asset in REPOS:
        ar=[r for r in rows if r["asset"]==asset]
        per_asset[asset]={
          "months":len(ar),
          "active_months":sum(r["commit_count"]>0 for r in ar),
          "total_commits":sum(r["commit_count"] for r in ar),
          "min_monthly_commits":min((r["commit_count"] for r in ar),default=0),
          "max_monthly_commits":max((r["commit_count"] for r in ar),default=0),
        }
    pairs=[(r["asset"],r["month"]) for r in rows]
    gates={
      "all_144_repo_months_succeeded":not errors and len(rows)==144,
      "exactly_36_months_each":all(x["months"]==36 for x in per_asset.values()),
      "no_duplicate_asset_month":len(pairs)==len(set(pairs)),
      "counts_nonnegative_integer":all(isinstance(r["commit_count"],int) and r["commit_count"]>=0 for r in rows),
      "active_months_ge_24_each":all(x["active_months"]>=24 for x in per_asset.values()),
      "total_commits_ge_100_each":all(x["total_commits"]>=100 for x in per_asset.values()),
      "no_timestamp_violations":all(x["timestamp_violations"]==0 for x in ledger.values()) if ledger else False,
      "training_boundary_enforced":all(r["month"]<"2026-01" for r in rows) and bool(rows),
      "response_hash_ledger_complete":len(ledger)==144 and all(x["response_pages_sha256"] for x in ledger.values()),
      "normalized_hash_recorded":bool(normalized),
    }
    decision="PASS_DATA_ONLY" if all(gates.values()) else "FAIL_DATA_NO_ALPHA"
    manifest={
      "engine":"V98 Independent","phase":262,"kind":"DATA_ONLY_DEVELOPER_ACTIVITY",
      "decision":decision,"source":"GitHub REST API commit history",
      "period_utc":["2023-01-01","2025-12-31"],"repo_mapping":{a:{"repo":r,"branch":b} for a,(r,b) in REPOS.items()},
      "normalized_rows":len(rows),"per_asset":per_asset,"request_errors":errors,
      "response_hash_ledger":ledger,"normalized_csv_sha256":sha(normalized),
      "authenticated_request_used":bool(token),"gates":gates,
      "alpha_executed":False,"pnl_executed":False,"crypto_price_join":False,
      "direction_selected":False,"parameter_search":False,"validation_accessed":False,"holdout_accessed":False,
      "phase083_selection_use":False,"v14_used":False,"v15_used":False,"v99_used":False,
      "preregistration":"research/v98_independent/phase262_developer_activity_prereg.md"
    }
    return normalized,manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",type=Path,default=Path("research/v98_independent/data/phase262_developer_activity"))
    ap.add_argument("--manifest",type=Path,default=Path("research/v98_independent/phase262_developer_activity_manifest.json"))
    ap.add_argument("--attempts",type=int,default=3);a=ap.parse_args()
    data,m=build(a.attempts)
    a.out_dir.mkdir(parents=True,exist_ok=True);(a.out_dir/"monthly_commits.csv").write_bytes(data)
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"phase":262,"decision":m["decision"],"normalized_rows":m["normalized_rows"],
      "per_asset":m["per_asset"],"errors":m["request_errors"],"gates":m["gates"],
      "normalized_csv_sha256":m["normalized_csv_sha256"]},indent=2,sort_keys=True))
if __name__=="__main__":main()
