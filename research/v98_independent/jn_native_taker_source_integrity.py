#!/usr/bin/env python3
"""JN source-only: authenticated Binance USD-M hourly taker-buy quote, 2022-12..2024-12.
No 2025+, PnL, benchmark internals, paper or live. Fail closed on missing checksum.
"""
from __future__ import annotations
import calendar,concurrent.futures,csv,hashlib,io,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from phase803_training_ohlc_official_replay import (
    ASSETS,MONTHS,BASE,PINS,download,checksum)
from phase1260_aj_authenticated_source_digest import HOURS,START

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"jn_native_taker_flow_source.csv"
RECEIPT=ROOT/"jn_native_taker_flow_source_receipt.json"
COLS=("open","high","low","close","quote_volume")
RAW_COLS=("open_time","open","high","low","close","volume","close_time",
          "quote_volume","trade_count","taker_buy_base","taker_buy_quote","ignore")

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def one_month(asset,month):
    if asset not in ASSETS or month not in MONTHS:
        raise ValueError("JN_MONTH_OR_ASSET_FIREWALL")
    name=f"{asset}-1h-{month}.zip"
    url=f"{BASE}/{asset}/1h/{name}"
    official=checksum(download(url+".CHECKSUM"),name)
    raw=download(url)
    actual=sha(raw)
    if actual!=official:raise ValueError("JN_OFFICIAL_ZIP_SHA_"+asset+"_"+month)
    member=f"{asset}-1h-{month}.csv"
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=[member]:raise ValueError("JN_ARCHIVE_MEMBER")
        csvbytes=z.read(member)
    df=pd.read_csv(io.BytesIO(csvbytes),dtype=str,keep_default_na=False)
    if len(df.columns)!=12 or str(df.columns[0]).strip().lower()!="open_time":
        raise ValueError("JN_RAW_12_COLUMN_SCHEMA")
    df.columns=list(RAW_COLS)
    y,m=map(int,month.split("-"))
    first=int(datetime(y,m,1,tzinfo=timezone.utc).timestamp()*1000)
    expected=np.arange(first,first+calendar.monthrange(y,m)[1]*24*3600000,3600000,dtype=np.int64)
    opened=pd.to_numeric(df["open_time"],errors="raise").to_numpy(dtype=np.int64)
    closed=pd.to_numeric(df["close_time"],errors="raise").to_numpy(dtype=np.int64)
    if len(opened)!=len(expected) or not np.array_equal(opened,expected) or not np.array_equal(closed,opened+3599999):
        raise ValueError("JN_MONTHLY_UTC_CHRONOLOGY_"+asset+"_"+month)
    vals={k:pd.to_numeric(df[k],errors="raise").to_numpy(dtype=float) for k in
          (*COLS,"trade_count","taker_buy_quote")}
    if any(not np.isfinite(v).all() for v in vals.values()):
        raise ValueError("JN_NONFINITE_SOURCE")
    q=vals["quote_volume"];buy=vals["taker_buy_quote"]
    if (np.any(q<0) or np.any(buy<0) or np.any(buy>q*(1.+1e-8)+1e-8)
        or np.any(vals["trade_count"]<0)):
        raise ValueError("JN_TAKER_QUOTE_BOUNDS")
    return asset,month,actual,opened,vals

def run():
    if len(MONTHS)!=25 or MONTHS[0]!="2022-12" or MONTHS[-1]!="2024-12":
        raise ValueError("JN_TRAINING_CALENDAR_FIREWALL")
    canonical={}
    for asset in ASSETS:
        path=ROOT/"phase243_clean4_canonical"/(asset+"_1h.csv")
        raw=path.read_bytes()
        pin,size=PINS[asset]
        if sha(raw)!=pin or len(raw)!=size:
            raise ValueError("JN_PINNED_CANONICAL_SOURCE_"+asset)
        df=pd.read_csv(path)
        if len(df)!=HOURS:raise ValueError("JN_CANONICAL_HOURS")
        canonical[asset]=df
    tasks=[(a,m) for a in ASSETS for m in MONTHS]
    results={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(one_month,a,m) for a,m in tasks]
        for future in concurrent.futures.as_completed(futures):
            asset,month,digest,times,vals=future.result()
            results[(asset,month)]=(digest,times,vals)
    expected=(pd.date_range(START,periods=HOURS,freq="h",tz="UTC").asi8//1000000).astype(np.int64)
    ratios={};digests={}
    for asset in ASSETS:
        rows=[results[(asset,m)] for m in MONTHS]
        times=np.concatenate([x[1] for x in rows])
        if not np.array_equal(times,expected):raise ValueError("JN_FULL_UTC_CHRONOLOGY_"+asset)
        cols={k:np.concatenate([x[2][k] for x in rows]) for k in
              (*COLS,"trade_count","taker_buy_quote")}
        df=canonical[asset]
        for k in COLS:
            v=pd.to_numeric(df[k],errors="raise").to_numpy(dtype=float)
            if not np.allclose(cols[k],v,rtol=2e-10,atol=1e-8):
                raise ValueError("JN_CROSS_PINNED_OHLC_QUOTE_MISMATCH_"+asset+"_"+k)
        q=cols["quote_volume"];b=cols["taker_buy_quote"]
        ratio=np.where(q>0,b/np.maximum(q,1e-9),np.nan)
        if np.any((q>0)&((ratio<0)|(ratio>1.+1e-8))):
            raise ValueError("JN_TAKER_RATIO_INVALID_"+asset)
        ratios[asset]=ratio
        digests[asset]=sha(np.nan_to_num(ratio,nan=-1.).astype("<f8").tobytes())
    out=pd.DataFrame({"open_time":pd.to_datetime(expected,unit="ms",utc=True).strftime("%Y-%m-%dT%H:%M:%SZ")})
    for asset in ASSETS:out[asset]=ratios[asset]
    manifest={
        "architecture":"JN","source_only":True,"training_only":True,
        "validation_2025_read":False,"external_benchmarks_used":False,
        "trading_authorized":False,"assets":list(ASSETS),"hours":HOURS,
        "months":list(MONTHS),"official_archive_sha256":{
            asset:{m:results[(asset,m)][0] for m in MONTHS} for asset in ASSETS},
        "canonical_pins":{asset:PINS[asset][0] for asset in ASSETS},
        "taker_ratio_sha256":digests,
        "nonpositive_quote_hours":{a:int(np.isnan(ratios[a]).sum()) for a in ASSETS},
        "decision":"PASS_JN_NATIVE_TAKER_SOURCE_INTEGRITY_ONLY_NOT_ECONOMIC"}
    OUT.write_text(out.to_csv(index=False,float_format="%.17g"))
    RECEIPT.write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    print("JN_NATIVE_TAKER_SOURCE_ONLY",manifest["decision"],
          "archives",len(tasks),"hours",HOURS,
          "ratio_sha",json.dumps(digests,sort_keys=True),flush=True)
    return manifest

if __name__=="__main__":run()
