#!/usr/bin/env python3
"""JQ native 5m chronological path SOURCE ONLY; pinned Clean-4 2022-12..2024-12.
Never computes signals, returns, strategy PnL, validation or benchmarks.
"""
from __future__ import annotations
import calendar,concurrent.futures,hashlib,io,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from phase803_training_ohlc_official_replay import ASSETS,MONTHS,BASE,PINS,download,checksum
from phase1260_aj_authenticated_source_digest import HOURS,START

HERE=Path(__file__).resolve().parent
FEATURES=HERE/"jq_native_5m_verified_hourly_features.csv"
RECEIPT=HERE/"jq_native_5m_source_receipt.json"
FIELDS=("open_time","asset","early_trough_pct","late_rebound_log",
        "late_selloff_log","path_realized_vol","first_half_taker_share",
        "second_half_taker_share")
RAW=("open_time","open","high","low","close","volume","close_time",
     "quote_volume","trade_count","taker_buy_base","taker_buy_quote","ignore")
PASS="PASS_JQ_NATIVE_5M_SOURCE_ONLY_NOT_ECONOMIC"

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def verify_archive(raw,sidecar,name):
    expected=checksum(sidecar,name)
    actual=digest(raw)
    if actual!=expected:raise ValueError("JQ_VENDOR_SHA256_MISMATCH")
    member=name[:-4]+".csv"
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=[member]:raise ValueError("JQ_ZIP_MEMBER_MISMATCH")
        data=z.read(member)
    return data,actual,digest(data)

def parse_month(data,asset,month):
    """Return month-ordered 5m rows and per-hour path features, without forecasting."""
    if asset not in ASSETS or month not in MONTHS:
        raise ValueError("JQ_TRAINING_FIREWALL")
    df=pd.read_csv(io.BytesIO(data),header=None,dtype=str,keep_default_na=False)
    if df.shape[1]!=12:raise ValueError("JQ_RAW_12_COLUMN_SCHEMA")
    if str(df.iloc[0,0]).strip().lower()=="open_time":
        if str(df.iloc[0,0]).strip().lower()!="open_time":
            raise ValueError("JQ_RAW_HEADER_SCHEMA")
        df=df.iloc[1:].reset_index(drop=True)
    year,mon=map(int,month.split("-"))
    first=int(datetime(year,mon,1,tzinfo=timezone.utc).timestamp()*1000)
    hours=calendar.monthrange(year,mon)[1]*24
    expected=first+np.arange(hours*12,dtype=np.int64)*300000
    opened=pd.to_numeric(df.iloc[:,0],errors="raise").to_numpy(dtype=np.int64)
    ended=pd.to_numeric(df.iloc[:,6],errors="raise").to_numpy(dtype=np.int64)
    if (len(opened)!=len(expected) or not np.array_equal(opened,expected)
        or not np.array_equal(ended,opened+299999)):
        raise ValueError("JQ_5M_UTC_ORDER_MISSING_DUPLICATE_OR_CLOSE_TIME")
    x=np.column_stack([pd.to_numeric(df.iloc[:,j],errors="raise").to_numpy(dtype=float)
                       for j in (1,2,3,4,7,10)])
    if not np.isfinite(x).all():raise ValueError("JQ_NONFINITE_NATIVE_5M")
    op,hi,lo,cl,q,taker=(x[:,j] for j in range(6))
    if (np.any(op<=0) or np.any(cl<=0) or np.any(lo<=0)
        or np.any(lo>np.minimum(op,cl)) or np.any(hi<np.maximum(op,cl))
        or np.any(q<0) or np.any(taker<0) or np.any(taker>q*(1+1e-8)+1e-8)):
        raise ValueError("JQ_NATIVE_5M_GEOMETRY_OR_TAKER")
    a=x.reshape(hours,12,6)
    oo=a[:,0,0]; hh=a[:,:,1].max(axis=1); ll=a[:,:,2].min(axis=1)
    cc=a[:,-1,3]; qq=a[:,:,4].sum(axis=1)
    early_low=a[:,:6,2].min(axis=1)
    early_high=a[:,:6,1].max(axis=1)
    prev=np.column_stack((oo,a[:,:-1,3]))
    vol=np.sqrt(np.square(np.log(a[:,:,3]/prev)).sum(axis=1))
    early_q=a[:,:6,4].sum(axis=1); late_q=a[:,6:,4].sum(axis=1)
    early_t=a[:,:6,5].sum(axis=1); late_t=a[:,6:,5].sum(axis=1)
    early_share=np.divide(early_t,early_q,out=np.full(hours,np.nan),where=early_q>0)
    late_share=np.divide(late_t,late_q,out=np.full(hours,np.nan),where=late_q>0)
    feature=np.column_stack((early_low/oo-1.,np.log(cc/early_low),
                             np.log(cc/early_high),vol,early_share,late_share))
    if not np.isfinite(feature[:,:4]).all():raise ValueError("JQ_PATH_FEATURE_NONFINITE")
    if np.any(np.isfinite(feature[:,4:])&((feature[:,4:]<0)|(feature[:,4:]>1+1e-8))):
        raise ValueError("JQ_PATH_TAKER_SHARE_INVALID")
    return expected[::12],np.column_stack((oo,hh,ll,cc,qq)),feature

