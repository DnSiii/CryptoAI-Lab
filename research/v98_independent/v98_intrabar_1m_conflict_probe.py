#!/usr/bin/env python3
"""V98 1m daily-vs-monthly publisher provenance forensic; NO strategy or PnL."""
from __future__ import annotations
import csv,hashlib,io,json,math,time,urllib.request,zipfile
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
from phase1260_aj_authenticated_source_digest import load_official
ROOT=Path(__file__).resolve().parent
MONTHLY=ROOT/"v98_intrabar_full_1m_raw"
DAILY=ROOT/"v98_intrabar_conflict_daily_raw"
OUT=ROOT/"v98_intrabar_conflict_forensic_receipt.json"
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
DATES=("2023-08-16","2023-11-10","2023-11-14","2024-10-28")
BASE="https://data.binance.vision/data/futures/um/daily/klines"
def sha(b):return hashlib.sha256(b).hexdigest()
def get(url):
    last=None
    for k in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"V98-1m-Provenance-Forensic/1.0"})
            with urllib.request.urlopen(req,timeout=40) as r:
                if r.status!=200:raise ValueError("HTTP_"+str(r.status))
                return r.read()
        except Exception as e:last=e;time.sleep(1+k)
    raise ValueError("PROVIDER_FETCH:"+str(last))
def parse(raw,name):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files=[x for x in z.namelist() if not x.endswith("/")]
        if len(files)!=1 or files[0].split("/")[-1]!=name[:-4]+".csv":
            raise ValueError("ZIP_MEMBER")
        reader=csv.reader(io.TextIOWrapper(z.open(files[0]),encoding="utf-8-sig"))
        result=[]
        for row in reader:
            if row and row[0].strip().lower() in ("open_time","opentime"):continue
            if len(row)<11:raise ValueError("SCHEMA")
            t=int(row[0]);v=tuple(float(row[j]) for j in (1,2,3,4,5,7))
            if not all(math.isfinite(x) for x in v):raise ValueError("NONFINITE")
            o,h,l,c,vol,q=v
            if min(o,h,l,c)<=0 or h<max(o,c) or l>min(o,c) or vol<0 or q<0:
                raise ValueError("GEOMETRY")
            result.append((t,*v))
    return result
def same(a,b,price):
    return abs(a-b)<=max(1e-8 if price else 1e-6,(1e-10 if price else 1e-8)*max(abs(a),abs(b)))
def compare_hours(bars,anchor,epoch):
    errors=[]
    if len(bars)!=1440 or [x[0] for x in bars]!=list(range(epoch,epoch+86400000,60000)):
        raise ValueError("DAILY_1440_MINUTE_GRID")
    for hour in range(24):
        chunk=bars[hour*60:(hour+1)*60]
        agg=(chunk[0][1],max(x[2] for x in chunk),min(x[3] for x in chunk),
             chunk[-1][4],sum(x[5] for x in chunk),sum(x[6] for x in chunk))
        t=pd.Timestamp(epoch+hour*3600000,unit="ms",tz="UTC")
        ref=anchor.loc[t]
        for j,col in enumerate(("open","high","low","close","volume","quote_volume")):
            if not same(agg[j],float(ref[col]),j<4):
                errors.append({"hour":hour,"column":col,"got":agg[j],"canonical":float(ref[col])})
    return errors
