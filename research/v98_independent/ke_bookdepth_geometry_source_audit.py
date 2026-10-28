#!/usr/bin/env python3
"""KE native bookDepth 2023-24 source-only physical geometry vs immutable Clean-4 OHLC."""
from __future__ import annotations
import concurrent.futures,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from ke_bookdepth_source_feasibility import ASSETS,DATES,BASE,get
from phase803_training_ohlc_official_replay import PINS
ROOT=Path(__file__).resolve().parent
START=pd.Timestamp("2022-12-01T00:00:00Z")
HOURS=18288

def pinned_ohlc():
    result={}
    for a in ASSETS:
        path=ROOT/"phase243_clean4_canonical"/(a+"_1h.csv")
        raw=path.read_bytes();pin,size=PINS[a]
        if hashlib.sha256(raw).hexdigest()!=pin or len(raw)!=size:
            raise ValueError("KE_CLEAN4_PIN_"+a)
        df=pd.read_csv(io.BytesIO(raw))
        if len(df)!=HOURS or not pd.to_datetime(df.open_time,utc=True).equals(
            pd.Series(pd.date_range(START,periods=HOURS,freq="h",tz="UTC"))):
            raise ValueError("KE_CLEAN4_CALENDAR_"+a)
        result[a]=(df.high.to_numpy(float),df.low.to_numpy(float))
    return result

def audit_one(asset,day,ohlc):
    name=f"{asset}-bookDepth-{day}.zip";url=f"{BASE}/{asset}/{name}"
    raw=get(url,25000000)
    check=get(url+".CHECKSUM",4096).decode("utf-8-sig").strip().split()
    if len(check)!=2 or check[1].lstrip("*./")!=name or hashlib.sha256(raw).hexdigest()!=check[0].lower():
        raise ValueError("KE_PUBLISHER_SHA_"+asset+day)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=[name[:-4]+".csv"]:raise ValueError("KE_MEMBER")
        df=pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
    if list(df.columns)!=["timestamp","percentage","depth","notional"]:
        raise ValueError("KE_SCHEMA")
    df["timestamp"]=pd.to_datetime(df.timestamp,utc=True,errors="raise")
    if not (df.timestamp.dt.strftime("%Y-%m-%d")==day).all():
        raise ValueError("KE_CROSS_DAY")
    for col in ("percentage","depth","notional"):
        df[col]=pd.to_numeric(df[col],errors="raise")
    if not np.isfinite(df[["percentage","depth","notional"]].to_numpy(float)).all():
        raise ValueError("KE_NONFINITE")
    df=df[df.percentage.isin([-1.,1.])]
    p=df.pivot_table(index="timestamp",columns="percentage",values=["depth","notional"],aggfunc="first")
    if not all((field,side) in p.columns for field in ("depth","notional") for side in (-1.,1.)):
        raise ValueError("KE_MISSING_INNER_BANDS")
    bid=(p[("notional",-1.)]/p[("depth",-1.)]).to_numpy(float)
    ask=(p[("notional",1.)]/p[("depth",1.)]).to_numpy(float)
    idx=((p.index-START).total_seconds()/3600).astype(int)
    if np.any(idx<0) or np.any(idx>=HOURS):
        raise ValueError("KE_FORBIDDEN_TIMESTAMP")
    high,low=ohlc[asset]
    mid=(bid+ask)/2.
    good=(np.isfinite(bid)&np.isfinite(ask)&(bid>0)&(ask>0)&(bid<=ask)&
          (mid>=low[idx]*.98)&(mid<=high[idx]*1.02))
    hours=set(p.index[good].hour.tolist())
    bad=np.flatnonzero(~good)[:3]
    return {"asset":asset,"day":day,"publisher_verified":True,
            "source_rows":int(len(df)*5),"snapshots":int(len(p)),
            "good_snapshots":int(np.sum(good)),"bad_snapshots":int(np.sum(~good)),
            "valid_utc_hours":len(hours),"full_day":len(hours)==24,
            "examples_bad":[{"ts":str(p.index[j]),"bid":float(bid[j]),
                             "ask":float(ask[j]),"center":float(mid[j]),
                             "low":float(low[idx[j]]),"high":float(high[idx[j]])}
                            for j in bad]}

def run():
    ohlc=pinned_ohlc()
    tasks=[(a,d) for a in ASSETS for d in DATES]
    def work(x):
        a,d=x
        try:return audit_one(a,d,ohlc)
        except Exception as exc:return {"asset":a,"day":d,"publisher_verified":False,
                                        "error":type(exc).__name__+": "+str(exc)[:200],
                                        "snapshots":0,"good_snapshots":0,
                                        "bad_snapshots":0,"valid_utc_hours":0,"full_day":False}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(work,tasks))
    total=sum(r["snapshots"] for r in rows)
    good=sum(r["good_snapshots"] for r in rows)
    full=sum(r["full_day"] for r in rows)
    quality=good/total if total else 0.
    passed=all(r["publisher_verified"] for r in rows) and quality>=.95 and full>=19
    result={"architecture":"KE","source_only":True,"historical_system_pnl_computed":False,
            "validation_2025_read":False,"holdout_accessed":False,
            "external_benchmarks_used":False,"trading_authorized":False,
            "publisher_verified_samples":sum(r["publisher_verified"] for r in rows),
            "total_snapshots":total,"physically_consistent_snapshots":good,
            "physically_consistent_fraction":quality,"full_utc_days":full,
            "results":rows,"decision":"PASS_KE_SAMPLE_GEOMETRY_NOT_FULL_HISTORY" if passed else
                             "BLOCK_KE_SAMPLE_GEOMETRY_OR_COVERAGE"}
    (ROOT/"ke_bookdepth_geometry_source_audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("KE_GEOMETRY",result["decision"],"publisher",result["publisher_verified_samples"],
          "good",good,"total",total,"fraction",quality,"full_days",full,flush=True)
    for r in rows:
        print("KE_GEOMETRY_DAY",r["asset"],r["day"],r["good_snapshots"],
              r["snapshots"],r["valid_utc_hours"],r.get("error",""),flush=True)
    return result

if __name__=="__main__":run()
