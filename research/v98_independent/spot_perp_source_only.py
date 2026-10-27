#!/usr/bin/env python3
"""V98 Independent SPOT source-only Binance monthly 1h SHA256/UTC audit.
Strict preregistration: Dec-2022 through Dec-2024 Clean-4 only. No 2025/PnL.
"""
from __future__ import annotations
import csv,datetime as dt,hashlib,io,json,time,urllib.request,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
MONTHS=((2022,12),)+tuple((year,month) for year in (2023,2024) for month in range(1,13))
EXPECTED_HOURS=18288
SOURCE="https://data.binance.vision/data/spot/monthly/klines"
OUT=ROOT/"spot_perp_source_only"
FIELDS=("asset","open_time_ms","open","high","low","close","quote_volume")

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def get(url:str)->bytes:
    error=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"V98-independent-source-audit/1.0"})
            with urllib.request.urlopen(req,timeout=35) as response:
                raw=response.read()
            if not raw:raise ValueError("EMPTY_PROVIDER_OBJECT")
            return raw
        except Exception as exc:
            error=exc
            if attempt<2:time.sleep(2*(attempt+1))
    raise RuntimeError("SOURCE_OBJECT_UNAVAILABLE "+url+" "+repr(error))

def month_hours(year:int,month:int)->list[int]:
    start=dt.datetime(year,month,1,tzinfo=dt.timezone.utc)
    end=dt.datetime(year+1,1,1,tzinfo=dt.timezone.utc) if month==12 else dt.datetime(year,month+1,1,tzinfo=dt.timezone.utc)
    return list(range(int(start.timestamp()*1000),int(end.timestamp()*1000),3600000))

def parse_zip(raw:bytes,expected_name:str,asset:str,expected:list[int])->list[tuple]:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        if names!=[expected_name]:
            raise ValueError("SPOT_ZIP_MEMBER_MISMATCH "+asset+" "+str(names))
        with z.open(names[0]) as f:
            content=io.TextIOWrapper(f,encoding="utf-8",newline="")
            rows=list(csv.reader(content))
    if len(rows)!=len(expected):
        raise ValueError("SPOT_HOURLY_COUNT "+asset+" "+str(len(rows))+" != "+str(len(expected)))
    out=[]
    for i,(row,timestamp) in enumerate(zip(rows,expected)):
        if len(row)<11:raise ValueError("SPOT_SCHEMA "+asset+" "+str(i))
        try:
            got=int(row[0])
            o,h,l,c,q=(float(row[j]) for j in (1,2,3,4,7))
        except Exception as exc:raise ValueError("SPOT_PARSE "+asset+" "+str(i)) from exc
        if got!=timestamp:raise ValueError("SPOT_UTC_GRID "+asset+" "+str(i))
        import math
        if (not all(map(math.isfinite,(o,h,l,c,q))) or
            min(o,h,l,c)<=0 or q<0 or l>min(o,c) or h<max(o,c)):
            raise ValueError("SPOT_OHLC_GEOMETRY "+asset+" "+str(i))
        out.append((asset,str(got),row[1],row[2],row[3],row[4],row[7]))
    return out

def canonical(cache:dict)->bytes:
    rows=[]
    for asset in ASSETS:
        for year,month in MONTHS:
            name=f"{asset}-1h-{year}-{month:02d}.csv"
            rows.extend(parse_zip(cache[(asset,year,month)],name,asset,month_hours(year,month)))
    if len(rows)!=len(ASSETS)*EXPECTED_HOURS:
        raise ValueError("SPOT_TOTAL_ASSET_HOURS")
    stream=io.StringIO(newline="")
    writer=csv.writer(stream,lineterminator="\n")
    writer.writerow(FIELDS)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    cache={};archive_receipts=[]
    for asset in ASSETS:
        for year,month in MONTHS:
            zipname=f"{asset}-1h-{year}-{month:02d}.zip"
            url=f"{SOURCE}/{asset}/1h/{zipname}"
            zipped=get(url)
            checksum=get(url+".CHECKSUM").decode("ascii").strip().split()[0].lower()
            if len(checksum)!=64 or any(c not in "0123456789abcdef" for c in checksum):
                raise ValueError("SPOT_PROVIDER_CHECKSUM_SCHEMA "+zipname)
            digest=sha(zipped)
            if digest!=checksum:
                raise ValueError("SPOT_PROVIDER_SHA256_MISMATCH "+zipname)
            cache[(asset,year,month)]=zipped
            archive_receipts.append({"asset":asset,"month":f"{year}-{month:02d}",
                "zip":zipname,"provider_sha256":checksum,"actual_sha256":digest,
                "bytes":len(zipped),"hours":len(month_hours(year,month))})
            print("SPOT_ARCHIVE_VERIFIED",asset,f"{year}-{month:02d}",flush=True)
    a=canonical(cache);b=canonical(cache)
    if a!=b or sha(a)!=sha(b):raise ValueError("SPOT_TWO_PASS_NONDETERMINISM")
    csv_path=OUT/"spot_clean4_2022_2024_1h.csv"
    csv_path.write_bytes(a)
    receipt={"decision":"PASS_SPOT_SOURCE_INTEGRITY_ONLY_NOT_ECONOMIC",
       "training_only":True,"validation_2025_read":False,"data_2026_read":False,
       "historical_system_pnl_computed":False,"alpha_selected":False,
       "external_benchmarks_used":False,"trading_authorized":False,
       "assets":ASSETS,"months_per_asset":len(MONTHS),
       "archive_count":len(archive_receipts),"asset_hours":len(ASSETS)*EXPECTED_HOURS,
       "provider_sha256_count":len(archive_receipts),"two_pass_byte_identical":True,
       "canonical_sha256":sha(a),"canonical_bytes":len(a),
       "archives":archive_receipts}
    (OUT/"spot_source_integrity_receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print("SPOT_SOURCE_PASS",len(archive_receipts),receipt["asset_hours"],sha(a),flush=True)
    return receipt

if __name__=="__main__":
    run()
