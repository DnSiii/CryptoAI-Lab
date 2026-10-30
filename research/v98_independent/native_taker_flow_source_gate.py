#!/usr/bin/env python3
"""V98 native taker-flow source ONLY: exact pinned Binance Clean-4 2022-12..2024-12."""
from __future__ import annotations
import csv,hashlib,io,json,re,time,zipfile
from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
MONTHS=pd.period_range("2022-12","2024-12",freq="M").astype(str).tolist()
HOURS=18288
EXPECTED=pd.date_range("2022-12-01",periods=HOURS,freq="h",tz="UTC")
FIELDS=("open_time","open","high","low","close","volume","close_time",
        "quote_volume","trade_count","taker_buy_base","taker_buy_quote","ignore")
CHECKSUM=re.compile(rb"^([a-fA-F0-9]{64})\s+\*?([^\s]+)\s*$")

def sha(b):return hashlib.sha256(b).hexdigest()

def download(url,limit):
    last=None
    for i in range(4):
        try:
            with urlopen(Request(url,headers={"User-Agent":"V98-Independent-Native-Taker-Source/1.0"}),timeout=45) as r:
                if not r.geturl().startswith("https://data.binance.vision/data/futures/um/"):
                    raise ValueError("UNEXPECTED_REDIRECT")
                b=r.read(limit+1)
            if not b or len(b)>limit:raise ValueError("EMPTY_OR_OVERSIZED")
            return b
        except Exception as exc:
            last=exc
            if i<3:time.sleep(1+i)
    raise RuntimeError("SOURCE_DOWNLOAD_"+str(last))

def original(asset,month,pin):
    name=f"{asset}-1h-{month}.zip"
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{asset}/1h/{name}"
    side=download(url+".CHECKSUM",2048)
    match=CHECKSUM.fullmatch(side.strip())
    if not match or match.group(2).decode()!=name:
        raise ValueError("PUBLISHER_CHECKSUM_FORMAT")
    b=download(url,12_000_000)
    digest=sha(b)
    if digest!=match.group(1).decode().lower() or digest!=pin["archive_sha256"]:
        raise ValueError("PUBLISHER_OR_FROZEN_ARCHIVE_SHA")
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        members=z.infolist()
        if len(members)!=1 or members[0].filename!=name[:-4]+".csv" or members[0].is_dir():
            raise ValueError("ZIP_MEMBER")
        raw=z.read(members[0])
    if sha(raw)!=pin["member_sha256"]:
        raise ValueError("FROZEN_MEMBER_SHA")
    first=raw.splitlines()[0].decode("utf-8-sig").split(",")[0].strip().strip('"').lower()
    header=0 if first=="open_time" else None
    df=pd.read_csv(io.BytesIO(raw),header=header,dtype=str,keep_default_na=False)
    if len(df.columns)!=12 or len(df)!=pin["rows"]:
        raise ValueError("ORIGINAL_SCHEMA_OR_ROWS")
    df.columns=FIELDS
    expected=pd.date_range(month+"-01",periods=len(df),freq="h",tz="UTC")
    timestamps=pd.to_datetime(pd.to_numeric(df["open_time"],errors="raise"),unit="ms",utc=True)
    if not timestamps.equals(pd.Series(expected)):
        raise ValueError("ORIGINAL_HOURLY_UTC")
    numbers={}
    for field in FIELDS[1:]:
        if field in ("close_time","ignore"):continue
        a=pd.to_numeric(df[field],errors="raise").to_numpy(dtype=float)
        if not np.isfinite(a).all():raise ValueError("NONFINITE_"+field)
        numbers[field]=a
    o,h,l,c,v,q,tb,tq=[numbers[x] for x in
                         ("open","high","low","close","volume","quote_volume","taker_buy_base","taker_buy_quote")]
    if (np.any(o<=0) or np.any(l<=0) or np.any(l>np.minimum(o,c)) or
        np.any(h<np.maximum(o,c)) or np.any(v<0) or np.any(q<0) or
        np.any(tb<0) or np.any(tq<0) or
        np.any(tb>v+1e-7) or np.any(tq>q+1e-5)):
        raise ValueError("NATIVE_PHYSICAL_GEOMETRY")
    if np.any((tb==0)!=(tq==0)) or np.any((v==0)!=(q==0)):
        raise ValueError("ZERO_VOLUME_CONTRADICTION")
    nonzero=tb>0
    if np.any(tq[nonzero]<tb[nonzero]*l[nonzero]-1e-5) or np.any(tq[nonzero]>tb[nonzero]*h[nonzero]+1e-5):
        raise ValueError("TAKER_VWAP_OUTSIDE_BAR")
    return timestamps,numbers,{"asset":asset,"month":month,"archive_sha256":digest,
                              "member_sha256":sha(raw),"rows":len(df)}

