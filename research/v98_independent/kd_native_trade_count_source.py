#!/usr/bin/env python3
"""KD: official 2022-24 USD-M hourly trade-count source-only attestation; no PnL."""
from __future__ import annotations
import calendar,csv,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase803_training_ohlc_official_replay import ASSETS,MONTHS,BASE,PINS,download,checksum,month_frame
ROOT=Path(__file__).resolve().parent
CSV=ROOT/"kd_trade_count_2022_2024_native.csv"
RECEIPT=ROOT/"kd_trade_count_source_receipt.json"
HOURS=18288
PINNED_COUNT_SHA="3cd3c6e88826d0ed9faa0c9a39c084ab01810ded33609d7d1655a5073dc01a8d"
START=pd.Timestamp("2022-12-01T00:00:00Z")
NAMES=("open_time","open","high","low","close","volume","close_time",
       "quote_volume","trade_count","taker_buy_base","taker_buy_quote","ignore")

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def extract_count(raw,asset,month):
    member=f"{asset}-1h-{month}.csv"
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=[member]:raise ValueError("KD_ARCHIVE_MEMBER_"+asset+month)
        data=z.read(member)
    frame=pd.read_csv(io.BytesIO(data),dtype=str,keep_default_na=False)
    if len(frame.columns)!=12 or frame.columns[0].lower().strip()!="open_time":
        raise ValueError("KD_NATIVE_12COL_SCHEMA")
    frame.columns=list(NAMES)
    n=calendar.monthrange(*map(int,month.split("-")))[1]*24
    if len(frame)!=n:raise ValueError("KD_NATIVE_MONTH_HOURS")
    openms=pd.to_numeric(frame.open_time,errors="raise").to_numpy(dtype=np.int64)
    closems=pd.to_numeric(frame.close_time,errors="raise").to_numpy(dtype=np.int64)
    expected=int(pd.Timestamp(month+"-01T00:00:00Z").timestamp()*1000)+np.arange(n,dtype=np.int64)*3600000
    if not np.array_equal(openms,expected) or not np.array_equal(closems,expected+3599999):
        raise ValueError("KD_NATIVE_UTC_CALENDAR")
    count=pd.to_numeric(frame.trade_count,errors="raise").to_numpy(dtype=np.float64)
    if not np.isfinite(count).all() or np.any(count<0) or np.any(count!=np.floor(count)):
        raise ValueError("KD_NATIVE_INTEGER_COUNT")
    return count.astype(np.int64)

def run():
    if len(MONTHS)!=25 or MONTHS[0]!="2022-12" or MONTHS[-1]!="2024-12":
        raise ValueError("KD_FORBIDDEN_CALENDAR")
    counts={};manifest={}
    for asset in ASSETS:
        original=[];pieces=[];digests={}
        for month in MONTHS:
            name=f"{asset}-1h-{month}.zip"
            url=f"{BASE}/{asset}/1h/{name}"
            official=checksum(download(url+".CHECKSUM"),name)
            raw=download(url)
            if sha(raw)!=official:raise ValueError("KD_PUBLISHER_SHA_"+asset+month)
            digests[month]=official
            pieces.append(month_frame(raw,asset,month))
            original.append(extract_count(raw,asset,month))
        rebuilt=pd.concat(pieces,ignore_index=True).to_csv(index=False,float_format="%.12g").encode()
        pin,size=PINS[asset]
        if len(rebuilt)!=size or sha(rebuilt)!=pin:
            raise ValueError("KD_CROSS_SOURCE_CANONICAL_PIN_"+asset)
        values=np.concatenate(original)
        if len(values)!=HOURS:raise ValueError("KD_ASSET_HOURS")
        counts[asset]=values
        manifest[asset]={"canonical_sha256":pin,"publisher_month_sha256":digests,
                         "zero_trade_hours":int(np.sum(values==0))}
    timestamps=pd.date_range(START,periods=HOURS,freq="h",tz="UTC")
    out=pd.DataFrame({"open_time":timestamps,**counts})
    raw=out.to_csv(index=False).encode()
    if sha(raw)!=PINNED_COUNT_SHA:raise ValueError("KD_IMMUTABLE_COUNT_DIGEST_DRIFT")
    CSV.write_bytes(raw)
    result={"architecture":"KD","source_only":True,"historical_system_pnl_computed":False,
            "validation_2025_read":False,"holdout_accessed":False,
            "external_benchmarks_used":False,"trading_authorized":False,
            "assets":list(ASSETS),"months_per_asset":25,"publisher_archives":100,
            "hours_per_asset":HOURS,"trade_count_csv_sha256":sha(raw),
            "publisher_manifest_sha256":sha(json.dumps(manifest,sort_keys=True).encode()),
            "manifest":manifest,"decision":"PASS_KD_100_PUBLISHER_ZIPS_NATIVE_COUNT_ONLY"}
    RECEIPT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("KD_NATIVE_TRADE_COUNT",result["decision"],"sha",result["trade_count_csv_sha256"],
          "zeros",{a:manifest[a]["zero_trade_hours"] for a in ASSETS},flush=True)
    return result

def load_native(root=ROOT):
    root=Path(root)
    receipt=json.loads((root/RECEIPT.name).read_text())
    if receipt["decision"]!="PASS_KD_100_PUBLISHER_ZIPS_NATIVE_COUNT_ONLY" or receipt["publisher_archives"]!=100:
        raise ValueError("KD_SOURCE_NOT_ATTESTED")
    raw=(root/CSV.name).read_bytes()
    if sha(raw)!=PINNED_COUNT_SHA or receipt["trade_count_csv_sha256"]!=PINNED_COUNT_SHA:
        raise ValueError("KD_TRADE_COUNT_PIN")
    frame=pd.read_csv(io.BytesIO(raw))
    if list(frame.columns)!=["open_time",*ASSETS] or len(frame)!=HOURS:
        raise ValueError("KD_COUNT_SCHEMA")
    ts=pd.to_datetime(frame.open_time,utc=True)
    if not ts.equals(pd.Series(pd.date_range(START,periods=HOURS,freq="h",tz="UTC"))):
        raise ValueError("KD_COUNT_UTC")
    data=frame[list(ASSETS)].to_numpy(dtype=np.float64)
    if not np.isfinite(data).all() or np.any(data<0) or np.any(data!=np.floor(data)):
        raise ValueError("KD_COUNT_INTEGER")
    return data,receipt["trade_count_csv_sha256"]

if __name__=="__main__":run()
