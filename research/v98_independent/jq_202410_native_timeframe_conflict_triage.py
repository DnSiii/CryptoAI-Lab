#!/usr/bin/env python3
"""JQ independent October-2024 vendor-SHA 1m/5m/1h source conflict triage.
SOURCE-ONLY: no signals, PnL, training selection, holdout or source replacement.
"""
from __future__ import annotations
import calendar,hashlib,io,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from phase803_training_ohlc_official_replay import ASSETS,BASE,PINS,download
from jq_native_5m_path_source import verify_archive

HERE=Path(__file__).resolve().parent
MONTH="2024-10"
OUT=HERE/"jq_202410_native_timeframe_conflict_triage.json"
FIELDS=("open","high","low","close","quote_volume")
TOL_ABS=np.array([1e-8]*4+[1e-6])
TOL_REL=np.array([2e-10]*4+[2e-8])

def one(asset,period):
    if asset not in ASSETS or period not in ("1m","5m"):
        raise ValueError("JQ_TRIAGE_SCOPE")
    filename=f"{asset}-{period}-{MONTH}.zip"
    url=f"{BASE}/{asset}/{period}/{filename}"
    raw=download(url);sidecar=download(url+".CHECKSUM")
    member,zipsha,member_sha=verify_archive(raw,sidecar,filename)
    df=pd.read_csv(io.BytesIO(member),header=None,dtype=str,keep_default_na=False)
    if df.shape[1]!=12:raise ValueError("JQ_TRIAGE_SCHEMA")
    if str(df.iloc[0,0]).strip().lower()=="open_time":
        df=df.iloc[1:].reset_index(drop=True)
    mins=1 if period=="1m" else 5
    first=int(datetime(2024,10,1,tzinfo=timezone.utc).timestamp()*1000)
    expected=first+np.arange(31*24*60//mins,dtype=np.int64)*mins*60000
    opened=pd.to_numeric(df.iloc[:,0],errors="raise").to_numpy(dtype=np.int64)
    closed=pd.to_numeric(df.iloc[:,6],errors="raise").to_numpy(dtype=np.int64)
    if (len(opened)!=len(expected) or not np.array_equal(opened,expected)
        or not np.array_equal(closed,opened+mins*60000-1)):
        raise ValueError("JQ_TRIAGE_UTC_CONTINUITY_"+period)
    x=np.column_stack([pd.to_numeric(df.iloc[:,j],errors="raise").to_numpy(dtype=float)
                       for j in (1,2,3,4,7)])
    if not np.isfinite(x).all():raise ValueError("JQ_TRIAGE_NONFINITE")
    op,hi,lo,cl,q=(x[:,j] for j in range(5))
    if (np.any(op<=0) or np.any(cl<=0) or np.any(lo<=0)
        or np.any(lo>np.minimum(op,cl)) or np.any(hi<np.maximum(op,cl))
        or np.any(q<0)):
        raise ValueError("JQ_TRIAGE_GEOMETRY")
    blocks=x.reshape(744,60//mins,5)
    hourly=np.column_stack((blocks[:,0,0],blocks[:,:,1].max(axis=1),
                            blocks[:,:,2].min(axis=1),blocks[:,-1,3],
                            blocks[:,:,4].sum(axis=1)))
    return hourly,{"zip_sha256":zipsha,"member_sha256":member_sha,
                   "bars":len(opened),"hourly_rows":len(hourly)}

def canonical(asset):
    raw=(HERE/"phase243_clean4_canonical"/(asset+"_1h.csv")).read_bytes()
    pin,size=PINS[asset]
    if hashlib.sha256(raw).hexdigest()!=pin or len(raw)!=size:
        raise ValueError("JQ_TRIAGE_PINNED_CANONICAL_SHA")
    df=pd.read_csv(io.BytesIO(raw))
    dt=pd.to_datetime(df["open_time"],utc=True)
    mask=(dt>=pd.Timestamp("2024-10-01",tz="UTC"))&(dt<pd.Timestamp("2024-11-01",tz="UTC"))
    cut=df.loc[mask,list(FIELDS)].to_numpy(dtype=float)
    if cut.shape!=(744,5):raise ValueError("JQ_TRIAGE_CANONICAL_OCT_HOURS")
    return cut,pin

def mask_diff(a,b):
    return np.abs(a-b)>(TOL_ABS+TOL_REL*np.abs(b))

def run():
    result={"source_only":True,"historical_system_pnl_computed":False,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "trading_authorized":False,"month":MONTH,"assets":{}}
    for asset in ASSETS:
        x1,sha1=one(asset,"1m");x5,sha5=one(asset,"5m")
        xh,canonical_sha=canonical(asset)
        m1=mask_diff(x1,xh);m5=mask_diff(x5,xh);m15=mask_diff(x1,x5)
        bad=np.argwhere(m1|m5|m15)
        details=[]
        for i,j in bad[:60]:
            details.append({"utc_hour":(pd.Timestamp("2024-10-01",tz="UTC")+
                                         pd.Timedelta(hours=int(i))).isoformat(),
                            "field":FIELDS[int(j)],"native_1m":float(x1[i,j]),
                            "native_5m":float(x5[i,j]),"pinned_1h":float(xh[i,j]),
                            "delta_1m_5m":float(x1[i,j]-x5[i,j]),
                            "delta_1m_1h":float(x1[i,j]-xh[i,j]),
                            "delta_5m_1h":float(x5[i,j]-xh[i,j])})
        item={"native_1m":sha1,"native_5m":sha5,"canonical_1h_sha256":canonical_sha,
              "bad_cells_1m_vs_1h":int(m1.sum()),
              "bad_cells_5m_vs_1h":int(m5.sum()),
              "bad_cells_1m_vs_5m":int(m15.sum()),
              "bad_hours_union":int(len(np.unique(bad[:,0])) if len(bad) else 0),
              "conflict_examples":details}
        result["assets"][asset]=item
        print("JQ_TRIAGE_ASSET",asset,"1m_vs_1h",item["bad_cells_1m_vs_1h"],
              "5m_vs_1h",item["bad_cells_5m_vs_1h"],
              "1m_vs_5m",item["bad_cells_1m_vs_5m"],
              "examples",json.dumps(details[:8],sort_keys=True),flush=True)
    result["decision"]="SOURCE_CONFLICT_TRIAGED_NO_AUTHORITY_OVERRIDE_NO_PNL"
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("JQ_OCT_2024_TRIAGE_COMPLETE_NO_PNL",flush=True)
    return result

if __name__=="__main__":run()
