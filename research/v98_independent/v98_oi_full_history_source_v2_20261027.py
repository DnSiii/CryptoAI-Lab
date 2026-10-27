#!/usr/bin/env python3
"""V98 Independent source-only 2022-24 Clean4 native OI archive acquisition.
Strict vendor checksum, 5m continuity, completed-hour sampling; NO PnL.
"""
from __future__ import annotations
import concurrent.futures,csv,datetime as dt,hashlib,io,json,math,statistics,time,urllib.error,zipfile
from pathlib import Path
from v98_oi_native_source_probe_20261027 import ASSETS,ROOT,get,timestamp

HERE=Path(__file__).resolve().parent
OUT=HERE/"v98_oi_full_history_source_v2_report_20261027.json"
CSV=HERE/"v98_oi_full_history_v2_verified_hourly_20261027.csv"
START=dt.date(2022,12,1)
END=dt.date(2024,12,31)
FIELDS=("bar_open_utc","asset","oi_contracts","oi_value_usdt","taker_ratio","source_zip_sha256")

def retry_get(url):
    for i in range(3):
        try:return get(url)
        except urllib.error.HTTPError as exc:
            if exc.code in (400,403,404):raise
            if i==2:raise
        except (TimeoutError,ConnectionError,OSError):
            if i==2:raise
        time.sleep(.4*(i+1))
    raise RuntimeError("V98_OI_DOWNLOAD_RETRY_EXHAUSTED")

def read_day(asset,day):
    date=day.isoformat()
    url=f"{ROOT}/{asset}/{asset}-metrics-{date}.zip"
    z=retry_get(url)
    checksum=retry_get(url+".CHECKSUM").decode("utf-8-sig")
    sha=hashlib.sha256(z).hexdigest()
    import re
    m=re.search(r"\b[a-fA-F0-9]{64}\b",checksum)
    if not m or m.group(0).lower()!=sha:
        raise ValueError("V98_OI_CHECKSUM")
    with zipfile.ZipFile(io.BytesIO(z)) as archive:
        files=[x for x in archive.namelist() if x.endswith(".csv")]
        if len(files)!=1:raise ValueError("V98_OI_ZIP_CSV_COUNT")
        rows=list(csv.DictReader(io.StringIO(archive.read(files[0]).decode("utf-8-sig"))))
    if len(rows)!=288:raise ValueError("V98_OI_EXPECTED_288_GOT_"+str(len(rows)))
    columns=set(rows[0])
    timekey=next((x for x in ("create_time","timestamp","time") if x in columns),None)
    oikey=next((x for x in ("sum_open_interest","sumOpenInterest") if x in columns),None)
    if not timekey or not oikey:raise ValueError("V98_OI_REQUIRED_COLUMNS")
    valuekey=next((x for x in ("sum_open_interest_value","sumOpenInterestValue") if x in columns),None)
    takerkey=next((x for x in ("sum_taker_long_short_vol_ratio",) if x in columns),None)
    ts=[timestamp(row[timekey]) for row in rows]
    if any(x.date()!=day for x in ts) or len(set(ts))!=len(ts):
        raise ValueError("V98_OI_WRONG_DAY_OR_DUPLICATE")
    order=sorted(range(len(ts)),key=lambda i:ts[i])
    reordered=order!=list(range(len(ts)))
    # Vendor archives in April/May 2024 can be fully complete yet shuffled.
    # This is strict SHA-preserving timestamp canonicalization, never a fill.
    rows=[rows[i] for i in order]
    ts=[ts[i] for i in order]
    if any((b-a).total_seconds()!=300 for a,b in zip(ts,ts[1:])):
        raise ValueError("V98_OI_NONCONTIGUOUS_5MIN")
    if ts[0].hour!=0 or ts[0].minute!=0 or ts[-1].hour!=23 or ts[-1].minute!=55:
        raise ValueError("V98_OI_DAY_BOUNDARY")
    hourly=[]
    for hour in range(24):
        block=rows[hour*12:(hour+1)*12]
        if ts[hour*12+11].hour!=hour or ts[hour*12+11].minute!=55:
            raise ValueError("V98_OI_HOURLY_CLOSE_ALIGNMENT")
        row=block[-1]
        oi=float(row[oikey])
        value=float(row[valuekey]) if valuekey else float("nan")
        taker=float(row[takerkey]) if takerkey else float("nan")
        if not math.isfinite(oi) or oi<=0 or (valuekey and (not math.isfinite(value) or value<=0)):
            raise ValueError("V98_OI_INVALID_VALUE")
        if takerkey and (not math.isfinite(taker) or taker<0):
            raise ValueError("V98_OI_INVALID_TAKER_RATIO")
        hourly.append((f"{date}T{hour:02d}:00:00+00:00",asset,
                       format(oi,".12g"),format(value,".12g") if valuekey else "",
                       format(taker,".12g") if takerkey else "",sha))
    if "symbol" in columns and any(row["symbol"]!=asset for row in rows):
        raise ValueError("V98_OI_SYMBOL_MISMATCH")
    return {"asset":asset,"date":date,"passed":True,"sha256":sha,
            "rows_5min":288,"hours":24,"source_rows_reordered":reordered,"columns":sorted(columns)},hourly

def attempt(pair):
    asset,day=pair
    try:return read_day(asset,day)
    except Exception as exc:
        return {"asset":asset,"date":day.isoformat(),"passed":False,
                "first_fault":str(exc)[:240]},[]

def run():
    days=(END-START).days+1
    pairs=[(asset,START+dt.timedelta(days=i)) for asset in ASSETS for i in range(days)]
    assert len(pairs)==days*4 and END.year==2024
    manifest=[];hours=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        futures=[pool.submit(attempt,p) for p in pairs]
        for idx,f in enumerate(concurrent.futures.as_completed(futures),1):
            entry,rows=f.result()
            manifest.append(entry);hours.extend(rows)
            if idx%150==0:
                print("V98_OI_PROGRESS",idx,"/",len(pairs),
                      "passed",sum(z["passed"] for z in manifest),flush=True)
    manifest.sort(key=lambda z:(z["asset"],z["date"]))
    hours.sort(key=lambda z:(z[0],z[1]))
    with CSV.open("w",newline="") as f:
        w=csv.writer(f);w.writerow(FIELDS);w.writerows(hours)
    passed=sum(x["passed"] for x in manifest)
    faults=[x for x in manifest if not x["passed"]]
    report={"source_only":True,"historical_training_only":True,
            "holdout_2025_read":False,"external_benchmarks_used":False,
            "trading_authorized":False,"pnl_computed":False,
            "date_start":START.isoformat(),"date_end":END.isoformat(),
            "assets":ASSETS,"files_expected":len(pairs),
            "files_verified_complete":passed,"files_quarantined":len(faults),
            "verified_hourly_rows":len(hours),"expected_hourly_rows":len(pairs)*24,
            "hourly_csv_sha256":hashlib.sha256(CSV.read_bytes()).hexdigest(),
            "decision":"PASS_FULL_OI_CAUSAL_SOURCE_NO_GAPS" if not faults else
                       "QUARANTINE_OI_SOURCE_GAPS_NO_PNL",
            "first_faults":faults[:40],"manifest":manifest}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("V98_OI_FULL_SOURCE",report["decision"],
          "files",passed,"/",len(pairs),"hours",len(hours),
          "quarantined",len(faults),"first",faults[:5],flush=True)
    return report
if __name__=="__main__":
    x=run()
    raise SystemExit(0 if not x["files_quarantined"] else 2)
