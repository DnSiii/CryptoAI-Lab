#!/usr/bin/env python3
"""V98 Independent masked native-5m source-only provenance, no strategy PnL.
Quarantine any full asset-month whose vendor 5m fails original pinned 1h match.
"""
from __future__ import annotations
import calendar,concurrent.futures,hashlib,io,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from phase803_training_ohlc_official_replay import ASSETS,MONTHS,PINS
from phase1260_aj_authenticated_source_digest import HOURS,START
from jq_native_5m_path_source import fetch_month,compare_1h,FIELDS

HERE=Path(__file__).resolve().parent
OUT=HERE/"native_5m_masked_verified_hourly_features.csv"
RECEIPT=HERE/"native_5m_masked_source_receipt.json"
COLS=("open_time","asset","source_valid",*FIELDS[2:])

def run():
    if HOURS!=18288 or len(ASSETS)!=4 or len(MONTHS)!=25 or MONTHS[-1]!="2024-12":
        raise ValueError("MASKED_5M_TRAINING_FIREWALL")
    canonical={}
    for asset in ASSETS:
        raw=(HERE/"phase243_clean4_canonical"/f"{asset}_1h.csv").read_bytes()
        pin,size=PINS[asset]
        if hashlib.sha256(raw).hexdigest()!=pin or len(raw)!=size:
            raise ValueError("MASKED_5M_CANONICAL_PIN_"+asset)
        df=pd.read_csv(io.BytesIO(raw))
        if len(df)!=HOURS:raise ValueError("MASKED_5M_CANONICAL_HOURS")
        canonical[asset]=df[["open","high","low","close","quote_volume"]].to_numpy(dtype=float)
    expected=(pd.date_range(START,periods=HOURS,freq="h",tz="UTC").asi8//1000000).astype(np.int64)
    pairs=[(a,m) for a in ASSETS for m in MONTHS]
    results={};transport_faults={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(fetch_month,*pair):pair for pair in pairs}
        for future in concurrent.futures.as_completed(futures):
            pair=futures[future]
            try:results[pair]=future.result()
            except Exception as exc:transport_faults[pair]=type(exc).__name__+": "+str(exc)[:240]
    records=[];verified=[];quarantined=[];manifest={}
    for asset in ASSETS:
        offset=0
        for month in MONTHS:
            year,mon=map(int,month.split("-"))
            hours=calendar.monthrange(year,mon)[1]*24
            sl=slice(offset,offset+hours)
            t=expected[sl];base=canonical[asset][sl]
            valid=False;features=None;sha=None
            if (asset,month) in results:
                _,_,zipsha,member_sha,times,ohlc,feat=results[(asset,month)]
                sha={"zip_sha256":zipsha,"csv_sha256":member_sha}
                try:
                    if not np.array_equal(times,t):
                        raise ValueError("MASKED_5M_MONTH_HOUR_ALIGNMENT")
                    compare_1h(ohlc,base)
                    valid=True;features=feat
                    verified.append({"asset":asset,"month":month,**sha})
                except Exception as exc:
                    quarantined.append({"asset":asset,"month":month,
                                        "reason":type(exc).__name__+": "+str(exc)[:200],**sha})
            else:
                quarantined.append({"asset":asset,"month":month,
                                    "reason":transport_faults[(asset,month)]})
            manifest[asset+"/"+month]={"verified":valid,**(sha or {})}
            for i,stamp in enumerate(t):
                value=(features[i] if valid else None)
                usable=bool(valid and np.isfinite(value).all())
                values=tuple(float(v) for v in value) if usable else (None,)*6
                records.append((int(stamp),asset,int(usable),*values))
            offset+=hours
        if offset!=HOURS:raise ValueError("MASKED_5M_CALENDAR_OFFSET")
    out=pd.DataFrame(records,columns=COLS)
    out["open_time"]=pd.to_datetime(out["open_time"],unit="ms",utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    raw=out.to_csv(index=False,float_format="%.17g",na_rep="").encode()
    OUT.write_bytes(raw)
    valid_hours=int(out["source_valid"].sum())
    report={"source_only":True,"historical_system_pnl_computed":False,
            "validation_2025_read":False,"external_benchmarks_used":False,
            "trading_authorized":False,"source_contract":"MONTHLY_FAIL_CLOSED_QUARANTINE",
            "assets":list(ASSETS),"months":list(MONTHS),
            "archives_expected":len(pairs),"archives_verified":len(verified),
            "archives_quarantined":len(quarantined),
            "asset_hours_expected":HOURS*len(ASSETS),
            "asset_hours_source_valid":valid_hours,
            "asset_hours_masked":HOURS*len(ASSETS)-valid_hours,
            "feature_csv_sha256":hashlib.sha256(raw).hexdigest(),
            "manifest":manifest,"verified":verified,"quarantined":quarantined,
            "decision":"MASKED_5M_SOURCE_ONLY_NO_ECONOMIC_AUTHORIZATION"}
    if (len(records)!=HOURS*len(ASSETS) or
        any(not any(x["asset"]==a for x in verified) for a in ASSETS)):
        report["decision"]="BLOCK_MASKED_5M_SOURCE_COVERAGE"
    RECEIPT.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("MASKED_NATIVE_5M_SOURCE",report["decision"],"verified_months",len(verified),
          "quarantined_months",len(quarantined),"valid_asset_hours",valid_hours,
          "first_quarantine",quarantined[:10],flush=True)
    return report

if __name__=="__main__":
    report=run()
    raise SystemExit(0 if report["decision"]=="MASKED_5M_SOURCE_ONLY_NO_ECONOMIC_AUTHORIZATION" else 2)
