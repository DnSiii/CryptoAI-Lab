#!/usr/bin/env python3
"""JT contemporaneous 5m downside resilience SOURCE ONLY, no PnL/sign selection."""
from __future__ import annotations
import calendar,concurrent.futures,hashlib,io,json,math
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from phase803_training_ohlc_official_replay import ASSETS,MONTHS,BASE,PINS,download
from phase1260_aj_authenticated_source_digest import HOURS,START
from jq_native_5m_path_source import verify_archive,parse_month,compare_1h

HERE=Path(__file__).resolve().parent
OUT=HERE/"jt_downside_resilience_hourly.csv"
RECEIPT=HERE/"jt_downside_resilience_source_receipt.json"
COLS=("open_time","asset","source_valid","down_beta","down_resilience",
      "cojump_frequency","up_capture")

def canonical_feature(value):
    x=float(value)
    if not math.isfinite(x):raise ValueError("JT_NONFINITE_DERIVED_SOURCE")
    return float(format(x,".12g"))

def source_month(asset,month):
    if asset not in ASSETS or month not in MONTHS:
        raise ValueError("JT_TRAINING_SCOPE")
    name=f"{asset}-5m-{month}.zip"
    url=f"{BASE}/{asset}/5m/{name}"
    data,zipsha,member_sha=verify_archive(download(url),download(url+".CHECKSUM"),name)
    times,ohlc,_=parse_month(data,asset,month)
    df=pd.read_csv(io.BytesIO(data),header=None,dtype=str,keep_default_na=False)
    if str(df.iloc[0,0]).strip().lower()=="open_time":
        df=df.iloc[1:].reset_index(drop=True)
    op=pd.to_numeric(df.iloc[:,1],errors="raise").to_numpy(dtype=float)
    cl=pd.to_numeric(df.iloc[:,4],errors="raise").to_numpy(dtype=float)
    n=len(times)
    if len(op)!=n*12 or np.any(op<=0) or np.any(cl<=0):
        raise ValueError("JT_NATIVE_5M_CLOSE_GEOMETRY")
    op=op.reshape(n,12);cl=cl.reshape(n,12)
    prev=np.column_stack((op[:,0],cl[:,:-1]))
    ret=np.log(cl/prev)
    if not np.isfinite(ret).all():raise ValueError("JT_NATIVE_5M_RETURNS_NONFINITE")
    return (asset,month,zipsha,member_sha,times,ohlc,ret)

