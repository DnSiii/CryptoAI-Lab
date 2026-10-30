#!/usr/bin/env python3
"""V98 Independent complete 2022-12..2024-12 1m publisher archive gate; NO alpha/PnL."""
from __future__ import annotations
import calendar,csv,hashlib,io,json,math,re,time,urllib.request,zipfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
from phase1260_aj_authenticated_source_digest import load_official
ROOT=Path(__file__).resolve().parent
RAW=ROOT/"v98_intrabar_full_1m_raw"
OUT=ROOT/"v98_intrabar_full_1m_primary_receipt.json"
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
MONTHS=("2022-12",)+tuple(f"{y}-{m:02d}" for y in (2023,2024) for m in range(1,13))
BASE="https://data.binance.vision/data/futures/um/monthly/klines"
START=int(datetime(2022,12,1,tzinfo=timezone.utc).timestamp()*1000)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def close(a,b,price):
    return abs(a-b)<=max(1e-8 if price else 1e-6,(1e-10 if price else 1e-8)*max(abs(a),abs(b)))
def get(url):
    last=None
    for k in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"V98-Independent-1m-Full-Source/1.0"})
            with urllib.request.urlopen(req,timeout=45) as r:
                if r.status!=200:raise ValueError("HTTP_"+str(r.status))
                return r.read()
        except Exception as exc:
            last=exc;time.sleep(1+k)
    raise ValueError("PROVIDER_FETCH:"+str(last))
def fetch_archive(asset,month):
    name=f"{asset}-1m-{month}.zip"
    url=f"{BASE}/{asset}/1m/{name}"
    record={"asset":asset,"month":month,"archive":name}
    try:
        raw=get(url);side=get(url+".CHECKSUM")
        parts=side.decode("utf-8").strip().split()
        if len(parts) not in (1,2) or not re.fullmatch("[0-9a-fA-F]{64}",parts[0]):
            raise ValueError("PUBLISHER_SIDECAR_SCHEMA")
        if len(parts)==2 and parts[1].lstrip("*").split("/")[-1]!=name:
            raise ValueError("PUBLISHER_SIDECAR_NAME")
        if sha(raw)!=parts[0].lower():raise ValueError("PUBLISHER_SHA256")
        (RAW/name).write_bytes(raw)
        (RAW/(name+".CHECKSUM")).write_bytes(side)
        record.update({"sha256":parts[0].lower(),"bytes":len(raw),"download":"PASS"})
    except Exception as e:
        record.update({"download":"FAIL","error":str(e)[:250]})
    return record
def parse_archive(record,anchors):
    asset=record["asset"];month=record["month"];name=record["archive"]
    y,m=map(int,month.split("-"));days=calendar.monthrange(y,m)[1]
    first=int(datetime(y,m,1,tzinfo=timezone.utc).timestamp()*1000)
    expected=days*1440
    with zipfile.ZipFile(RAW/name) as z:
        names=[x for x in z.namelist() if not x.endswith("/")]
        if len(names)!=1 or names[0].split("/")[-1]!=name[:-4]+".csv":
            raise ValueError("ZIP_MEMBER_NAME")
        stream=io.TextIOWrapper(z.open(names[0]),encoding="utf-8-sig")
        reader=csv.reader(stream)
        count=0;hour=0;agg=None
        for row in reader:
            if row and row[0].strip().lower() in ("open_time","opentime"):continue
            if len(row)<11:raise ValueError("KLINE_SCHEMA")
            t=int(row[0])
            if t!=first+count*60000:
                raise ValueError(f"MINUTE_GRID:index={count}:observed={t}")
            if int(row[6])<t or int(row[6])>t+59999:raise ValueError("CLOSE_TIME")
            vals=[float(row[j]) for j in (1,2,3,4,5,7)]
            if not all(math.isfinite(v) for v in vals):raise ValueError("NONFINITE")
            op,hi,lo,cl,vol,quote=vals
            if min(op,hi,lo,cl)<=0 or hi<max(op,cl) or lo>min(op,cl) or vol<0 or quote<0:
                raise ValueError("GEOMETRY")
            if quote<vol*lo-1e-6*max(1,quote) or quote>vol*hi+1e-6*max(1,quote):
                raise ValueError("QUOTE_BASE_UNIT")
            if count%60==0:agg=[op,hi,lo,cl,vol,quote]
            else:
                agg[1]=max(agg[1],hi);agg[2]=min(agg[2],lo)
                agg[3]=cl;agg[4]+=vol;agg[5]+=quote
            if count%60==59:
                global_hour=(first-START)//3600000+hour
                if not (0<=global_hour<18288):raise ValueError("HOUR_OUTSIDE_TRAINING")
                ref=anchors[asset][global_hour]
                for j in range(6):
                    if not close(agg[j],ref[j],j<4):
                        raise ValueError(f"HOURLY_MISMATCH:hour={hour}:column={j}:got={agg[j]}:ref={ref[j]}")
                hour+=1
            count+=1
        if count!=expected or hour!=days*24:
            raise ValueError(f"MONTH_COVERAGE:minutes={count}/{expected}:hours={hour}/{days*24}")
    return count,hour
def main():
    _,source_manifest=load_official()
    anchors={}
    for a in ASSETS:
        d=pd.read_csv(ROOT/"phase243_clean4_canonical"/(a+"_1h.csv"))
        assert len(d)==18288
        anchors[a]=d[["open","high","low","close","volume","quote_volume"]].to_numpy(dtype=float)
    RAW.mkdir(parents=True,exist_ok=True)
    records=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        tasks=[pool.submit(fetch_archive,a,m) for a in ASSETS for m in MONTHS]
        for task in as_completed(tasks):
            r=task.result()
            records.append(r)
            print("V98_FULL_1M_DOWNLOAD",r["asset"],r["month"],r["download"],r.get("error",""),flush=True)
    records.sort(key=lambda x:(ASSETS.index(x["asset"]),x["month"]))
    for r in records:
        if r["download"]=="PASS":
            try:
                n,h=parse_archive(r,anchors)
                r.update({"status":"PASS","minutes":n,"hours":h})
            except Exception as e:
                r.update({"status":"FAIL","error":str(e)[:350]})
        else:r["status"]="FAIL"
        print("V98_FULL_1M_AUDIT",r["asset"],r["month"],r["status"],r.get("error",""),flush=True)
    passed=[r for r in records if r["status"]=="PASS"]
    minutes=sum(r["minutes"] for r in passed);hours=sum(r["hours"] for r in passed)
    ok=len(passed)==100 and minutes==4389120 and hours==73152
    receipt={"source_only":True,"pnl_computed":False,"validation_2025_read":False,
        "future_holdout_read":False,"benchmarks_read":False,"trading_authorized":False,
        "assets":list(ASSETS),"months":list(MONTHS),"expected_archives":100,
        "passed_archives":len(passed),"verified_minutes":minutes,
        "verified_hourly_aggregates":hours,
        "canonical_manifest_sha256":sha(json.dumps(source_manifest,sort_keys=True,separators=(",",":")).encode()),
        "records":records,"first_faults":[r for r in records if r["status"]!="PASS"][:30],
        "decision":"PASS_FULL_1M_SOURCE_REQUIRES_INDEPENDENT_AUDIT" if ok else "REJECT_FULL_1M_SOURCE_NO_PNL"}
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("V98_FULL_1M_SOURCE",receipt["decision"],len(passed),"/100",minutes,"/4389120",hours,"/73152",flush=True)
if __name__=="__main__":main()