def compare_1h(actual,canonical):
    if actual.shape!=canonical.shape:raise ValueError("JQ_CANONICAL_HOUR_COUNT")
    if not np.isfinite(canonical).all():raise ValueError("JQ_CANONICAL_NONFINITE")
    diff=np.abs(actual-canonical)
    tolerance=np.array([1e-8,1e-8,1e-8,1e-8,1e-6])+np.abs(canonical)*np.array(
        [2e-10,2e-10,2e-10,2e-10,2e-8])
    if np.any(diff>tolerance):
        i,j=np.argwhere(diff>tolerance)[0]
        raise ValueError(f"JQ_PINNED_1H_RECONCILIATION_{int(i)}_{int(j)}")
    return diff.max(axis=0).tolist()

def conflict_evidence(actual,canonical,times,entries):
    """SOURCE FORENSIC ONLY. Never relax or override the precommitted gate."""
    delta=np.abs(actual-canonical)
    tolerance=np.array([1e-8,1e-8,1e-8,1e-8,1e-6])+np.abs(canonical)*np.array(
        [2e-10,2e-10,2e-10,2e-10,2e-8])
    bad=np.argwhere(delta>tolerance)
    fields=("open","high","low","close","quote_volume")
    by_month={e[1]:e[2] for e in entries}
    rows=[]
    for i,j in bad[:40]:
        date=pd.to_datetime(int(times[i]),unit="ms",utc=True)
        rows.append({"hour_utc":date.isoformat(),"field":fields[int(j)],
                     "native_5m_aggregate":float(actual[i,j]),
                     "pinned_1h":float(canonical[i,j]),
                     "absolute_difference":float(delta[i,j]),
                     "relative_difference":float(delta[i,j]/max(abs(canonical[i,j]),1e-12)),
                     "vendor_5m_zip_sha256":by_month[date.strftime("%Y-%m")]})
    months=sorted({pd.to_datetime(int(times[i]),unit="ms",utc=True).strftime("%Y-%m")
                   for i in np.unique(bad[:,0])})
    return {"bad_cells":int(len(bad)),
            "bad_hour_count":int(len(np.unique(bad[:,0]))),
            "affected_months":months,
            "examples":rows}

def fetch_month(asset,month):
    if asset not in ASSETS or month not in MONTHS:raise ValueError("JQ_TRAINING_FIREWALL")
    name=f"{asset}-5m-{month}.zip"
    url=f"{BASE}/{asset}/5m/{name}"
    data,zipsha,membersha=verify_archive(download(url),download(url+".CHECKSUM"),name)
    opened,hourly,feature=parse_month(data,asset,month)
    return (asset,month,zipsha,membersha,opened,hourly,feature)