def run():
    if HOURS!=18288 or len(ASSETS)!=4 or len(MONTHS)!=25 or MONTHS[-1]!="2024-12":
        raise ValueError("JT_TRAINING_CALENDAR")
    masked=json.loads((HERE/"native_5m_masked_source_receipt.json").read_text())
    raw_mask=(HERE/"native_5m_masked_verified_hourly_features.csv").read_bytes()
    if (masked["decision"]!="MASKED_5M_SOURCE_ONLY_NO_ECONOMIC_AUTHORIZATION"
        or hashlib.sha256(raw_mask).hexdigest()!=masked["feature_csv_sha256"]):
        raise ValueError("JT_MASKED_SOURCE_PIN")
    upstream=pd.read_csv(io.BytesIO(raw_mask))
    expected_mask_times=pd.date_range(START,periods=HOURS,freq="h",tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy()
    hour_masks={}
    for asset in ASSETS:
        rows=upstream.loc[upstream["asset"]==asset].reset_index(drop=True)
        if (len(rows)!=HOURS or not np.array_equal(rows["open_time"].to_numpy(),expected_mask_times)
            or not rows["source_valid"].isin([0,1]).all()):
            raise ValueError("JT_UPSTREAM_MASK_HOURLY_ALIGNMENT_"+asset)
        hour_masks[asset]=rows["source_valid"].to_numpy(dtype=int).astype(bool)
    canonical={}
    for asset in ASSETS:
        raw=(HERE/"phase243_clean4_canonical"/f"{asset}_1h.csv").read_bytes()
        pin,size=PINS[asset]
        if hashlib.sha256(raw).hexdigest()!=pin or len(raw)!=size:
            raise ValueError("JT_1H_PIN_"+asset)
        df=pd.read_csv(io.BytesIO(raw))
        if len(df)!=HOURS:raise ValueError("JT_1H_HOURS")
        canonical[asset]=df[["open","high","low","close","quote_volume"]].to_numpy(dtype=float)
    tasks=[(a,m) for a in ASSETS for m in MONTHS]
    data={};faults=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(source_month,*pair):pair for pair in tasks}
        for future in concurrent.futures.as_completed(futures):
            pair=futures[future]
            try:data[pair]=future.result()
            except Exception as exc:
                faults.append({"asset":pair[0],"month":pair[1],
                               "fault":type(exc).__name__+": "+str(exc)[:200]})
    if faults:
        raise ValueError("JT_NATIVE_SOURCE_TRANSPORT_OR_SCHEMA_"+str(faults[:4]))
    times_all=(pd.date_range(START,periods=HOURS,freq="h",tz="UTC").asi8//1000000).astype(np.int64)
    records=[];month_manifest={};quarantine=[];valid_months=0
    offset=0
    for month in MONTHS:
        y,m=map(int,month.split("-"))
        count=calendar.monthrange(y,m)[1]*24
        sl=slice(offset,offset+count)
        aligned={}
        for asset in ASSETS:
            item=data[(asset,month)]
            _,_,zipsha,member_sha,times,ohlc,ret=item
            entry=masked["manifest"][asset+"/"+month]
            if entry.get("zip_sha256")!=zipsha:
                raise ValueError("JT_VENDOR_ARCHIVE_CHANGED_"+asset+"_"+month)
            if not np.array_equal(times,times_all[sl]):
                raise ValueError("JT_CROSS_ASSET_UTC_ALIGNMENT_"+asset+"_"+month)
            month_manifest[asset+"/"+month]={"zip_sha256":zipsha,
                                             "csv_sha256":member_sha,
                                             "mask_verified":bool(entry["verified"])}
            if entry["verified"]:
                compare_1h(ohlc,canonical[asset][sl])
            aligned[asset]=ret
        good=all(masked["manifest"][a+"/"+month]["verified"] for a in ASSETS)
        hourly_valid=np.logical_and.reduce([hour_masks[a][sl] for a in ASSETS]) if good else np.zeros(count,dtype=bool)
        if good:valid_months+=1
        else:quarantine.append(month)
        btc=aligned["BTCUSDT"]
        for asset in ASSETS[1:]:
            alt=aligned[asset]
            bdown=np.minimum(btc,0.)
            adown=np.minimum(alt,0.)
            down_beta=np.sum(bdown*adown,axis=1)/(np.sum(bdown*bdown,axis=1)+1e-10)
            resilience=np.sum((alt-btc)*(btc<0.),axis=1)/np.maximum(np.sum(btc<0.,axis=1),1)
            cojump=np.mean((btc<-.001)&(alt<0.),axis=1)
            up_capture=np.sum(np.maximum(alt,0.)*(btc>0.),axis=1)/(
                np.sum(np.maximum(btc,0.),axis=1)+1e-10)
            for i,stamp in enumerate(times_all[sl]):
                usable=bool(hourly_valid[i])
                values=tuple(canonical_feature(v) for v in
                             (down_beta[i],resilience[i],cojump[i],up_capture[i])) if usable else (None,)*4
                records.append((int(stamp),asset,int(usable),*values))
        offset+=count
    if offset!=HOURS or len(records)!=HOURS*3:
        raise ValueError("JT_FULL_CALENDAR_COVERAGE")
    df=pd.DataFrame(records,columns=COLS)
    df["open_time"]=pd.to_datetime(df["open_time"],unit="ms",utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    raw=df.to_csv(index=False,float_format="%.17g",na_rep="").encode()
    OUT.write_bytes(raw)
    report={"source_only":True,"historical_system_pnl_computed":False,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "trading_authorized":False,"assets":list(ASSETS),
            "months":list(MONTHS),"vendor_archives_authenticated":len(data),
            "full_alt_asset_hours":HOURS*3,
            "valid_alt_asset_hours":int(df["source_valid"].sum()),
            "quarantined_months":quarantine,"valid_months":valid_months,
            "vendor_archive_manifest":month_manifest,
            "source_feature_sha256":hashlib.sha256(raw).hexdigest(),
            "upstream_mask_sha256":masked["feature_csv_sha256"],
            "decision":"PASS_JT_DOWNSIDE_SOURCE_ONLY_NOT_ECONOMIC"}
    RECEIPT.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("JT_CROSS_ASSET_SOURCE_ONLY",report["decision"],
          "archives",len(data),"valid_months",valid_months,
          "valid_alt_hours",report["valid_alt_asset_hours"],
          "quarantine",quarantine,flush=True)
    return report

if __name__=="__main__":run()
