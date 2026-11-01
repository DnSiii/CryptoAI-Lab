#!/usr/bin/env python3
"""Official 2025 spot source-only masked feasibility for future V98 two-leg basis research."""
import csv,datetime as dt,hashlib,io,json,math,time,urllib.request,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"v98_spot_2025_masked_source_only"
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
MONTHS=tuple(range(1,13))
BASE="https://data.binance.vision/data/spot/monthly/klines"
FIELDS=("asset","open_time_ms","open","high","low","close","quote_volume","source_zip_sha256")
HOUR=3600000

def sha(b):return hashlib.sha256(b).hexdigest()

def get(url):
    err=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"V98-independent-2025-spot-source-only/1.0"})
            with urllib.request.urlopen(req,timeout=40) as r:
                raw=r.read()
            if not raw:raise ValueError("EMPTY_OFFICIAL_ARCHIVE")
            return raw
        except Exception as exc:
            err=exc
            if attempt<2:time.sleep(1+attempt)
    raise RuntimeError("OFFICIAL_SPOT_UNAVAILABLE "+url+" "+repr(err))

def month_calendar(month):
    start=dt.datetime(2025,month,1,tzinfo=dt.timezone.utc)
    end=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc) if month==12 else dt.datetime(2025,month+1,1,tzinfo=dt.timezone.utc)
    return range(int(start.timestamp()*1000),int(end.timestamp()*1000),HOUR)

def normalize_open_time(value):
    if not value.isascii() or not value.isdecimal():raise ValueError("SPOT_TIME_NONDECIMAL")
    t=int(value)
    if t>=10**15:
        if t%1000:raise ValueError("SPOT_MICROSECOND_NON_GRID")
        t//=1000
    if t<1735689600000 or t>=1767225600000:
        raise ValueError("SPOT_OUTSIDE_2025")
    return t

def parse_month(raw,asset,month,expected_name,digest):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        if names!=[expected_name]:raise ValueError("SPOT_ZIP_MEMBER "+asset+" "+str(month))
        with z.open(names[0]) as handle:
            rows=list(csv.reader(io.TextIOWrapper(handle,encoding="utf-8",newline="")))
    expected=set(month_calendar(month))
    found=set();out=[]
    for i,row in enumerate(rows):
        if len(row)!=12:raise ValueError("SPOT_SCHEMA "+asset+" "+str(month)+" "+str(i))
        t=normalize_open_time(row[0])
        if t not in expected or t in found:raise ValueError("SPOT_DUPLICATE_OR_OFF_GRID "+asset+" "+str(t))
        o,h,l,c,q=(float(row[k]) for k in (1,2,3,4,7))
        if not all(math.isfinite(x) for x in (o,h,l,c,q)) or min(o,h,l,c)<=0 or q<0 or l>min(o,c) or h<max(o,c):
            raise ValueError("SPOT_BAD_OHLC "+asset+" "+str(t))
        found.add(t)
        out.append((asset,str(t),row[1],row[2],row[3],row[4],row[7],digest))
    if [int(r[1]) for r in out]!=sorted(found):
        raise ValueError("SPOT_NOT_STRICTLY_SORTED "+asset+" "+str(month))
    missing=sorted(expected-found)
    return out,missing

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    archives=[];all_rows=[];missing_by_asset={a:[] for a in ASSETS}
    for asset in ASSETS:
        for month in MONTHS:
            filename=f"{asset}-1h-2025-{month:02d}.zip"
            url=f"{BASE}/{asset}/1h/{filename}"
            raw=get(url)
            official=get(url+".CHECKSUM").decode("ascii").strip().split()[0].lower()
            if len(official)!=64 or any(c not in "0123456789abcdef" for c in official):
                raise ValueError("SPOT_PROVIDER_CHECKSUM_SCHEMA "+filename)
            digest=sha(raw)
            if digest!=official:raise ValueError("SPOT_PROVIDER_CHECKSUM_CONFLICT "+filename)
            rows,missing=parse_month(raw,asset,month,filename[:-4]+".csv",digest)
            all_rows.extend(rows)
            missing_by_asset[asset].extend(missing)
            archives.append({"archive":filename,"sha256":digest,"rows":len(rows),
                             "expected_rows":len(month_calendar(month)),"missing_hours":len(missing),
                             "bytes":len(raw)})
            print("SPOT_2025_OFFICIAL_MONTH",filename,len(rows),len(missing),flush=True)
    if len(archives)!=48 or any(sum(x["rows"] for x in archives if x["archive"].startswith(a+"-"))+
                                 len(missing_by_asset[a])!=8760 for a in ASSETS):
        raise ValueError("SPOT_2025_COVERAGE_ACCOUNTING")
    output=io.StringIO(newline="")
    writer=csv.writer(output,lineterminator="\n")
    writer.writerow(FIELDS);writer.writerows(all_rows)
    raw=output.getvalue().encode("utf-8")
    canonical=OUT/"v98_spot_2025_observed_only.csv"
    canonical.write_bytes(raw)
    receipt={"decision":"PASS_MASKED_SPOT_2025_SOURCE_ONLY_NOT_ECONOMIC",
             "archive_count":48,"provider_sha256_verified":48,
             "expected_asset_hours":35040,"observed_asset_hours":len(all_rows),
             "missing_asset_hours":sum(map(len,missing_by_asset.values())),
             "per_asset_observed_hours":{a:sum(r[0]==a for r in all_rows) for a in ASSETS},
             "missing_utc":{a:[dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).isoformat()
                               for t in missing_by_asset[a]] for a in ASSETS},
             "archives":archives,"canonical_sha256":sha(raw),
             "2025_exposed_training_only":True,"pnl_computed":False,
             "holdout_accessed":False,"data_2026_accessed":False,
             "external_benchmarks_accessed":False,"trading_authorized":False,
             "complete_grid_2022_2024_source_rejection_still_active":True}
    (OUT/"v98_spot_2025_masked_source_receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print("SPOT_2025_MASKED_SOURCE_ONLY",receipt["observed_asset_hours"],
          receipt["missing_asset_hours"],receipt["canonical_sha256"],flush=True)
    return receipt

if __name__=="__main__":run()
