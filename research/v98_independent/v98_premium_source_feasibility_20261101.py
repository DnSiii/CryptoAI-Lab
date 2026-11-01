#!/usr/bin/env python3
"""V98 source-only feasibility: official USD-M premium-index hourly archive, NO PnL."""
import csv,datetime as dt,hashlib,io,json,re,zipfile
from urllib.request import Request,urlopen

CASES=(("BTCUSDT","2023-01"),("ETHUSDT","2024-06"),
       ("BNBUSDT","2025-01"),("SOLUSDT","2025-12"))
BASE="https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines"
LIMIT=2_000_000

def get(url):
    req=Request(url,headers={"User-Agent":"V98-Independent-Premium-Source-Only/1.0"})
    with urlopen(req,timeout=25) as response:
        if response.status!=200:raise ValueError("HTTP_"+str(response.status))
        data=response.read(LIMIT+1)
    if not data or len(data)>LIMIT:raise ValueError("EMPTY_OR_OVERSIZE")
    return data

def probe(asset,ym):
    if asset not in ("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT") or ym not in ("2023-01","2024-06","2025-01","2025-12"):
        raise ValueError("OUT_OF_SCOPE")
    name=f"{asset}-1h-{ym}.zip"
    url=f"{BASE}/{asset}/1h/{name}"
    archive=get(url);check=get(url+".CHECKSUM").decode("utf-8").strip()
    digest=hashlib.sha256(archive).hexdigest()
    if not re.fullmatch(r"[a-fA-F0-9]{64}\s+\*?"+re.escape(name),check):
        raise ValueError("BAD_OFFICIAL_CHECKSUM_FORMAT")
    if check.split()[0].lower()!=digest:raise ValueError("VENDOR_SHA_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        names=z.namelist()
        if len(names)!=1 or not names[0].endswith(".csv"):raise ValueError("BAD_ZIP_MEMBERS")
        raw=z.read(names[0])
    rows=list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    if not rows:raise ValueError("EMPTY_CSV")
    header=rows[0][0].lower() in ("open_time","open time","timestamp")
    if header:rows=rows[1:]
    start=dt.datetime.strptime(ym,"%Y-%m").replace(tzinfo=dt.timezone.utc)
    end=(start.replace(year=start.year+1,month=1) if start.month==12 else start.replace(month=start.month+1))
    hours=int((end-start).total_seconds()/3600)
    if len(rows)!=hours:raise ValueError(f"BAD_HOURLY_COVERAGE_{len(rows)}_EXPECTED_{hours}")
    vals=[]
    for i,row in enumerate(rows):
        if len(row)<5:raise ValueError("BAD_COLUMN_COUNT")
        stamp=int(row[0])
        if stamp!=int(start.timestamp()*1000)+i*3600000:raise ValueError("NONCAUSAL_HOURLY_CLOCK")
        vals.append(float(row[4]))
    if not all(abs(x)<1 for x in vals):raise ValueError("BAD_PREMIUM_SCALE")
    return {"asset":asset,"month":ym,"source_url":url,"vendor_zip_sha256":digest,
            "csv_sha256":hashlib.sha256(raw).hexdigest(),"rows":len(rows),
            "csv_columns":len(rows[0]),"header":header,
            "first_utc":start.isoformat(),"last_utc":(end-dt.timedelta(hours=1)).isoformat(),
            "premium_close_min":min(vals),"premium_close_max":max(vals),
            "provenance":"OFFICIAL_BINANCE_VISION_CHECKSUM_NOT_EXCHANGE_TICK"}

def main():
    records=[]
    for asset,ym in CASES:
        try:
            r=probe(asset,ym);records.append(r)
            print("V98_PREMIUM_PROBE",json.dumps(r,sort_keys=True),flush=True)
        except Exception as e:
            records.append({"asset":asset,"month":ym,"error":type(e).__name__+":"+str(e)})
            print("V98_PREMIUM_PROBE_FAIL",asset,ym,str(e),flush=True)
    result={"decision":"PASS_PREMIUM_SOURCE_FEASIBILITY_NOT_PNL" if all("error" not in r for r in records)
            else "REJECT_OR_INCOMPLETE_PREMIUM_SOURCE_FEASIBILITY",
            "records":records,"pnl_computed":False,"2026_plus_accessed":False,
            "exact_funding_event_mark_attested":False,"holdout_accessed":False}
    print("V98_PREMIUM_REPORT",json.dumps(result,sort_keys=True),flush=True)
    with open("v98_premium_source_feasibility_result.json","w") as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    if result["decision"]!="PASS_PREMIUM_SOURCE_FEASIBILITY_NOT_PNL":
        raise SystemExit("PREMIUM_SOURCE_FEASIBILITY_FAILED")

if __name__=="__main__":main()
