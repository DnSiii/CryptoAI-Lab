#!/usr/bin/env python3
"""Independent 16 original daily-vs-monthly 1m provenance replay; no primary parser imports."""
from __future__ import annotations
import hashlib,io,json,re,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from phase1260_aj_authenticated_source_digest import load_official
ROOT=Path(__file__).resolve().parent
MONTHLY=ROOT/"v98_intrabar_full_1m_raw"
DAILY=ROOT/"v98_intrabar_conflict_daily_raw"
PRIMARY=ROOT/"v98_intrabar_conflict_forensic_receipt.json"
OUT=ROOT/"v98_intrabar_conflict_independent_receipt.json"
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
DATES=("2023-08-16","2023-11-10","2023-11-14","2024-10-28")
def sha(b):return hashlib.sha256(b).hexdigest()
def load_zip(root,name):
    raw=(root/name).read_bytes()
    side=(root/(name+".CHECKSUM")).read_text().strip().split()
    if len(side) not in (1,2) or not re.fullmatch("[0-9a-fA-F]{64}",side[0]):
        raise ValueError("SIDECAR_SCHEMA")
    if sha(raw)!=side[0].lower():raise ValueError("PUBLISHER_SHA")
    if len(side)==2 and side[1].lstrip("*").split("/")[-1]!=name:
        raise ValueError("SIDECAR_NAME")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files=[x for x in z.namelist() if not x.endswith("/")]
        if len(files)!=1 or files[0].split("/")[-1]!=name[:-4]+".csv":
            raise ValueError("ZIP_MEMBER")
        with z.open(files[0]) as f:
            df=pd.read_csv(f,header=None,low_memory=False)
    if len(df) and str(df.iloc[0,0]).strip().lower() in ("open_time","opentime"):
        df=df.iloc[1:].reset_index(drop=True)
    t=pd.to_numeric(df.iloc[:,0],errors="raise").to_numpy(dtype=np.int64)
    a=df.iloc[:,[1,2,3,4,5,7]].apply(pd.to_numeric,errors="raise").to_numpy(dtype=float)
    return t,a,sha(raw)
def compare_1h(a,anchor):
    z=a.reshape((24,60,6))
    v=np.column_stack((z[:,0,0],z[:,:,1].max(axis=1),z[:,:,2].min(axis=1),
        z[:,-1,3],z[:,:,4].sum(axis=1),z[:,:,5].sum(axis=1)))
    tol=np.maximum(np.array([1e-8]*4+[1e-6]*2),
                   np.array([1e-10]*4+[1e-8]*2)*np.maximum(abs(v),abs(anchor)))
    return int(np.sum(np.abs(v-anchor)>tol))
def main():
    _,manifest=load_official()
    original=json.loads(PRIMARY.read_text())
    anchors={}
    for asset in ASSETS:
        d=pd.read_csv(ROOT/"phase243_clean4_canonical"/(asset+"_1h.csv"))
        anchors[asset]=d.set_index(pd.to_datetime(d["open_time"],utc=True))
    errors=[];daily_mismatches=monthly_mismatches=minute_differences=0;verified=0
    for asset in ASSETS:
        for day in DATES:
            try:
                t=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000)
                dname=f"{asset}-1m-{day}.zip";mname=f"{asset}-1m-{day[:7]}.zip"
                dt,da,dsha=load_zip(DAILY,dname)
                mt,ma,msha=load_zip(MONTHLY,mname)
                keep=(mt>=t)&(mt<t+86400000)
                mt=mt[keep];ma=ma[keep]
                expected=t+np.arange(1440,dtype=np.int64)*60000
                if not (np.array_equal(dt,expected) and np.array_equal(mt,expected)):
                    raise ValueError("INDEPENDENT_1M_CALENDAR")
                price_tol=np.maximum(np.array([1e-8]*4+[1e-6]*2),
                    np.array([1e-10]*4+[1e-8]*2)*np.maximum(abs(da),abs(ma)))
                nd=int(np.sum(np.any(abs(da-ma)>price_tol,axis=1)))
                idx=pd.date_range(pd.Timestamp(t,unit="ms",tz="UTC"),periods=24,freq="h")
                a=anchors[asset].loc[idx][["open","high","low","close","volume","quote_volume"]].to_numpy(dtype=float)
                dh=compare_1h(da,a);mh=compare_1h(ma,a)
                p=next((x for x in original["rows"] if x["asset"]==asset and x["date"]==day),None)
                if not p or p["status"]!="PASS_AUTHENTICATED" or p["daily_sha256"]!=dsha or p["monthly_sha256"]!=msha:
                    raise ValueError("INDEPENDENT_RAW_SHA_RECEIPT")
                if (p["daily_hourly_mismatch_count"]!=dh or
                    p["monthly_hourly_mismatch_count"]!=mh or
                    p["minute_diff_count"]!=nd):
                    raise ValueError(f"INDEPENDENT_MISMATCH_COUNTS:{dh}:{mh}:{nd}")
                verified+=1;daily_mismatches+=dh;monthly_mismatches+=mh;minute_differences+=nd
            except Exception as e:
                errors.append({"asset":asset,"date":day,"error":str(e)[:200]})
            print("V98_1M_CONFLICT_INDEPENDENT",asset,day,"PASS" if not any(x.get("asset")==asset and x.get("date")==day for x in errors) else "FAIL",flush=True)
    decision=original.get("decision")
    if (verified!=16 or errors or original.get("daily_hourly_mismatches")!=daily_mismatches or
        original.get("monthly_hourly_mismatches")!=monthly_mismatches or
        original.get("minute_differences")!=minute_differences):
        decision="BLOCK_INDEPENDENT_SOURCE_REPLAY"
    result={"decision":decision,"independent_replay_pass":not errors and verified==16,
        "verified_asset_days":verified,"daily_hourly_mismatches":daily_mismatches,
        "monthly_hourly_mismatches":monthly_mismatches,"minute_differences":minute_differences,
        "errors":errors,"source_only":True,"pnl_computed":False,
        "validation_2025_read":False,"trading_authorized":False}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("V98_1M_CONFLICT_INDEPENDENT_RESULT",decision,verified,
          "daily",daily_mismatches,"monthly",monthly_mismatches,"minute",minute_differences,flush=True)
    raise SystemExit(2 if decision=="BLOCK_INDEPENDENT_SOURCE_REPLAY" else 0)
if __name__=="__main__":main()