def run():
    if (len(MONTHS)!=25 or MONTHS[0]!="2022-12" or MONTHS[-1]!="2024-12"
        or HOURS!=18288 or len(ASSETS)!=4):
        raise ValueError("JQ_SOURCE_TRAINING_CALENDAR_FIREWALL")
    official_times=(pd.date_range(START,periods=HOURS,freq="h",tz="UTC").asi8//1000000).astype(np.int64)
    canonical={}
    for asset in ASSETS:
        raw=(HERE/"phase243_clean4_canonical"/f"{asset}_1h.csv").read_bytes()
        pin,size=PINS[asset]
        if digest(raw)!=pin or len(raw)!=size:raise ValueError("JQ_PINNED_1H_SHA_"+asset)
        df=pd.read_csv(io.BytesIO(raw))
        if len(df)!=HOURS:raise ValueError("JQ_PINNED_1H_HOURS_"+asset)
        canonical[asset]=df[["open","high","low","close","quote_volume"]].to_numpy(dtype=float)
    pairs=[(asset,month) for asset in ASSETS for month in MONTHS]
    verified={};faults=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(fetch_month,*p):p for p in pairs}
        for future in concurrent.futures.as_completed(futures):
            asset,month=futures[future]
            try:verified[(asset,month)]=future.result()
            except Exception as exc:
                faults.append({"asset":asset,"month":month,
                               "first_fault":type(exc).__name__+": "+str(exc)[:260]})
    faults.sort(key=lambda x:(x["asset"],x["month"]))
    manifests={};lines=[];maxdiff={};conflicts={}
    for asset in ASSETS:
        if any((asset,m) not in verified for m in MONTHS):continue
        entries=[verified[(asset,m)] for m in MONTHS]
        times=np.concatenate([e[4] for e in entries])
        if not np.array_equal(times,official_times):
            faults.append({"asset":asset,"month":"FULL","first_fault":"JQ_FULL_UTC_ALIGNMENT"})
            continue
        manifests[asset]={e[1]:{"zip_sha256":e[2],"csv_sha256":e[3],
                                 "hours":len(e[4])} for e in entries}
        actual=np.concatenate([e[5] for e in entries])
        try:maxdiff[asset]=compare_1h(actual,canonical[asset])
        except Exception as exc:
            conflicts[asset]=conflict_evidence(actual,canonical[asset],times,entries)
            faults.append({"asset":asset,"month":"FULL","first_fault":str(exc),
                           "affected_months":conflicts[asset]["affected_months"]})
            continue
        features=np.concatenate([e[6] for e in entries])
        for i,t in enumerate(times):
            vals=[None if np.isnan(v) else float(v) for v in features[i]]
            lines.append((int(t),asset,*vals))
    faults.sort(key=lambda x:(x["asset"],x["month"]))
    report={"source_only":True,"historical_training_only":True,
            "historical_system_pnl_computed":False,"validation_2025_read":False,
            "external_benchmarks_used":False,"trading_authorized":False,
            "assets":list(ASSETS),"months":list(MONTHS),"archives_expected":len(pairs),
            "archives_checksum_and_schema_verified":len(verified),
            "hourly_rows_reconciled":len(lines),"hourly_rows_expected":HOURS*4,
            "max_absolute_hourly_1h_differences":maxdiff,
            "archive_manifest":manifests,"cross_source_conflicts":conflicts,"first_faults":faults[:100],
            "fault_count":len(faults),"decision":"BLOCK_JQ_NATIVE_5M_SOURCE_INCOMPLETE"}
    if not faults and len(lines)==HOURS*4:
        out=pd.DataFrame(lines,columns=FIELDS)
        out["open_time"]=pd.to_datetime(out["open_time"],unit="ms",utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        raw=out.to_csv(index=False,float_format="%.17g",na_rep="").encode()
        FEATURES.write_bytes(raw)
        report["features_sha256"]=digest(raw)
        report["decision"]=PASS
    RECEIPT.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("JQ_5M_SOURCE",report["decision"],"archives",len(verified),"/",len(pairs),
          "rows",len(lines),"/",HOURS*4,"faults",faults[:5],flush=True)
    return report

if __name__=="__main__":
    result=run()
    raise SystemExit(0 if result["decision"]==PASS else 2)
