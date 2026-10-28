#!/usr/bin/env python3
"""Independent full original 1m archive replay using pandas vector aggregation; no primary parser."""
from __future__ import annotations
import calendar,hashlib,io,json,math,re,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from phase1260_aj_authenticated_source_digest import load_official
ROOT=Path(__file__).resolve().parent
RAW=ROOT/"v98_intrabar_full_1m_raw"
PRIMARY=ROOT/"v98_intrabar_full_1m_primary_receipt.json"
OUT=ROOT/"v98_intrabar_full_1m_independent_receipt.json"
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
MONTHS=("2022-12",)+tuple(f"{y}-{m:02d}" for y in (2023,2024) for m in range(1,13))
START=int(datetime(2022,12,1,tzinfo=timezone.utc).timestamp()*1000)
def sha(x):return hashlib.sha256(x).hexdigest()
def verify(asset,month,anchors):
    y,m=map(int,month.split("-"));days=calendar.monthrange(y,m)[1]
    first=int(datetime(y,m,1,tzinfo=timezone.utc).timestamp()*1000)
    name=f"{asset}-1m-{month}.zip"
    raw=(RAW/name).read_bytes()
    side=(RAW/(name+".CHECKSUM")).read_text().strip().split()
    if len(side) not in (1,2) or not re.fullmatch("[0-9a-fA-F]{64}",side[0]):
        raise ValueError("INDEPENDENT_SIDECAR_SCHEMA")
    if len(side)==2 and side[1].lstrip("*").split("/")[-1]!=name:
        raise ValueError("INDEPENDENT_SIDECAR_NAME")
    if sha(raw)!=side[0].lower():raise ValueError("INDEPENDENT_PUBLISHER_SHA")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members=[n for n in z.namelist() if not n.endswith("/")]
        if len(members)!=1 or members[0].split("/")[-1]!=name[:-4]+".csv":
            raise ValueError("INDEPENDENT_ZIP_MEMBER")
        with z.open(members[0]) as f:
            d=pd.read_csv(f,header=None,low_memory=False)
    if len(d) and str(d.iloc[0,0]).strip().lower() in ("open_time","opentime"):
        d=d.iloc[1:].reset_index(drop=True)
    expected=days*1440
    if len(d)!=expected or d.shape[1]<11:raise ValueError("INDEPENDENT_MONTH_ROWS_OR_COLUMNS")
    t=pd.to_numeric(d.iloc[:,0],errors="raise").to_numpy(dtype=np.int64)
    if not np.array_equal(t,first+np.arange(expected,dtype=np.int64)*60000):
        raise ValueError("INDEPENDENT_MINUTE_UTC_ORDER")
    end=pd.to_numeric(d.iloc[:,6],errors="raise").to_numpy(dtype=np.int64)
    if np.any(end<t) or np.any(end>t+59999):raise ValueError("INDEPENDENT_CLOSE_TIME")
    arr=d.iloc[:,[1,2,3,4,5,7]].apply(pd.to_numeric,errors="raise").to_numpy(dtype=float)
    if not np.isfinite(arr).all():raise ValueError("INDEPENDENT_NONFINITE")
    o,h,l,c,v,q=(arr[:,j] for j in range(6))
    if np.any(np.minimum.reduce((o,h,l,c))<=0) or np.any(h<np.maximum(o,c)) or np.any(l>np.minimum(o,c)) or np.any(v<0) or np.any(q<0):
        raise ValueError("INDEPENDENT_GEOMETRY")
    margin=1e-6*np.maximum(1.,q)
    if np.any(q<v*l-margin) or np.any(q>v*h+margin):
        raise ValueError("INDEPENDENT_QUOTE_BASE_UNITS")
    chunks=arr.reshape((-1,60,6))
    aggregate=np.column_stack((chunks[:,0,0],chunks[:,:,1].max(axis=1),
        chunks[:,:,2].min(axis=1),chunks[:,-1,3],
        chunks[:,:,4].sum(axis=1),chunks[:,:,5].sum(axis=1)))
    start=(first-START)//3600000
    original=anchors[start:start+days*24]
    if len(original)!=len(aggregate):raise ValueError("INDEPENDENT_HOURLY_COVERAGE")
    tol=np.maximum(np.array([1e-8]*4+[1e-6]*2),
                   np.array([1e-10]*4+[1e-8]*2)*np.maximum(abs(original),abs(aggregate)))
    mismatch=np.argwhere(np.abs(aggregate-original)>tol)
    if len(mismatch):
        i,j=map(int,mismatch[0])
        raise ValueError(f"INDEPENDENT_HOURLY_MISMATCH:{i}:{j}:{aggregate[i,j]}:{original[i,j]}")
    return {"asset":asset,"month":month,"sha256":sha(raw),"minutes":expected,"hours":days*24}
def main():
    _,source_manifest=load_official()
    receipt=json.loads(PRIMARY.read_text())
    pins={}
    for asset in ASSETS:
        d=pd.read_csv(ROOT/"phase243_clean4_canonical"/(asset+"_1h.csv"))
        if len(d)!=18288:raise ValueError("INDEPENDENT_ANCHOR_ROWS")
        pins[asset]=d[["open","high","low","close","volume","quote_volume"]].to_numpy(dtype=float)
    good=[];errors=[]
    for asset in ASSETS:
        for month in MONTHS:
            try:
                r=verify(asset,month,pins[asset])
                previous=next((x for x in receipt["records"] if x["asset"]==asset and x["month"]==month),None)
                if not previous or previous.get("status")!="PASS" or previous.get("sha256")!=r["sha256"]:
                    raise ValueError("INDEPENDENT_PRIMARY_RECEIPT_DISAGREEMENT")
                good.append(r)
            except Exception as e:
                errors.append({"asset":asset,"month":month,"error":str(e)[:250]})
            print("V98_FULL_1M_INDEPENDENT",asset,month,"PASS" if (asset,month) in {(x["asset"],x["month"]) for x in good} else "FAIL",flush=True)
    n=sum(x["minutes"] for x in good);h=sum(x["hours"] for x in good)
    pin=sha(json.dumps(source_manifest,sort_keys=True,separators=(",",":")).encode())
    if receipt.get("canonical_manifest_sha256")!=pin or len(receipt.get("records",[]))!=100:
        errors.append({"error":"INDEPENDENT_CANONICAL_OR_INVENTORY"})
    if receipt.get("verified_minutes")!=n or receipt.get("verified_hourly_aggregates")!=h:
        errors.append({"error":"INDEPENDENT_COUNTS_DISAGREE"})
    passed=len(good)==100 and n==4389120 and h==73152 and not errors
    report={"source_only":True,"pnl_computed":False,"validation_2025_read":False,
        "trading_authorized":False,"expected_archives":100,"passed_archives":len(good),
        "verified_minutes":n,"verified_hourly_aggregates":h,
        "canonical_manifest_sha256":pin,"errors":errors[:50],
        "decision":"PASS_FULL_1M_INDEPENDENT_SOURCE_ONLY_NOT_PNL" if passed else "REJECT_FULL_1M_SOURCE_NO_PNL"}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("V98_FULL_1M_INDEPENDENT_RESULT",report["decision"],len(good),"/100",n,"/4389120",h,"/73152",flush=True)
    raise SystemExit(0 if passed else 2)
if __name__=="__main__":main()
