#!/usr/bin/env python3
"""JS cross-asset BTC-to-alt 5m propagation SOURCE ONLY, no PnL/sign selection."""
from __future__ import annotations
import calendar,concurrent.futures,hashlib,io,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from phase803_training_ohlc_official_replay import ASSETS,MONTHS,BASE,PINS,download
from phase1260_aj_authenticated_source_digest import HOURS,START
from jq_native_5m_path_source import verify_archive,parse_month,compare_1h

HERE=Path(__file__).resolve().parent
OUT=HERE/"js_cross_asset_5m_propagation_hourly.csv"
RECEIPT=HERE/"js_cross_asset_5m_propagation_source_receipt.json"
COLS=("open_time","asset","source_valid","btc_to_alt_lag_cov",
      "alt_to_btc_lag_cov","btc_early_sell_pressure",
      "alt_late_response","btc_late_response")

def source_month(asset,month):
    if asset not in ASSETS or month not in MONTHS:
        raise ValueError("JS_TRAINING_SCOPE")
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
        raise ValueError("JS_NATIVE_5M_CLOSE_GEOMETRY")
    op=op.reshape(n,12);cl=cl.reshape(n,12)
    prev=np.column_stack((op[:,0],cl[:,:-1]))
    ret=np.log(cl/prev)
    if not np.isfinite(ret).all():raise ValueError("JS_NATIVE_5M_RETURNS_NONFINITE")
    return (asset,month,zipsha,member_sha,times,ohlc,ret)

def run():
    if HOURS!=18288 or len(ASSETS)!=4 or len(MONTHS)!=25 or MONTHS[-1]!="2024-12":
        raise ValueError("JS_TRAINING_CALENDAR")
    masked=json.loads((HERE/"native_5m_masked_source_receipt.json").read_text())
    raw_mask=(HERE/"native_5m_masked_verified_hourly_features.csv").read_bytes()
    if (masked["decision"]!="MASKED_5M_SOURCE_ONLY_NO_ECONOMIC_AUTHORIZATION"
        or hashlib.sha256(raw_mask).hexdigest()!=masked["feature_csv_sha256"]):
        raise ValueError("JS_MASKED_SOURCE_PIN")
    canonical={}
    for asset in ASSETS:
        raw=(HERE/"phase243_clean4_canonical"/f"{asset}_1h.csv").read_bytes()
        pin,size=PINS[asset]
        if hashlib.sha256(raw).hexdigest()!=pin or len(raw)!=size:
            raise ValueError("JS_1H_PIN_"+asset)
        df=pd.read_csv(io.BytesIO(raw))
        if len(df)!=HOURS:raise ValueError("JS_1H_HOURS")
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
        raise ValueError("JS_NATIVE_SOURCE_TRANSPORT_OR_SCHEMA_"+str(faults[:4]))
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
                raise ValueError("JS_VENDOR_ARCHIVE_CHANGED_"+asset+"_"+month)
            if not np.array_equal(times,times_all[sl]):
                raise ValueError("JS_CROSS_ASSET_UTC_ALIGNMENT_"+asset+"_"+month)
            month_manifest[asset+"/"+month]={"zip_sha256":zipsha,
                                             "csv_sha256":member_sha,
                                             "mask_verified":bool(entry["verified"])}
            if entry["verified"]:
                compare_1h(ohlc,canonical[asset][sl])
            aligned[asset]=ret
        good=all(masked["manifest"][a+"/"+month]["verified"] for a in ASSETS)
        if good:valid_months+=1
        else:quarantine.append(month)
        btc=aligned["BTCUSDT"]
        for asset in ASSETS[1:]:
            alt=aligned[asset]
            btc_alt=np.mean(btc[:,:-1]*alt[:,1:],axis=1)
            alt_btc=np.mean(alt[:,:-1]*btc[:,1:],axis=1)
            early=np.minimum(btc[:,:6],0.).sum(axis=1)
            late_alt=alt[:,6:].sum(axis=1)
            late_btc=btc[:,6:].sum(axis=1)
            for i,stamp in enumerate(times_all[sl]):
                values=(float(btc_alt[i]),float(alt_btc[i]),float(early[i]),
                        float(late_alt[i]),float(late_btc[i])) if good else (None,)*5
                records.append((int(stamp),asset,int(good),*values))
        offset+=count
    if offset!=HOURS or len(records)!=HOURS*3:
        raise ValueError("JS_FULL_CALENDAR_COVERAGE")
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
            "decision":"PASS_JS_CROSS_ASSET_SOURCE_ONLY_NOT_ECONOMIC"}
    RECEIPT.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("JS_CROSS_ASSET_SOURCE_ONLY",report["decision"],
          "archives",len(data),"valid_months",valid_months,
          "valid_alt_hours",report["valid_alt_asset_hours"],
          "quarantine",quarantine,flush=True)
    return report

if __name__=="__main__":run()
