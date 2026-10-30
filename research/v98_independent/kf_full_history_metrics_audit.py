#!/usr/bin/env python3
"""KF independent full 2023-24 original USD-M metrics archive integrity audit; NO PnL."""
from __future__ import annotations
import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import urllib.error
import zipfile
from pathlib import Path
from kf_crowding_metrics_source_gate import ASSETS,BASE,download,parse_time,CROWD_FIELDS

START=dt.date(2023,1,1)
END=dt.date(2024,12,31)
OUT=Path(__file__).resolve().parent/"kf_full_history_metrics_audit.json"
def all_dates():
    return [START+dt.timedelta(days=i) for i in range((END-START).days+1)]
def inspect(asset,day):
    assert asset in ASSETS and START<=day<=END
    ds=day.isoformat()
    name=f"{asset}-metrics-{ds}.zip"
    url=f"{BASE}/{asset}/{name}"
    rec={"asset":asset,"day":ds}
    try:
        check=download(url+".CHECKSUM",4096).decode("utf-8-sig").strip().split()
        if len(check)!=2 or check[1].lstrip("./*")!=name or len(check[0])!=64:
            raise ValueError("KF_CHECKSUM_SCHEMA")
        sha=check[0].lower()
        if any(c not in "0123456789abcdef" for c in sha):raise ValueError("KF_SHA_FORMAT")
        raw=download(url,25000000)
        if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("KF_SHA_MISMATCH")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.namelist()!=[name[:-4]+".csv"]:raise ValueError("KF_MEMBER_MISMATCH")
            member=z.read(z.namelist()[0])
        if len(member)>100000000:raise ValueError("KF_MEMBER_TOO_LARGE")
        reader=csv.DictReader(io.StringIO(member.decode("utf-8-sig")))
        header=reader.fieldnames or []
        tcol=next((x for x in header if x.lower().strip() in ("create_time","timestamp","time","date","open_time")),None)
        crowd=[x for x in header if any(k in x.lower().replace("-","_") for k in CROWD_FIELDS)]
        if not tcol or not crowd:raise ValueError("KF_SCHEMA_NO_TIME_OR_CROWD")
        times=[]
        invalid=0
        for row in reader:
            times.append(parse_time(row[tcol]))
            for c in crowd:
                s=(row.get(c) or "").strip()
                if not s: invalid+=1;continue
                try:
                    f=float(s)
                    if not (f==f and abs(f)!=float("inf") and f>=0):invalid+=1
                except ValueError:invalid+=1
        expected=[dt.datetime.combine(day,dt.time(0),dt.timezone.utc)+dt.timedelta(minutes=5*i) for i in range(288)]
        complete=times==expected and invalid==0
        rec.update(status="PUBLISHER_VERIFIED",sha256=sha,rows=len(times),
                   strictly_ordered=all(a<b for a,b in zip(times,times[1:])),
                   five_minute_grid=times==expected,invalid_values=invalid,
                   eligible=complete)
    except urllib.error.HTTPError as exc:
        rec.update(status="PUBLISHER_404" if exc.code==404 else "HTTP_ERROR",http_status=exc.code,eligible=False)
    except Exception as exc:
        rec.update(status="SOURCE_OR_TRANSPORT_ERROR",error=type(exc).__name__+": "+str(exc)[:120],eligible=False)
    return rec

def main():
    dates=all_dates()
    assert len(dates)==731
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(lambda pair:inspect(*pair),((a,d) for a in ASSETS for d in dates)))
    assert len(records)==2924
    eligible=sum(r["eligible"] for r in records)
    sha_mismatch=sum("SHA_MISMATCH" in r.get("error","") for r in records)
    transport=sum(r["status"] in ("HTTP_ERROR","SOURCE_OR_TRANSPORT_ERROR") for r in records)
    max_gap=0
    per_asset={}
    for asset in ASSETS:
        arr=[r for r in records if r["asset"]==asset]
        gap=0;longest=0
        for r in arr:
            gap=0 if r["eligible"] else gap+1
            longest=max(longest,gap)
        max_gap=max(max_gap,longest)
        per_asset[asset]={"eligible":sum(r["eligible"] for r in arr),
                          "invalid_days":sum(not r["eligible"] for r in arr),
                          "max_consecutive_invalid_days":longest}
    decision=("PASS_FULL_SOURCE_ONLY_PUBLICATION_LAG_UNRESOLVED" if eligible>=2895 and max_gap<=1 and sha_mismatch==0 and transport==0 else
              "BLOCK_FULL_SOURCE_NO_ECONOMIC_PNL")
    report={"candidate":"KF","source_only":True,"economic_pnl_computed":False,
            "validation_2025_accessed":False,"holdout_accessed":False,"benchmark_internals_accessed":False,
            "archive_asof_publication_proven":False,"live_trading_authorized":False,
            "fixed_asset_days":2924,"eligible_asset_days":eligible,"invalid_asset_days":2924-eligible,
            "publisher_sha_mismatches":sha_mismatch,"transport_or_schema_errors":transport,
            "max_consecutive_invalid_days":max_gap,"per_asset":per_asset,
            "decision":decision,"records":records}
    OUT.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("KF_FULL_HISTORY",decision,"eligible",eligible,"invalid",2924-eligible,
          "max_gap",max_gap,"sha_mismatch",sha_mismatch,"transport",transport,flush=True)
    for asset,data in per_asset.items():print("KF_ASSET",asset,data,flush=True)
    for row in records:
        if not row["eligible"]:print("KF_INVALID",row["asset"],row["day"],row["status"],
                                   row.get("rows"),row.get("invalid_values"),row.get("strictly_ordered"),
                                   row.get("error",""),flush=True)
    return report
if __name__=="__main__":main()
