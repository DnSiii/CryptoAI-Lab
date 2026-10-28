#!/usr/bin/env python3
"""Independent raw-ZIP reader and original 1h receipt audit; no primary parser import."""
from __future__ import annotations
import csv,hashlib,io,json,re,zipfile,math
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
from phase1260_aj_authenticated_source_digest import load_official
ROOT=Path(__file__).resolve().parent
RAW=ROOT/"v98_intrabar_1m_raw"
REPORT=ROOT/"v98_intrabar_1m_primary_receipt.json"
OUT=ROOT/"v98_intrabar_1m_independent_receipt.json"
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
DATES=("2023-01-15","2023-04-15","2023-07-15","2023-10-15",
       "2024-01-15","2024-04-15","2024-07-15","2024-10-15")
def sha(b):return hashlib.sha256(b).hexdigest()
def close(a,b,price):
    return abs(a-b)<=max(1e-8 if price else 1e-6,(1e-10 if price else 1e-8)*max(abs(a),abs(b)))
def verify(name,day,canonical):
    zpath=RAW/name
    raw=zpath.read_bytes()
    side=(RAW/(name+".CHECKSUM")).read_text().strip().splitlines()
    if len(side)!=1:raise ValueError("PUBLISHER_SIDECAR_LINES")
    expected=side[0].split()[0].lower()
    if not re.fullmatch("[0-9a-f]{64}",expected) or sha(raw)!=expected:
        raise ValueError("INDEPENDENT_SHA256")
    if len(side[0].split())>1 and side[0].split()[-1].lstrip("*").split("/")[-1]!=name:
        raise ValueError("INDEPENDENT_SIDECAR_NAME")
    with zipfile.ZipFile(io.BytesIO(raw)) as f:
        names=[x for x in f.namelist() if not x.endswith("/")]
        if len(names)!=1 or names[0].split("/")[-1]!=name[:-4]+".csv":
            raise ValueError("INDEPENDENT_ZIP_MEMBER")
        lines=f.read(names[0]).decode("utf-8-sig").splitlines()
    data=list(csv.reader(lines))
    if data and data[0][0].lower().strip() in ("open_time","opentime"):
        data=data[1:]
    if len(data)!=1440:raise ValueError("INDEPENDENT_MINUTES_"+str(len(data)))
    epoch=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1000)
    groups=[[] for _ in range(24)]
    for k,row in enumerate(data):
        if len(row)<11:raise ValueError("INDEPENDENT_SCHEMA")
        t=int(row[0])
        if t!=epoch+k*60000:raise ValueError("INDEPENDENT_GRID_"+str(k))
        if int(row[6])<t or int(row[6])>t+59999:raise ValueError("INDEPENDENT_CLOSE_TIME")
        nums=[float(row[j]) for j in (1,2,3,4,5,7)]
        if not all(math.isfinite(x) for x in nums):raise ValueError("INDEPENDENT_NONFINITE")
        op,hi,lo,cl,vol,quote=nums
        if min(op,hi,lo,cl)<=0 or hi<max(op,cl) or lo>min(op,cl) or vol<0 or quote<0:
            raise ValueError("INDEPENDENT_GEOMETRY")
        if quote<vol*lo-1e-6*max(1,quote) or quote>vol*hi+1e-6*max(1,quote):
            raise ValueError("INDEPENDENT_QUOTE_UNITS")
        groups[k//60].append(nums)
    for hour,chunk in enumerate(groups):
        agg=[chunk[0][0],max(r[1] for r in chunk),min(r[2] for r in chunk),
             chunk[-1][3],sum(r[4] for r in chunk),sum(r[5] for r in chunk)]
        ts=pd.Timestamp(epoch+hour*3600000,unit="ms",tz="UTC")
        if ts not in canonical.index:raise ValueError("INDEPENDENT_HOUR_MISSING")
        target=canonical.loc[ts]
        for j,key in enumerate(("open","high","low","close","volume","quote_volume")):
            if not close(agg[j],float(target[key]),j<4):
                raise ValueError(f"INDEPENDENT_MISMATCH:{hour}:{key}")
    return expected
def main():
    _,manifest=load_official()
    orig=json.loads(REPORT.read_text())
    canonical={}
    for a in ASSETS:
        d=pd.read_csv(ROOT/"phase243_clean4_canonical"/(a+"_1h.csv"))
        canonical[a]=d.set_index(pd.to_datetime(d["open_time"],utc=True))
    passed=0;errors=[];checked={}
    for asset in ASSETS:
        for day in DATES:
            name=f"{asset}-1m-{day}.zip"
            try:
                checked[name]=verify(name,day,canonical[asset])
                original=next((r for r in orig["rows"] if r["asset"]==asset and r["date"]==day),None)
                if original is None or original.get("sha256")!=checked[name] or original.get("status")!="PASS":
                    raise ValueError("INDEPENDENT_RECEIPT_DISAGREEMENT")
                passed+=1
            except Exception as e:
                errors.append({"asset":asset,"date":day,"error":str(e)[:200]})
    source_pin=sha(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode())
    if orig.get("canonical_manifest_sha256")!=source_pin:
        errors.append({"error":"INDEPENDENT_CANONICAL_PIN_DISAGREEMENT"})
    if orig.get("passed_asset_days")!=passed or len(orig.get("rows",[]))!=32:
        errors.append({"error":"INDEPENDENT_INVENTORY_DISAGREEMENT"})
    result={"decision":"PASS_INDEPENDENT_1M_SOURCE_ONLY_NOT_PNL" if not errors and passed==32 else "REJECT_1M_SOURCE_NO_PNL",
            "independent_parser":True,"passed_asset_days":passed,"expected_asset_days":32,
            "verified_minutes":passed*1440,"verified_hourly_aggregates":passed*24,
            "canonical_manifest_sha256":source_pin,"errors":errors,
            "validation_2025_read":False,"future_holdout_read":False,
            "pnl_computed":False,"trading_authorized":False}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("V98_INDEPENDENT_INTRABAR",result["decision"],passed,"/32",errors[:4],flush=True)
    raise SystemExit(0 if not errors and passed==32 else 2)
if __name__=="__main__":main()
