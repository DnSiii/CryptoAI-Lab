#!/usr/bin/env python3
"""KF official USD-M positioning metrics source-only fixed 20-day probe; NEVER PnL."""
from __future__ import annotations
import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
DATES=("2023-01-15","2023-07-15","2024-01-15","2024-07-15","2024-12-15")
BASE="https://data.binance.vision/data/futures/um/daily/metrics"
OUT=Path(__file__).resolve().parent/"kf_crowding_metrics_source_gate.json"
CROWD_FIELDS=("toptrader","long_short","longshort","taker")

def download(url,limit):
    if not url.startswith(BASE+"/") or not url.endswith((".zip",".zip.CHECKSUM")):
        raise ValueError("KF_FORBIDDEN_SOURCE")
    req=urllib.request.Request(url,headers={"User-Agent":"V98-KF-Independent-Source-Gate/1.0"})
    with urllib.request.urlopen(req,timeout=25) as resp:
        if resp.status!=200 or resp.geturl()!=url: raise ValueError("KF_HTTP_REDIRECT_OR_STATUS")
        raw=resp.read(limit+1)
    if len(raw)>limit:raise ValueError("KF_OVERSIZED_SOURCE")
    return raw

def parse_time(raw):
    s=str(raw).strip()
    if s.isdigit():
        v=int(s)
        if v>=10**15: v/=10**6
        elif v>=10**12: v/=1000
        return dt.datetime.fromtimestamp(v,dt.timezone.utc)
    return dt.datetime.fromisoformat(s.replace("Z","+00:00")).replace(
        tzinfo=dt.timezone.utc) if dt.datetime.fromisoformat(s.replace("Z","+00:00")).tzinfo is None else dt.datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(dt.timezone.utc)

def probe(asset,day):
    if asset not in ASSETS or day not in DATES:raise ValueError("KF_FORBIDDEN_SCOPE")
    name=f"{asset}-metrics-{day}.zip"
    url=f"{BASE}/{asset}/{name}"
    record={"asset":asset,"day":day,"publisher_url":url,"source_only":True}
    try:
        parts=download(url+".CHECKSUM",4096).decode("utf-8-sig").strip().split()
        if len(parts)!=2 or parts[1].lstrip("./*")!=name or len(parts[0])!=64:
            raise ValueError("KF_PUBLISHER_CHECKSUM_SCHEMA")
        sha=parts[0].lower()
        if any(c not in "0123456789abcdef" for c in sha):
            raise ValueError("KF_PUBLISHER_CHECKSUM_HEX")
        raw=download(url,25000000)
        if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("KF_PUBLISHER_SHA_MISMATCH")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.namelist()!=[name[:-4]+".csv"]:raise ValueError("KF_ZIP_MEMBER")
            member=z.read(z.namelist()[0])
        if len(member)>100000000:raise ValueError("KF_CSV_OVERSIZED")
        reader=csv.DictReader(io.StringIO(member.decode("utf-8-sig")))
        header=reader.fieldnames or []
        normalized=[x.lower().strip() for x in header]
        crowd=[x for x in header if any(k in x.lower().replace("-","_") for k in CROWD_FIELDS)]
        timecol=next((x for x in header if x.lower().strip() in ("create_time","timestamp","time","date","open_time")),None)
        if not timecol or not crowd:raise ValueError("KF_NO_TIMESTAMP_OR_CROWDING_FIELDS")
        timestamps=[]
        negative=0
        for row in reader:
            timestamps.append(parse_time(row[timecol]))
            for col in crowd:
                val=row.get(col,"").strip()
                if val:
                    x=float(val)
                    if not (x==x and abs(x)!=float("inf") and x>=0):negative+=1
        expected=dt.date.fromisoformat(day)
        hours={x.hour for x in timestamps if x.date()==expected}
        ordered=all(a<b for a,b in zip(timestamps,timestamps[1:]))
        unique=len(timestamps)==len(set(timestamps))
        in_day=all(x.date()==expected for x in timestamps)
        full=len(hours)==24 and in_day and ordered and unique and negative==0
        record.update(status="PUBLISHER_VERIFIED",sha256=sha,csv_rows=len(timestamps),
                      header=header,crowding_fields=crowd,observed_utc_hours=len(hours),
                      first_timestamp=timestamps[0].isoformat() if timestamps else None,
                      last_timestamp=timestamps[-1].isoformat() if timestamps else None,
                      full_utc_day=full,strict_time_order=ordered,unique_timestamps=unique,
                      invalid_physical_fields=negative)
    except urllib.error.HTTPError as e:
        record.update(status="PUBLISHER_404" if e.code==404 else "HTTP_ERROR",http_status=e.code)
    except Exception as e:
        record.update(status="TRANSPORT_OR_SCHEMA_ERROR",error=type(e).__name__+": "+str(e)[:180])
    return record

def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(lambda x:probe(*x),((a,d) for a in ASSETS for d in DATES)))
    verified=sum(r["status"]=="PUBLISHER_VERIFIED" for r in rows)
    full=sum(r.get("full_utc_day",False) for r in rows)
    invalid=sum(r.get("invalid_physical_fields",0) for r in rows)
    failures=sum(r["status"] not in ("PUBLISHER_VERIFIED","PUBLISHER_404") for r in rows)
    decision=("PASS_SAMPLE_SOURCE_ONLY_PUBLICATION_LAG_UNRESOLVED" if verified>=19 and full>=19 and invalid==0 and failures==0 else
              "REJECT_OR_BLOCK_SOURCE_FEASIBILITY_NO_PNL")
    result={"candidate":"KF","source_only":True,"economic_pnl_computed":False,
            "validation_2025_accessed":False,"future_holdout_accessed":False,
            "external_benchmarks_accessed":False,"live_trading_authorized":False,
            "publication_lag_verified":False,"full_2023_2024_history_authenticated":False,
            "fixed_asset_days":20,"publisher_verified":verified,"full_utc_days":full,
            "physical_invalid":invalid,"transport_or_schema_failures":failures,
            "decision":decision,"results":rows}
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("KF_SOURCE_GATE",decision,"verified",verified,"full",full,"errors",failures,flush=True)
    for row in rows:
        print("KF_DAY",row["asset"],row["day"],row["status"],
              row.get("csv_rows"),row.get("observed_utc_hours"),row.get("error",""),flush=True)
    return result

if __name__=="__main__":main()
