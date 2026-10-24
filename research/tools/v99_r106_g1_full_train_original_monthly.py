"""G1 full preregistered TRAIN monthly original OKX FUTURES candles, fail closed.

This is SOURCE acquisition, not a return simulation or permission to open validation.
The original 2022-03 archive is known to contain impossible 2025/26 labels:
never remap instruments, fabricate absent hourly bars, or infer fills.
"""
from __future__ import annotations
import csv, hashlib, io, json, sys, time, zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

UTC=timezone.utc
TRAIN_START=datetime(2021,12,9,tzinfo=UTC)
TRAIN_END=datetime(2023,10,1,tzinfo=UTC)
EXPIRIES=("2022-03-25","2022-06-24","2022-09-30","2022-12-30",
          "2023-03-31","2023-06-30","2023-09-29")
MONTHS=[f"{y}-{m:02d}" for y in (2021,2022,2023) for m in range(1,13)
        if "2021-12"<=f"{y}-{m:02d}"<"2023-10"]
ASSETS=("BTC","ETH")
MAX_ZIP=150_000_000
HOUR=3_600_000

def epoch(d):
    return int(d.timestamp()*1000)

def get(url, limit):
    if urlsplit(url).scheme!="https" or urlsplit(url).hostname not in ("www.okx.com","static.okx.com"):
        raise ValueError("UNTRUSTED_SOURCE_HOST")
    with urlopen(Request(url,headers={"User-Agent":"V99-G1-preregistered-full-train/1.0"}),timeout=100) as r:
        if r.status!=200 or urlsplit(r.geturl()).hostname not in ("www.okx.com","static.okx.com"):
            raise ValueError("UNTRUSTED_REDIRECT")
        raw=r.read(limit+1)
    if not raw or len(raw)>limit: raise ValueError("SOURCE_EMPTY_OR_OVERSIZED")
    return raw

def month_bounds(month):
    y,m=map(int,month.split("-"))
    a=datetime(y,m,1,tzinfo=UTC)
    b=datetime(y+1,1,1,tzinfo=UTC) if m==12 else datetime(y,m+1,1,tzinfo=UTC)
    return a,b

def expected_contracts(month,asset):
    a,b=month_bounds(month)
    # Contracts opened in earlier months MUST remain in the tape until delivery.
    # Without this, the source collector would silently omit the settlement month.
    day=TRAIN_START
    found=set()
    while day<b and day<TRAIN_END:
        if day.weekday()==0:
            eligible=[e for e in EXPIRIES if 30 <= (datetime.fromisoformat(e).replace(tzinfo=UTC)-day).total_seconds()/86400 <=110]
            if eligible:
                selected=min(eligible)
                expiry=datetime.fromisoformat(selected).replace(tzinfo=UTC)
                if expiry>=a:
                    found.add(asset+"-USDT-"+selected.replace("-","")[2:])
        day+=timedelta(days=1)
    return sorted(found)