def run():
    with open(ROOT/"phase243_clean4_source_manifest.json") as f:manifest=json.load(f)
    canonical={}
    for asset in ASSETS:
        p=ROOT/"phase243_clean4_canonical"/(asset+"_1h.csv")
        df=pd.read_csv(p)
        ts=pd.to_datetime(df["open_time"],utc=True)
        if len(df)!=HOURS or not ts.equals(pd.Series(EXPECTED)):
            raise ValueError("PINNED_CANONICAL_UTC_"+asset)
        canonical[asset]=df
    output=[];receipts=[]
    # Bounded concurrency; each result is reconciled against frozen canonical.
    def task(asset,month):
        return asset,month,original(asset,month,manifest["prices"][asset]["months"][month])
    jobs=[(asset,month) for asset in ASSETS for month in MONTHS]
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending={pool.submit(task,a,m):(a,m) for a,m in jobs}
        for future in as_completed(pending):
            asset,month=pending[future]
            try:_,_,(ts,nums,receipt)=future.result()
            except Exception as exc:
                raise ValueError(f"FAIL_SOURCE_{asset}_{month}_{exc}") from exc
            expected=canonical[asset].loc[
                canonical[asset]["open_time"].str.startswith(month),:]
            if len(expected)!=len(ts) or not pd.to_datetime(expected["open_time"],utc=True).reset_index(drop=True).equals(ts):
                raise ValueError(f"CANONICAL_MONTH_{asset}_{month}")
            for field in ("open","high","low","close","volume","quote_volume"):
                pinned=pd.to_numeric(expected[field],errors="raise").to_numpy(dtype=float)
                if not np.allclose(pinned,nums[field],rtol=1e-9,atol=1e-7):
                    raise ValueError(f"CANONICAL_{field}_{asset}_{month}")
            for i,t in enumerate(ts):
                quote=float(nums["quote_volume"][i])
                output.append((t.isoformat(),asset,float(nums["taker_buy_base"][i]),
                               float(nums["taker_buy_quote"][i]),float(nums["volume"][i]),
                               quote,float(nums["taker_buy_quote"][i]/quote) if quote>0 else 0.))
            receipts.append(receipt)
            print("NATIVE_TAKER_PIN_PASS",asset,month,len(ts),flush=True)
    if len(receipts)!=100 or len(output)!=HOURS*4:
        raise ValueError("COVERAGE_100_ARCHIVES_73152_ASSET_HOURS")
    output.sort(key=lambda row:(row[0],ASSETS.index(row[1])))
    dest=ROOT/"native_taker_flow_clean4_2022_2024.csv"
    with dest.open("w",newline="") as f:
        w=csv.writer(f)
        w.writerow(("open_time","asset","taker_buy_base","taker_buy_quote","total_base","total_quote","taker_buy_quote_share"))
        w.writerows(output)
    result={"decision":"PASS_NATIVE_TAKER_SOURCE_ONLY_NOT_ALPHA","training_only":True,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "trading_authorized":False,"assets":list(ASSETS),"months":len(MONTHS),
            "archives":len(receipts),"asset_hours":len(output),
            "csv_sha256":sha(dest.read_bytes()),
            "source_authentication":"publisher_checksum_plus_prior_frozen_manifest_not_independent_signature",
            "receipts":sorted(receipts,key=lambda x:(x["asset"],x["month"]))}
    with (ROOT/"native_taker_flow_source_receipt.json").open("w") as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print("NATIVE_TAKER_SOURCE",result["decision"],len(output),result["csv_sha256"])
if __name__=="__main__":
    try:run()
    except Exception as exc:
        (ROOT/"native_taker_flow_source_receipt.json").write_text(
            json.dumps({"decision":"BLOCK_NATIVE_TAKER_SOURCE","error":str(exc),
                        "training_only":True,"validation_2025_read":False},indent=2))
        raise