def main():
    _,manifest=load_official()
    original=json.loads((ROOT/"v98_intrabar_full_1m_primary_receipt.json").read_text())
    DAILY.mkdir(parents=True,exist_ok=True)
    anchors={}
    for a in ASSETS:
        d=pd.read_csv(ROOT/"phase243_clean4_canonical"/(a+"_1h.csv"))
        anchors[a]=d.set_index(pd.to_datetime(d["open_time"],utc=True))
    results=[];faults=[]
    for asset in ASSETS:
        for day in DATES:
            month=day[:7];mname=f"{asset}-1m-{month}.zip";dname=f"{asset}-1m-{day}.zip"
            row={"asset":asset,"date":day}
            try:
                monthly=(MONTHLY/mname).read_bytes()
                previous=next((r for r in original["records"] if r["asset"]==asset and r["month"]==month),None)
                mside=(MONTHLY/(mname+".CHECKSUM")).read_text().split()[0].lower()
                if not previous or sha(monthly)!=mside or previous.get("sha256")!=mside:
                    raise ValueError("ORIGINAL_MONTHLY_SHA")
                url=f"{BASE}/{asset}/1m/{dname}"
                daily=get(url);side=get(url+".CHECKSUM")
                parts=side.decode().split()
                if len(parts) not in (1,2) or sha(daily)!=parts[0].lower():
                    raise ValueError("ORIGINAL_DAILY_SHA")
                if len(parts)==2 and parts[1].lstrip("*").split("/")[-1]!=dname:
                    raise ValueError("DAILY_SIDECAR_NAME")
                (DAILY/dname).write_bytes(daily)
                (DAILY/(dname+".CHECKSUM")).write_bytes(side)
                epoch=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000)
                db=parse(daily,dname)
                mb=[x for x in parse(monthly,mname) if epoch<=x[0]<epoch+86400000]
                de=compare_hours(db,anchors[asset],epoch)
                me=compare_hours(mb,anchors[asset],epoch)
                minute_diffs=[]
                if len(mb)==1440:
                    for i,(d,m) in enumerate(zip(db,mb)):
                        if d[0]!=m[0] or any(not same(d[j],m[j],j<=4) for j in range(1,7)):
                            minute_diffs.append(i)
                else:minute_diffs=list(range(1440))
                row.update({"status":"PASS_AUTHENTICATED","daily_sha256":sha(daily),
                    "monthly_sha256":sha(monthly),"daily_hourly_mismatch_count":len(de),
                    "monthly_hourly_mismatch_count":len(me),
                    "minute_diff_count":len(minute_diffs),
                    "first_daily_hourly_fault":de[:2],"first_monthly_hourly_fault":me[:2],
                    "first_minute_diff":minute_diffs[:3]})
            except Exception as e:
                row.update({"status":"FAIL_SOURCE","error":str(e)[:300]});faults.append(row)
            results.append(row)
            print("V98_1M_CONFLICT",asset,day,row["status"],
                  row.get("daily_hourly_mismatch_count"),row.get("monthly_hourly_mismatch_count"),
                  row.get("minute_diff_count"),row.get("error",""),flush=True)
    ok=[x for x in results if x["status"]=="PASS_AUTHENTICATED"]
    d=sum(x["daily_hourly_mismatch_count"] for x in ok)
    m=sum(x["monthly_hourly_mismatch_count"] for x in ok)
    dif=sum(x["minute_diff_count"] for x in ok)
    decision=("BLOCK_SOURCE_INCOMPLETE" if faults or len(ok)!=16 else
              "QUARANTINE_1M_DAILY_ALSO_CONFLICTS_WITH_PINNED_1H" if d>0 else
              "DAILY_RECONCILES_MONTHLY_DIFFERS_REQUIRES_UNIFORM_FULL_DAILY" if m>0 else
              "FULL_MONTHLY_GATE_STILL_FAILED_NO_PNL")
    report={"decision":decision,"source_only":True,"pnl_computed":False,
        "validation_2025_read":False,"trading_authorized":False,
        "authenticated_asset_days":len(ok),"expected_asset_days":16,
        "daily_hourly_mismatches":d,"monthly_hourly_mismatches":m,
        "minute_differences":dif,"first_faults":faults,"rows":results,
        "canonical_manifest_sha256":sha(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode())}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("V98_1M_CONFLICT_DECISION",decision,"daily",d,"monthly",m,"minute",dif,flush=True)
if __name__=="__main__":main()