def decode_hourly(archive,asset,targets,month):
    a,b=month_bounds(month)
    lo,hi=epoch(a),min(epoch(b),epoch(TRAIN_END))
    grouped=defaultdict(lambda:defaultdict(list))
    source_rows=defaultdict(int)
    bad=0
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for member in z.infolist():
            if not member.filename.lower().endswith(".csv"):continue
            if member.file_size>1_000_000_000:raise ValueError("OVERSIZED_CSV_MEMBER")
            with z.open(member) as f:
                reader=csv.DictReader(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""))
                required={"instrument_name","open","high","low","close","open_time","confirm"}
                if not required<=set(reader.fieldnames or []):raise ValueError("CANDLE_SCHEMA_MISMATCH")
                for row in reader:
                    inst=row["instrument_name"]
                    if inst not in targets:continue
                    t=int(row["open_time"])
                    if not lo<=t<hi or t%60000:raise ValueError("FUTURE_OR_MISALIGNED_CANDLE")
                    if row["confirm"]!="1":bad+=1;continue
                    p=tuple(Decimal(row[k]) for k in ("open","high","low","close","vol"))
                    if not all(x.is_finite() and x>0 for x in p[:4]) or not p[4].is_finite() or p[4]<0:raise ValueError("BAD_NATIVE_PRICE_OR_VOLUME")
                    if p[1]<max(p[0],p[3]) or p[2]>min(p[0],p[3]):raise ValueError("BAD_OHLC")
                    grouped[inst][(t//HOUR)*HOUR].append((t,*p))
                    source_rows[inst]+=1
    result={}
    for inst in targets:
        bars=[]
        for h,minutes in sorted(grouped[inst].items()):
            minutes.sort()
            if len(minutes)!=60 or len({r[0] for r in minutes})!=60:
                continue  # never fabricate an incomplete original hour
            if minutes[0][0]!=h or minutes[-1][0]!=h+59*60000:continue
            bars.append({"hour_ms":h,"open":str(minutes[0][1]),"high":str(max(x[2] for x in minutes)),
                         "low":str(min(x[3] for x in minutes)),"close":str(minutes[-1][4]),
                         "native_minutes":60,"volume_contracts":str(sum((x[5] for x in minutes),Decimal(0)))})
        result[inst]={"original_minutes":source_rows[inst],"complete_hours":bars,
                      "incomplete_or_missing_minutes":source_rows[inst]-60*len(bars)}
    return result,bad

def collect(batch,outdir):
    root=Path(outdir);root.mkdir(parents=True,exist_ok=True)
    records=[]
    for idx,month in enumerate(MONTHS):
        if idx%5!=batch:continue
        a,b=month_bounds(month)
        if epoch(b)>epoch(TRAIN_END):raise ValueError("SEALED_VALIDATION_WINDOW")
        for asset in ASSETS:
            targets=expected_contracts(month,asset)
            rec={"month":month,"asset":asset,"targets":targets,"status":"NOT_COLLECTED","issue":None}
            if not targets:
                rec["status"]="NO_PREREG_WEEKLY_ELIGIBILITY"
                records.append(rec);continue
            try:
                params={"module":"2","instType":"FUTURES","instFamilyList":asset+"-USDT",
                        "dateAggrType":"monthly","begin":str(epoch(a)),"end":str(epoch(b)-1)}
                listing=get("https://www.okx.com/api/v5/public/market-data-history?"+urlencode(params),250000)
                obj=json.loads(listing)
                if obj.get("code")!="0":raise ValueError("OKX_LISTING_CODE_"+str(obj.get("code")))
                entries=[v for g in obj.get("data",[]) for d in g.get("details",[])
                         for v in d.get("groupDetails",[])]
                filename=f"{asset}-USDT-futureschain-candlesticks-{month}.zip"
                matches=[x for x in entries if x.get("filename")==filename]
                if len(matches)!=1:raise ValueError("NO_UNIQUE_MONTHLY_ZIP")
                archive=get(matches[0]["url"],MAX_ZIP)
                prefix=f"{asset}_{month}"
                (root/(prefix+".listing.json")).write_bytes(listing)
                (root/filename).write_bytes(archive)
                data,unconfirmed=decode_hourly(archive,asset,targets,month)
                dest=root/(prefix+".hourly.json")
                dest.write_text(json.dumps(data,sort_keys=True,separators=(",",":"))+"\n")
                rec.update({"status":"SOURCE_COLLECTED","zip_filename":filename,
                            "zip_url":matches[0]["url"],
                            "zip_sha256":hashlib.sha256(archive).hexdigest(),
                            "listing_sha256":hashlib.sha256(listing).hexdigest(),
                            "hourly_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                            "unconfirmed_target_minutes":unconfirmed,
                            "targets_summary":{k:{"minutes":v["original_minutes"],
                                                   "complete_hours":len(v["complete_hours"])}
                                               for k,v in data.items()}})
            except Exception as exc:
                rec.update({"status":"BLOCKED_SOURCE","issue":type(exc).__name__+":"+str(exc)[:240]})
            records.append(rec)
            print(json.dumps(rec,sort_keys=True),flush=True)
            time.sleep(.15)
    (root/"manifest.json").write_text(json.dumps({"schema":"G1_ORIGINAL_FULL_TRAIN_MONTHLY_SOURCE_V1",
        "batch":batch,"records":records,"economic_train_executed":False,"roi_computed":False,
        "validation_opened":False,"holdout_opened":False,"orders_enabled":False,
        "promotion_authorized":False},sort_keys=True,indent=2)+"\n")

def audit(rootdir,outdir):
    root=Path(rootdir);out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    seen=set();issues=[];totals={"original_minutes":0,"complete_hours":0,"original_zips":0}
    for manifest in sorted(root.glob("batch*/manifest.json")):
        obj=json.loads(manifest.read_text())
        assert obj["economic_train_executed"] is False and obj["validation_opened"] is False
        for rec in obj["records"]:
            key=(rec["month"],rec["asset"])
            if key in seen:raise ValueError("DUPLICATE_MONTH_ASSET")
            seen.add(key)
            if rec["status"]=="NO_PREREG_WEEKLY_ELIGIBILITY":continue
            if rec["status"]!="SOURCE_COLLECTED":
                issues.append({"month":rec["month"],"asset":rec["asset"],"issue":rec.get("issue")});continue
            folder=manifest.parent; raw=(folder/rec["zip_filename"]).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=rec["zip_sha256"]:raise ValueError("SOURCE_SHA_MISMATCH")
            listing=(folder/(rec["asset"]+"_"+rec["month"]+".listing.json")).read_bytes()
            if hashlib.sha256(listing).hexdigest()!=rec["listing_sha256"]:raise ValueError("LISTING_SHA_MISMATCH")
            p=folder/(rec["asset"]+"_"+rec["month"]+".hourly.json")
            if hashlib.sha256(p.read_bytes()).hexdigest()!=rec["hourly_sha256"]:raise ValueError("DERIVED_SHA_MISMATCH")
            independent,bad=decode_hourly(raw,rec["asset"],rec["targets"],rec["month"])
            stored=json.loads(p.read_text())
            if independent!=stored:raise ValueError("INDEPENDENT_REEXECUTION_MISMATCH")
            totals["original_zips"]+=1
            for inst,data in stored.items():
                totals["original_minutes"]+=data["original_minutes"]
                totals["complete_hours"]+=len(data["complete_hours"])
                if not data["complete_hours"]:
                    issues.append({"month":rec["month"],"asset":rec["asset"],
                                   "contract":inst,"issue":"NO_ORIGINAL_COMPLETE_HOURS"})
    expected={(m,a) for m in MONTHS for a in ASSETS}
    if seen!=expected:
        issues.append({"issue":"MISSING_BATCH_MONTHS","count":len(expected-seen)})
    report={"schema":"G1_FULL_TRAIN_ORIGINAL_MONTHLY_SOURCE_INDEPENDENT_AUDIT_V1",
        "status":"DATA_ONLY_HOLD" if issues else "SOURCE_PRESENT_NOT_ECONOMICS",
        "months":len(MONTHS),"asset_months_seen":len(seen),"totals":totals,
        "issues":issues,"full_train_economic_ready":False,
        "historical_native_terms_verified":False,"economic_train_executed":False,
        "roi_computed":False,"validation_opened":False,"holdout_opened":False,
        "orders_enabled":False,"promotion_authorized":False}
    (out/"audit.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True))
    if seen!=expected:raise ValueError("INCOMPLETE_BATCH_UPLOADS")

if __name__=="__main__":
    if len(sys.argv)<2:raise SystemExit("collect BATCH OUT | audit ROOT OUT")
    if sys.argv[1]=="collect" and len(sys.argv)==4:collect(int(sys.argv[2]),sys.argv[3])
    elif sys.argv[1]=="audit" and len(sys.argv)==4:audit(sys.argv[2],sys.argv[3])
    else:raise SystemExit("collect BATCH OUT | audit ROOT OUT")
