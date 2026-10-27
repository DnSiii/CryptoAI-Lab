#!/usr/bin/env python3
"""V98 Independent source-only OI historical availability/provenance probe.
12 pinned Binance Vision USD-M daily metrics ZIPs (2023/24 only). NO PnL.
"""
from __future__ import annotations
import csv,datetime as dt,hashlib,io,json,re,statistics,urllib.request,zipfile
from pathlib import Path

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
DATES=("2023-01-21","2024-07-01","2024-12-01")
ROOT="https://data.binance.vision/data/futures/um/daily/metrics"
OUT=Path(__file__).resolve().parent/"v98_oi_native_source_probe_20261027.json"

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"V98-Independent-source-integrity/1.0"})
    with urllib.request.urlopen(req,timeout=30) as response:
        return response.read()

def timestamp(s):
    s=s.strip().replace("Z","+00:00")
    if re.fullmatch(r"\d{13}",s):
        return dt.datetime.fromtimestamp(int(s)/1000,tz=dt.timezone.utc)
    if re.fullmatch(r"\d{10}",s):
        return dt.datetime.fromtimestamp(int(s),tz=dt.timezone.utc)
    x=dt.datetime.fromisoformat(s)
    return x.replace(tzinfo=dt.timezone.utc) if x.tzinfo is None else x.astimezone(dt.timezone.utc)

def check(symbol,date):
    base=f"{ROOT}/{symbol}/{symbol}-metrics-{date}.zip"
    payload=get(base)
    sha=hashlib.sha256(payload).hexdigest()
    sidecar=get(base+".CHECKSUM").decode("utf-8-sig").strip()
    match=re.search(r"\b[a-fA-F0-9]{64}\b",sidecar)
    if match is None or match.group(0).lower()!=sha:
        raise ValueError("V98_OI_VENDOR_CHECKSUM_MISMATCH_OR_MISSING")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names=[n for n in archive.namelist() if n.lower().endswith(".csv")]
        if len(names)!=1:raise ValueError("V98_OI_ZIP_CSV_COUNT")
        text=archive.read(names[0]).decode("utf-8-sig")
    rows=list(csv.DictReader(io.StringIO(text)))
    if not rows:raise ValueError("V98_OI_NO_ROWS")
    columns=sorted(rows[0])
    time_key=next((k for k in ("create_time","timestamp","time") if k in rows[0]),None)
    oi_key=next((k for k in ("sum_open_interest","sumOpenInterest") if k in rows[0]),None)
    if not time_key or not oi_key:raise ValueError("V98_OI_MISSING_TIME_OR_OI_COLUMN")
    stamps=[timestamp(r[time_key]) for r in rows]
    if stamps!=sorted(set(stamps)):raise ValueError("V98_OI_DUPLICATE_OR_NONMONOTONIC_TIME")
    if any(x.date()!=dt.date.fromisoformat(date) for x in stamps):
        raise ValueError("V98_OI_WRONG_DAY")
    if any(not (0<float(r[oi_key])<1e18) for r in rows):
        raise ValueError("V98_OI_NONPOSITIVE_OI")
    if "symbol" in rows[0] and any(r["symbol"]!=symbol for r in rows):
        raise ValueError("V98_OI_WRONG_SYMBOL")
    gaps=[(b-a).total_seconds()/60 for a,b in zip(stamps,stamps[1:])]
    median=statistics.median(gaps) if gaps else None
    if len(stamps)<24 or not gaps or max(gaps)>60:
        raise ValueError("V98_OI_INSUFFICIENT_INTRADAY_CADENCE")
    return {"asset":symbol,"day":date,"zip_sha256":sha,"vendor_checksum":True,
            "rows":len(rows),"first_utc":stamps[0].isoformat(),
            "last_utc":stamps[-1].isoformat(),"median_gap_minutes":median,
            "max_gap_minutes":max(gaps),"columns":columns}

def run():
    rows=[]
    for day in DATES:
        for symbol in ASSETS:
            try:
                v=check(symbol,day);v["passed"]=True
            except Exception as exc:
                v={"asset":symbol,"day":day,"passed":False,
                   "error":str(exc)[:300]}
            rows.append(v)
            print("V98_OI_SOURCE",symbol,day,"PASS" if v["passed"] else "BLOCK",v.get("rows"),v.get("error",""),flush=True)
    passed=sum(x["passed"] for x in rows)
    report={"probe_only":True,"no_pnl":True,"holdout_2025_read":False,
            "external_benchmarks_used":False,"trading_authorized":False,
            "assets":ASSETS,"dates":DATES,"files_expected":12,"files_authenticated":passed,
            "decision":"PASS_V98_OI_SAMPLE_SOURCE_ONLY_NEEDS_FULL_HISTORICAL_PROVENANCE"
                if passed==12 else "BLOCK_V98_OI_SAMPLE_SOURCE_INTEGRITY_OR_CADENCE",
            "results":rows}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("V98_OI_SOURCE_GATE",report["decision"],passed,"/12",flush=True)
    return report
if __name__=="__main__":
    result=run()
    raise SystemExit(0 if result["files_authenticated"]==12 else 2)
