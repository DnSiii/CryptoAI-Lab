#!/usr/bin/env python3
"""KE prospective official Binance USD-M bookDepth 2023-24 source-only coverage probe; NO PnL."""
from __future__ import annotations
import concurrent.futures,csv,hashlib,io,json,urllib.error,urllib.request,zipfile
from pathlib import Path
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
DATES=("2023-01-15","2023-07-15","2024-01-15","2024-07-15","2024-12-15")
BASE="https://data.binance.vision/data/futures/um/daily/bookDepth"
OUT=Path(__file__).resolve().parent/"ke_bookdepth_source_feasibility.json"

def get(url,limit):
    if not url.startswith(BASE+"/") or not (url.endswith(".CHECKSUM") or url.endswith(".zip")):
        raise ValueError("KE_FORBIDDEN_SOURCE")
    req=urllib.request.Request(url,headers={"User-Agent":"V98-Independent-KE-Source-Only/1.0"})
    with urllib.request.urlopen(req,timeout=18) as response:
        if response.status!=200 or response.geturl()!=url:
            raise ValueError("KE_REDIRECT_OR_STATUS")
        raw=response.read(limit+1)
    if len(raw)>limit:raise ValueError("KE_SOURCE_TOO_LARGE")
    return raw

def probe(asset,day):
    if asset not in ASSETS or day not in DATES:raise ValueError("KE_FORBIDDEN_SCOPE")
    name=f"{asset}-bookDepth-{day}.zip"
    url=f"{BASE}/{asset}/{name}"
    row={"asset":asset,"day":day,"source":url,"source_only":True,
         "validation_2025_read":False,"system_pnl_computed":False}
    try:
        check=get(url+".CHECKSUM",4096).decode("utf-8-sig").strip().split()
        if len(check)!=2 or check[1].lstrip("*./")!=name or len(check[0])!=64:
            raise ValueError("KE_PUBLISHER_CHECKSUM_SCHEMA")
        expected=check[0].lower()
        if any(ch not in "0123456789abcdef" for ch in expected):
            raise ValueError("KE_CHECKSUM_HEX")
        raw=get(url,25000000)
        if hashlib.sha256(raw).hexdigest()!=expected:
            raise ValueError("KE_PUBLISHER_SHA_MISMATCH")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.namelist()!=[name[:-4]+".csv"]:
                raise ValueError("KE_ZIP_MEMBER")
            member=z.read(z.namelist()[0])
        if len(member)>100000000:raise ValueError("KE_CSV_SIZE")
        rows=csv.reader(io.StringIO(member.decode("utf-8-sig")))
        header=next(rows,None)
        if not header or len(header)<2:raise ValueError("KE_CSV_SCHEMA")
        first=next(rows,None)
        if first is None:raise ValueError("KE_EMPTY_CSV")
        count=1+sum(1 for _ in rows)
        row.update(status="PUBLISHER_VERIFIED_SAMPLE",zip_sha256=expected,
                   bytes=len(raw),csv_rows=count,csv_header=header[:16],
                   first_row_preview=first[:4])
    except urllib.error.HTTPError as exc:
        row.update(status="PUBLISHER_404_MISSING" if exc.code==404 else "HTTP_ERROR",
                   http_status=exc.code)
    except Exception as exc:
        row.update(status="TRANSPORT_OR_SCHEMA_ERROR",
                   error=type(exc).__name__+": "+str(exc)[:160])
    return row

def run():
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(lambda pair:probe(*pair),((a,d) for a in ASSETS for d in DATES)))
    verified=sum(r["status"]=="PUBLISHER_VERIFIED_SAMPLE" for r in rows)
    missing=sum(r["status"]=="PUBLISHER_404_MISSING" for r in rows)
    errors=sum(r["status"] not in ("PUBLISHER_VERIFIED_SAMPLE","PUBLISHER_404_MISSING") for r in rows)
    result={"architecture":"KE","source_only":True,"historical_system_pnl_computed":False,
            "validation_2025_read":False,"holdout_accessed":False,
            "external_benchmarks_used":False,"trading_authorized":False,
            "dates":list(DATES),"assets":list(ASSETS),
            "fixed_sample_probes":len(rows),"publisher_verified_samples":verified,
            "publisher_missing_samples":missing,"transport_or_schema_errors":errors,
            "results":rows,"decision":("PASS_KE_SAMPLE_ONLY_FULL_COVERAGE_NOT_ATTESTED" if verified==20 else
                                     "BLOCK_KE_SOURCE_INCOMPLETE_OR_UNVERIFIED")}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("KE_SOURCE_ONLY",result["decision"],"verified",verified,"404",missing,"errors",errors,flush=True)
    for row in rows:
        print("KE_SAMPLE",row["asset"],row["day"],row["status"],
              row.get("csv_rows"),row.get("error",""),flush=True)
    return result

if __name__=="__main__":run()
