#!/usr/bin/env python3
"""V98 Independent official 1m stress source PROVENANCE ONLY. No strategy or PnL."""
from __future__ import annotations
import csv,hashlib,io,json,re,time,urllib.request,zipfile
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
from phase1260_aj_authenticated_source_digest import load_official
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
DATES=("2023-01-15","2023-04-15","2023-07-15","2023-10-15",
       "2024-01-15","2024-04-15","2024-07-15","2024-10-15")
BASE="https://data.binance.vision/data/futures/um/daily/klines"
ROOT=Path(__file__).resolve().parent
RAW=ROOT/"v98_intrabar_1m_raw"
REPORT=ROOT/"v98_intrabar_1m_primary_receipt.json"
EXPECTED=32
def digest(b):return hashlib.sha256(b).hexdigest()
def get(url):
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"V98-Independent-Provenance/1.0"})
            with urllib.request.urlopen(req,timeout=35) as r:
                if r.status!=200:raise ValueError("HTTP_"+str(r.status))
                return r.read()
        except Exception as e:
            last=e;time.sleep(1+attempt)
    raise RuntimeError("PROVIDER_FETCH:"+str(last))
def sidecar(raw,filename):
    line=raw.decode("utf-8").strip().splitlines()
    if len(line)!=1:raise ValueError("SIDECAR_LINE_COUNT")
    m=re.fullmatch(r"([0-9a-fA-F]{64})(?:\s+\*?([^\s]+))?",line[0].strip())
    if not m:raise ValueError("SIDECAR_SCHEMA")
    if m.group(2) and m.group(2).split("/")[-1]!=filename:
        raise ValueError("SIDECAR_WRONG_FILENAME")
    return m.group(1).lower()
def parse(raw,filename,expected_ms):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files=[x for x in z.namelist() if not x.endswith("/")]
        if len(files)!=1 or files[0].split("/")[-1]!=filename.replace(".zip",".csv"):
            raise ValueError("ZIP_MEMBER")
        with z.open(files[0]) as f:
            reader=csv.reader(io.TextIOWrapper(f,encoding="utf-8-sig"))
            bars=[]
            for row in reader:
                if row and row[0].strip().lower() in ("open_time","opentime"):continue
                if len(row)<11:raise ValueError("KLINE_SCHEMA")
                vals=[float(row[j]) for j in (1,2,3,4,5,7)]
                if not all(__import__("math").isfinite(v) for v in vals):raise ValueError("NONFINITE")
                o,h,l,c,v,q=vals
                if min(o,h,l,c)<=0 or h<max(o,c) or l>min(o,c) or v<0 or q<0:
                    raise ValueError("KLINE_GEOMETRY")
                if q < v*l-1e-6*max(1,q) or q > v*h+1e-6*max(1,q):
                    raise ValueError("QUOTE_BASE_UNITS")
                start=int(row[0]);end=int(row[6])
                if end<start or end>start+59999:raise ValueError("CLOSE_TIME")
                bars.append((start,o,h,l,c,v,q))
    if len(bars)!=1440:raise ValueError("MINUTE_COUNT:"+str(len(bars)))
    times=[r[0] for r in bars]
    if len(set(times))!=1440 or times!=list(range(expected_ms,expected_ms+86400000,60000)):
        raise ValueError("MINUTE_GRID_OR_ORDER")
    return bars
def same(x,y,kind):
    tol=max(1e-8,1e-10*max(abs(x),abs(y))) if kind=="price" else max(1e-6,1e-8*max(abs(x),abs(y)))
    return abs(x-y)<=tol
def synthetic():
    base=[i*60000 for i in range(1440)]
    assert len(base)==1440 and len(set(base))==1440
    for altered in (base[:-1],base[:10]+base[9:10]+base[11:],base[:10]+base[11:12]+base[10:11]+base[12:]):
        if len(altered)==1440 and altered==base:raise ValueError("SYNTHETIC_TEST_FAILED")
    assert digest(b"raw")!=digest(b"tampered")
    assert not same(100.,101.,"price")
    return True
def main():
    assert synthetic()
    frames,manifest=load_official()
    RAW.mkdir(parents=True,exist_ok=True)
    anchors={}
    for asset in ASSETS:
        d=pd.read_csv(ROOT/"phase243_clean4_canonical"/(asset+"_1h.csv"))
        anchors[asset]=d.set_index(pd.to_datetime(d["open_time"],utc=True))
    rows=[];fail=[]
    for asset in ASSETS:
        for day in DATES:
            name=f"{asset}-1m-{day}.zip"
            url=f"{BASE}/{asset}/1m/{name}"
            record={"asset":asset,"date":day,"archive":name}
            try:
                z=RAW/name;check=RAW/(name+".CHECKSUM")
                raw=get(url);side=get(url+".CHECKSUM")
                expected=sidecar(side,name)
                if digest(raw)!=expected:raise ValueError("PUBLISHER_SHA256_MISMATCH")
                z.write_bytes(raw);check.write_bytes(side)
                midnight=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000)
                bars=parse(raw,name,midnight)
                for hour in range(24):
                    p=bars[hour*60:(hour+1)*60]
                    agg=(p[0][1],max(x[2] for x in p),min(x[3] for x in p),
                         p[-1][4],sum(x[5] for x in p),sum(x[6] for x in p))
                    ts=pd.Timestamp(midnight+hour*3600000,unit="ms",tz="UTC")
                    if ts not in anchors[asset].index:raise ValueError("MISSING_HOURLY_ANCHOR")
                    ref=anchors[asset].loc[ts]
                    for j,col in enumerate(("open","high","low","close","volume","quote_volume")):
                        if not same(agg[j],float(ref[col]),"price" if j<4 else "volume"):
                            raise ValueError(f"HOURLY_MISMATCH:{hour:02d}:{col}:{agg[j]}:{ref[col]}")
                record.update({"status":"PASS","sha256":expected,"minutes":1440,"hourly":24})
            except Exception as e:
                record.update({"status":"FAIL","error":str(e)[:350]})
                fail.append(record)
            rows.append(record)
            print("V98_1M_PROBE",asset,day,record["status"],record.get("error",""),flush=True)
    passed=sum(x["status"]=="PASS" for x in rows)
    receipt={"source_only":True,"pnl_computed":False,"validation_2025_read":False,
        "future_holdout_read":False,"benchmarks_read":False,"trading_authorized":False,
        "provider":"Binance USD-M official daily 1m klines","assets":list(ASSETS),
        "dates":list(DATES),"expected_asset_days":EXPECTED,"passed_asset_days":passed,
        "verified_minutes":passed*1440,"verified_hourly_aggregates":passed*24,
        "canonical_manifest_sha256":digest(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()),
        "rows":rows,"first_faults":fail,
        "decision":"PASS_SOURCE_ONLY_REQUIRES_INDEPENDENT_REPLAY" if passed==EXPECTED else "REJECT_1M_SOURCE_NO_PNL"}
    REPORT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print("V98_1M_PROVENANCE",receipt["decision"],passed,"/",EXPECTED,flush=True)
if __name__=="__main__":main()
