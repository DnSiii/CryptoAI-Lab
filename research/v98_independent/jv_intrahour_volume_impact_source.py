#!/usr/bin/env python3
"""JV intrahour volume-concentration and signed price-impact SOURCE ONLY, no PnL."""
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
OUT=HERE/"jv_volume_impact_hourly.csv"
RECEIPT=HERE/"jv_volume_impact_source_receipt.json"
COLS=("open_time","asset","source_valid","volume_hhi","signed_volume_impulse",
      "late_volume_share","directional_efficiency")

def canonical_feature(value):
    x=float(value)
    if not math.isfinite(x):raise ValueError("JV_NONFINITE_DERIVED_SOURCE")
    return float(format(x,".10g"))

def source_month(asset,month):
    if asset not in ASSETS or month not in MONTHS:
        raise ValueError("JV_TRAINING_SCOPE")
    name=f"{asset}-5m-{month}.zip"
    url=f"{BASE}/{asset}/5m/{name}"
    data,zipsha,member_sha=verify_archive(download(url),download(url+".CHECKSUM"),name)
    times,ohlc,_=parse_month(data,asset,month)
    df=pd.read_csv(io.BytesIO(data),header=None,dtype=str,keep_default_na=False)
    if str(df.iloc[0,0]).strip().lower()=="open_time":
        df=df.iloc[1:].reset_index(drop=True)
    op=pd.to_numeric(df.iloc[:,1],errors="raise").to_numpy(dtype=float)
    cl=pd.to_numeric(df.iloc[:,4],errors="raise").to_numpy(dtype=float)
    q=pd.to_numeric(df.iloc[:,7],errors="raise").to_numpy(dtype=float)
    n=len(times)
    if (len(op)!=n*12 or np.any(op<=0) or np.any(cl<=0) or
        np.any(q<0) or not np.isfinite(q).all()):
        raise ValueError("JV_NATIVE_5M_PRICE_VOLUME_GEOMETRY")
    op=op.reshape(n,12);cl=cl.reshape(n,12);q=q.reshape(n,12)
    prev=np.column_stack((op[:,0],cl[:,:-1]))
    ret=np.log(cl/prev)
    bar_ret=np.log(cl/op)
    if not np.isfinite(ret).all() or not np.isfinite(bar_ret).all():
        raise ValueError("JV_NATIVE_5M_RETURNS_NONFINITE")
    return (asset,month,zipsha,member_sha,times,ohlc,ret,bar_ret,q)

