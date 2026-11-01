#!/usr/bin/env python3
"""V98 only: official Binance Vision USD-M premium-index 1h 2022-25 SOURCE ONLY."""
import csv,datetime as dt,hashlib,io,json,math,re,zipfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.request import Request,urlopen

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
BASE="https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines"
START=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
MAX_BYTES=3_000_000

def months():
    y,m=2022,12
    while (y,m)<(2026,1):
        yield f"{y:04d}-{m:02d}"
        m+=1
        if m==13:y,m=y+1,1

def get(url):
    with urlopen(Request(url,headers={"User-Agent":"V98-Independent-Premium-2022-25/1.0"}),timeout=30) as response:
        if response.status!=200:raise ValueError("HTTP_"+str(response.status))
        raw=response.read(MAX_BYTES+1)
    if not raw or len(raw)>MAX_BYTES:raise ValueError("BAD_HTTP_SIZE")
    return raw

def read_vendor_zip(url,name):
    zbytes=get(url)
    check=get(url+".CHECKSUM").decode("utf-8").strip()
    sha=hashlib.sha256(zbytes).hexdigest()
    if not re.fullmatch(r"[a-fA-F0-9]{64}\s+\*?"+re.escape(name),check):
        raise ValueError("VENDOR_CHECKSUM_FORMAT")
    if check.split()[0].lower()!=sha:raise ValueError("VENDOR_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
        if len(z.namelist())!=1 or not z.namelist()[0].endswith(".csv"):
            raise ValueError("ZIP_MEMBER")
        raw=z.read(z.namelist()[0])
    rows=list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    if rows and rows[0][0].lower() in ("open_time","open time","timestamp"):
        rows=rows[1:]
    return sha,hashlib.sha256(raw).hexdigest(),rows

def one(asset,ym):
    name=f"{asset}-1h-{ym}.zip"
    url=f"{BASE}/{asset}/1h/{name}"
    sha,csv_sha,rows=read_vendor_zip(url,name)
    begin=dt.datetime.strptime(ym,"%Y-%m").replace(tzinfo=dt.timezone.utc)
    after=(begin.replace(year=begin.year+1,month=1) if begin.month==12 else begin.replace(month=begin.month+1))
    n=int((after-begin).total_seconds()/3600)
    expected={int(begin.timestamp()*1000)+3600000*k for k in range(n)}
    monthly_stamps=[int(row[0]) for row in rows]
    if len(monthly_stamps)!=len(set(monthly_stamps)) or not set(monthly_stamps).issubset(expected):
        raise ValueError("MONTHLY_DUPLICATE_OR_OUT_OF_SCOPE")
    repair_days=[]
    vendor_by_time={t:sha for t in monthly_stamps}
    missing=sorted(expected-set(monthly_stamps))
    if missing:
        if len(missing)!=24 or any(missing[k]!=missing[0]+k*3600000 for k in range(24)):
            raise ValueError("MISSING_NOT_ONE_COMPLETE_DAY")
        day=dt.datetime.fromtimestamp(missing[0]/1000,dt.timezone.utc).date().isoformat()
        dname=f"{asset}-1h-{day}.zip"
        durl=f"https://data.binance.vision/data/futures/um/daily/premiumIndexKlines/{asset}/1h/{dname}"
        dsha,dcsv_sha,drows=read_vendor_zip(durl,dname)
        dstamps=[int(row[0]) for row in drows]
        if len(dstamps)!=24 or sorted(dstamps)!=missing or len(set(dstamps))!=24:
            raise ValueError("DAILY_REPAIR_CLOCK_OR_DUPLICATE")
        rows.extend(drows)
        for t in dstamps:vendor_by_time[t]=dsha
        repair_days.append({"date":day,"url":durl,"zip_sha256":dsha,
                            "csv_sha256":dcsv_sha,"rows":24})
    rows.sort(key=lambda r:int(r[0]))
    if len(rows)!=n:raise ValueError(f"INCOMPLETE_MONTH_{len(rows)}_OF_{n}")
    out=[]
    for k,row in enumerate(rows):
        if len(row)<5 or int(row[0])!=int(begin.timestamp()*1000)+3600000*k:
            raise ValueError("HOURLY_TIMESTAMP_OR_SCHEMA")
        o,h,l,c=(float(row[x]) for x in (1,2,3,4))
        if not all(math.isfinite(v) and abs(v)<1 for v in (o,h,l,c)):
            raise ValueError("NONFINITE_OR_PREMIUM_RANGE")
        if l>min(o,c)+1e-10 or h<max(o,c)-1e-10:
            raise ValueError("PREMIUM_OHLC_GEOMETRY")
        out.append((asset,(begin+dt.timedelta(hours=k)).isoformat(),o,h,l,c,vendor_by_time[int(row[0])]))
    return {"asset":asset,"month":ym,"url":url,"zip_sha256":sha,
            "csv_sha256":csv_sha,"rows":n,"repair_days":repair_days},out

def main():
    jobs=[(a,m) for a in ASSETS for m in months()]
    report=[];data=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(one,a,m):(a,m) for a,m in jobs}
        for future in as_completed(futures):
            a,m=futures[future]
            try:
                manifest,rows=future.result()
                report.append(manifest);data.extend(rows)
                print("V98_PREMIUM_MONTH",a,m,len(rows),flush=True)
            except Exception as exc:
                report.append({"asset":a,"month":m,"error":type(exc).__name__+":"+str(exc)})
                print("V98_PREMIUM_MONTH_QUARANTINE",a,m,str(exc),flush=True)
    report.sort(key=lambda x:(x["asset"],x["month"]))
    data.sort(key=lambda x:(x[1],x[0]))
    out=Path("v98_premium_2022_2025_verified_hourly.csv")
    with out.open("w",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(("asset","bar_open_utc","premium_open","premium_high","premium_low","premium_close","source_zip_sha256"))
        writer.writerows(data)
    sha=hashlib.sha256(out.read_bytes()).hexdigest()
    missing=sum("error" in r for r in report)
    result={"decision":"PASS_PREMIUM_FULL_SOURCE_ONLY_NOT_PNL" if not missing and len(data)==108192 else "INCOMPLETE_PREMIUM_SOURCE_QUARANTINED_NOT_PNL",
            "scope":"CLEAN4_2022_12_TO_2025_12_EXPOSED_TRAINING_ONLY",
            "assets":list(ASSETS),"months":len(jobs),"passed_months":len(jobs)-missing,
            "quarantined_months":missing,"verified_asset_hours":len(data),
            "expected_asset_hours":108192,"hourly_csv_sha256":sha,"manifest":report,
            "pnl_computed":False,"2026_plus_accessed":False,
            "holdout_accessed":False,"exact_event_mark_attested":False}
    Path("v98_premium_2022_2025_source_report.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("V98_PREMIUM_FULL_SOURCE_REPORT",json.dumps({k:v for k,v in result.items() if k!="manifest"},sort_keys=True),flush=True)
    if result["decision"]!="PASS_PREMIUM_FULL_SOURCE_ONLY_NOT_PNL":
        raise SystemExit("V98_PREMIUM_SOURCE_INCOMPLETE_NO_PNL")

if __name__=="__main__":main()
