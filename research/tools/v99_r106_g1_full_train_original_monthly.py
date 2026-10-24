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

def decode_trade_hourly(archive,targets,month):
    """Independent first-party trade-tape hourly bars; no fabricated no-trade hour."""
    a,b=month_bounds(month)
    # OKX monthly trade archives are cut at UTC+8, not UTC midnight.
    # Retain the adjacent eight-hour boundary solely for original cross-month stitching.
    lo,hi=epoch(a)-8*HOUR,min(epoch(b)+8*HOUR,epoch(TRAIN_END))
    grouped=defaultdict(lambda:defaultdict(list))
    ids=defaultdict(dict)
    exact_duplicate_rows=defaultdict(int)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for member in z.infolist():
            if not member.filename.lower().endswith(".csv"):continue
            if member.file_size>3_000_000_000:raise ValueError("OVERSIZED_MONTHLY_TRADE_MEMBER")
            with z.open(member) as stream:
                reader=csv.DictReader(io.TextIOWrapper(stream,encoding="utf-8-sig",newline=""))
                if not {"instrument_name","created_time","trade_id","price","size"}<=set(reader.fieldnames or []):
                    raise ValueError("TRADE_SCHEMA_MISMATCH")
                for row in reader:
                    inst=row["instrument_name"]
                    if inst not in targets:continue
                    t=int(row["created_time"])
                    if not lo<=t<hi:continue  # UTC+8 archive boundary; never feed post-TRAIN records
                    trade_id=int(row["trade_id"])
                    price,size=Decimal(row["price"]),Decimal(row["size"])
                    if not price.is_finite() or price<=0 or not size.is_finite() or size<=0:
                        raise ValueError("BAD_NATIVE_TRADE_PRICE_OR_SIZE")
                    identity=(t,price,size)
                    if trade_id in ids[inst]:
                        if ids[inst][trade_id]!=identity:
                            raise ValueError("CONFLICTING_ORIGINAL_TRADE_ID")
                        exact_duplicate_rows[inst]+=1
                        continue  # exact repeated source row, not an additional trade
                    ids[inst][trade_id]=identity
                    grouped[inst][(t//HOUR)*HOUR].append((t,trade_id,price,size))
    out={}
    for inst in targets:
        bars=[]
        for h,rows in sorted(grouped[inst].items()):
            rows.sort(key=lambda x:(x[0],x[1]))
            bars.append({"hour_ms":h,"open":str(rows[0][2]),
                         "high":str(max(x[2] for x in rows)),
                         "low":str(min(x[2] for x in rows)),
                         "close":str(rows[-1][2]),
                         "volume_contracts":str(sum((x[3] for x in rows),Decimal(0))),
                         "native_trades":len(rows)})
        out[inst]={"original_trades":len(ids[inst]),"exact_duplicate_rows":exact_duplicate_rows[inst],"complete_hours":bars}
    return out

def required_hours(inst,month):
    expiry=datetime.strptime(inst[-6:],"%y%m%d").replace(tzinfo=UTC)
    a,b=month_bounds(month)
    eligible_mondays=[]
    day=TRAIN_START
    while day<min(TRAIN_END,expiry):
        if day.weekday()==0:
            candidates=[e for e in EXPIRIES if 30 <= (datetime.fromisoformat(e).replace(tzinfo=UTC)-day).total_seconds()/86400 <=110]
            if candidates and min(candidates).replace("-","")[2:]==inst[-6:]:
                eligible_mondays.append(day)
        day+=timedelta(days=1)
    if not eligible_mondays:raise ValueError("NONPREREG_CONTRACT_SELECTED")
    start=max(a,min(eligible_mondays)-timedelta(hours=1))
    end=min(b,expiry,TRAIN_END)
    return set(range(epoch(start),epoch(end),HOUR))

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
                # Original monthly candle archives are mislabeled for many early
                # TRAIN months. Recover only missing required hours from *original*
                # monthly trade tapes, never relabel an unrelated contract.
                missing=sum(len(required_hours(inst,month)-
                                {x["hour_ms"] for x in v["complete_hours"]})
                            for inst,v in data.items())
                if missing:
                    trade_params=dict(params,module="1")
                    trade_listing=get("https://www.okx.com/api/v5/public/market-data-history?"+
                                      urlencode(trade_params),250000)
                    trade_obj=json.loads(trade_listing)
                    if trade_obj.get("code")!="0":raise ValueError("TRADE_LISTING_CODE_"+str(trade_obj.get("code")))
                    trade_entries=[v for g in trade_obj.get("data",[])
                                   for d in g.get("details",[]) for v in d.get("groupDetails",[])]
                    trade_name=f"{asset}-USDT-futureschain-trades-{month}.zip"
                    found=[x for x in trade_entries if x.get("filename")==trade_name]
                    if len(found)!=1:raise ValueError("NO_UNIQUE_ORIGINAL_MONTHLY_TRADES")
                    trade_zip=get(found[0]["url"],350_000_000)
                    (root/trade_name).write_bytes(trade_zip)
                    (root/(prefix+".trade_listing.json")).write_bytes(trade_listing)
                    trade_bars=decode_trade_hourly(trade_zip,targets,month)
                    trade_path=root/(prefix+".trades.json")
                    trade_path.write_text(json.dumps(trade_bars,sort_keys=True,separators=(",",":"))+"\n")
                    rec.update({"trade_zip_filename":trade_name,
                                "trade_zip_sha256":hashlib.sha256(trade_zip).hexdigest(),
                                "trade_listing_sha256":hashlib.sha256(trade_listing).hexdigest(),
                                "trade_hourly_sha256":hashlib.sha256(trade_path.read_bytes()).hexdigest(),
                                "trade_targets_summary":{k:{"trades":v["original_trades"],
                                    "hours":len(v["complete_hours"])} for k,v in trade_bars.items()}})
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
    global_hours=defaultdict(set)
    coverage_checks=[]
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
            recovered={}
            if "trade_zip_filename" in rec:
                trade_raw=(folder/rec["trade_zip_filename"]).read_bytes()
                if hashlib.sha256(trade_raw).hexdigest()!=rec["trade_zip_sha256"]:
                    raise ValueError("ORIGINAL_TRADE_ZIP_SHA_MISMATCH")
                trade_listing=(folder/(rec["asset"]+"_"+rec["month"]+".trade_listing.json")).read_bytes()
                if hashlib.sha256(trade_listing).hexdigest()!=rec["trade_listing_sha256"]:
                    raise ValueError("ORIGINAL_TRADE_LISTING_SHA_MISMATCH")
                trade_path=folder/(rec["asset"]+"_"+rec["month"]+".trades.json")
                if hashlib.sha256(trade_path.read_bytes()).hexdigest()!=rec["trade_hourly_sha256"]:
                    raise ValueError("TRADE_DERIVED_SHA_MISMATCH")
                recovered=json.loads(trade_path.read_text())
                if decode_trade_hourly(trade_raw,rec["targets"],rec["month"])!=recovered:
                    raise ValueError("INDEPENDENT_TRADE_REEXECUTION_MISMATCH")
                totals["original_trade_zips"]=totals.get("original_trade_zips",0)+1
                totals["original_trades"]=totals.get("original_trades",0)+sum(v["original_trades"] for v in recovered.values())
            totals["original_zips"]+=1
            for inst,data in stored.items():
                totals["original_minutes"]+=data["original_minutes"]
                totals["complete_hours"]+=len(data["complete_hours"])
                expiry=datetime.strptime(inst[-6:],"%y%m%d").replace(tzinfo=UTC)
                a,b=month_bounds(rec["month"])
                # Original weekly decision must have prior completed hour. Include
                # the entire subsequent carry until contractual expiry date.
                eligible_mondays=[]
                day=TRAIN_START
                while day<min(TRAIN_END,expiry):
                    if day.weekday()==0:
                        candidates=[e for e in EXPIRIES if 30 <= (datetime.fromisoformat(e).replace(tzinfo=UTC)-day).total_seconds()/86400 <=110]
                        if candidates and min(candidates).replace("-","")[2:]==inst[-6:]:
                            eligible_mondays.append(day)
                    day+=timedelta(days=1)
                if not eligible_mondays:raise ValueError("NONPREREG_CONTRACT_SELECTED")
                first=min(eligible_mondays)-timedelta(hours=1)
                start=max(a,first);end=min(b,expiry,TRAIN_END)
                expected_hours=set(range(epoch(start),epoch(end),HOUR))
                observed_hours={x["hour_ms"] for x in data["complete_hours"]}
                observed_hours.update(x["hour_ms"] for x in recovered.get(inst,{}).get("complete_hours",[]))
                global_hours[(rec["asset"],inst)].update(observed_hours)
                coverage_checks.append((rec["month"],rec["asset"],inst,expected_hours))
    # Independently reconcile UTC+8 monthly trade archive boundaries across
    # adjacent source months; never interpolate or forward-fill a missing hour.
    for month,asset,inst,expected_hours in coverage_checks:
        missing=expected_hours-global_hours[(asset,inst)]
        totals["required_carry_hours"]=totals.get("required_carry_hours",0)+len(expected_hours)
        totals["missing_carry_hours"]=totals.get("missing_carry_hours",0)+len(missing)
        if missing:
            issues.append({"month":month,"asset":asset,"contract":inst,
                           "issue":"MISSING_ORIGINAL_CARRY_HOURS","missing_hours":len(missing),
                           "first_missing_hour_ms":min(missing)})
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