def run():
    if HOURS!=18288 or len(ASSETS)!=4 or len(MONTHS)!=25 or MONTHS[-1]!="2024-12":
        raise ValueError("JV_TRAINING_CALENDAR")
    masked=json.loads((HERE/"native_5m_masked_source_receipt.json").read_text())
    raw_mask=(HERE/"native_5m_masked_verified_hourly_features.csv").read_bytes()
    if (masked["decision"]!="MASKED_5M_SOURCE_ONLY_NO_ECONOMIC_AUTHORIZATION"
        or hashlib.sha256(raw_mask).hexdigest()!=masked["feature_csv_sha256"]):
        raise ValueError("JV_MASKED_SOURCE_PIN")
    upstream=pd.read_csv(io.BytesIO(raw_mask))
    expected_mask_times=pd.date_range(START,periods=HOURS,freq="h",tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy()
    hour_masks={}
    for asset in ASSETS:
        rows=upstream.loc[upstream["asset"]==asset].reset_index(drop=True)
        if (len(rows)!=HOURS or not np.array_equal(rows["open_time"].to_numpy(),expected_mask_times)
            or not rows["source_valid"].isin([0,1]).all()):
            raise ValueError("JV_UPSTREAM_MASK_HOURLY_ALIGNMENT_"+asset)
        hour_masks[asset]=rows["source_valid"].to_numpy(dtype=int).astype(bool)
    canonical={}
    for asset in ASSETS:
        raw=(HERE/"phase243_clean4_canonical"/f"{asset}_1h.csv").read_bytes()
        pin,size=PINS[asset]
        if hashlib.sha256(raw).hexdigest()!=pin or len(raw)!=size:
            raise ValueError("JV_1H_PIN_"+asset)
        df=pd.read_csv(io.BytesIO(raw))
        if len(df)!=HOURS:raise ValueError("JV_1H_HOURS")
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
        raise ValueError("JV_NATIVE_SOURCE_TRANSPORT_OR_SCHEMA_"+str(faults[:4]))
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
            _,_,zipsha,member_sha,times,ohlc,ret,bar_ret,q5=item
            entry=masked["manifest"][asset+"/"+month]
            if entry.get("zip_sha256")!=zipsha:
                raise ValueError("JV_VENDOR_ARCHIVE_CHANGED_"+asset+"_"+month)
            if not np.array_equal(times,times_all[sl]):
                raise ValueError("JV_CROSS_ASSET_UTC_ALIGNMENT_"+asset+"_"+month)
            month_manifest[asset+"/"+month]={"zip_sha256":zipsha,
                                             "csv_sha256":member_sha,
                                             "mask_verified":bool(entry["verified"])}
            if entry["verified"]:
                compare_1h(ohlc,canonical[asset][sl])
            aligned[asset]=(ret,bar_ret,q5,ohlc)
        good=all(masked["manifest"][a+"/"+month]["verified"] for a in ASSETS)
        hourly_valid=np.logical_and.reduce([hour_masks[a][sl] for a in ASSETS]) if good else np.zeros(count,dtype=bool)
        if good:valid_months+=1
        else:quarantine.append(month)
        for asset in ASSETS:
            ret,bar_ret,q5,ohlc=aligned[asset]
            total=q5.sum(axis=1)
            bad=(total<=0)|(~np.isfinite(total))
            if np.any(bad & hourly_valid):
                raise ValueError("JV_NONPOSITIVE_VERIFIED_HOURLY_NATIVE_QUOTE_"+asset)
            # Quarantined month-hours remain invalid; zero native volume in
            # those excluded hours must never leak into source features/PnL.
            safe_total=np.where(bad,1.,total)
            share=q5/safe_total[:,None]
            volume_hhi=np.square(share).sum(axis=1)
            impulse=np.sum(share*bar_ret,axis=1)
            late_share=np.sum(share[:,8:],axis=1)
            efficiency=np.log(ohlc[:,3]/ohlc[:,0])/np.maximum(
                np.sqrt(np.square(ret).sum(axis=1)),.001)
            for i,stamp in enumerate(times_all[sl]):
                usable=bool(hourly_valid[i])
                values=tuple(canonical_feature(v) for v in
                             (volume_hhi[i],impulse[i],late_share[i],efficiency[i])) if usable else (None,)*4
                records.append((int(stamp),asset,int(usable),*values))
        offset+=count
    if offset!=HOURS or len(records)!=HOURS*4:
        raise ValueError("JV_FULL_CALENDAR_COVERAGE")
    df=pd.DataFrame(records,columns=COLS)
    df["open_time"]=pd.to_datetime(df["open_time"],unit="ms",utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    raw=df.to_csv(index=False,float_format="%.17g",na_rep="").encode()
    OUT.write_bytes(raw)
    report={"source_only":True,"historical_system_pnl_computed":False,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "trading_authorized":False,"assets":list(ASSETS),
            "months":list(MONTHS),"vendor_archives_authenticated":len(data),
            "full_asset_hours":HOURS*4,
            "valid_asset_hours":int(df["source_valid"].sum()),
            "quarantined_months":quarantine,"valid_months":valid_months,
            "vendor_archive_manifest":month_manifest,
            "source_feature_sha256":hashlib.sha256(raw).hexdigest(),
            "upstream_mask_sha256":masked["feature_csv_sha256"],
            "decision":"PASS_JV_VOLUME_IMPACT_SOURCE_ONLY_NOT_ECONOMIC"}
    RECEIPT.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("JV_INTRAHOUR_VOLUME_SOURCE_ONLY",report["decision"],
          "archives",len(data),"valid_months",valid_months,
          "valid_alt_hours",report["valid_asset_hours"],
          "quarantine",quarantine,flush=True)
    return report

if __name__=="__main__":run()
