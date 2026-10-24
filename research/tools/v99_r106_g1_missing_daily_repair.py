"""G1 exact missing required-hour repair from original OKX daily trade ZIPs.

Reads independently verified full-monthly G1 artifacts from Actions 40052064153.
No PnL, no orders, no validation/holdout downloads, no synthetic hours.
"""
from __future__ import annotations
import csv,hashlib,io,json,sys,time,zipfile
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from urllib.request import Request,urlopen
from research.tools.v99_r106_g1_full_train_original_monthly import required_hours,epoch,TRAIN_END

UTC=timezone.utc
HOUR=3600000

def get(url,limit):
    p=urlsplit(url)
    if p.scheme!="https" or p.hostname not in ("www.okx.com","static.okx.com"):
        raise ValueError("UNTRUSTED_ORIGINAL_HOST")
    with urlopen(Request(url,headers={"User-Agent":"V99-G1-exact-155h-daily-source/1.0"}),timeout=95) as r:
        if r.status!=200 or urlsplit(r.geturl()).hostname not in ("www.okx.com","static.okx.com"):
            raise ValueError("UNTRUSTED_REDIRECT")
        data=r.read(limit+1)
    if not data or len(data)>limit:raise ValueError("INVALID_ORIGINAL_DAILY_SIZE")
    return data

def plan(monthly_root,outdir):
    root=Path(monthly_root);out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    source=defaultdict(set); checks=[];seen=set()
    for manifest in sorted(root.glob("batch*/manifest.json")):
        for rec in json.loads(manifest.read_text())["records"]:
            key=(rec["month"],rec["asset"])
            if key in seen:raise ValueError("DUPLICATE_MONTH_ASSET")
            seen.add(key)
            if rec["status"]!="SOURCE_COLLECTED":raise ValueError("ORIGINAL_MONTHLY_SOURCE_NOT_COLLECTED")
            folder=manifest.parent
            for ext in (".hourly.json",".trades.json"):
                p=folder/(rec["asset"]+"_"+rec["month"]+ext)
                if not p.exists():continue
                obj=json.loads(p.read_text())
                for inst,data in obj.items():
                    source[(rec["asset"],inst)].update(x["hour_ms"] for x in data["complete_hours"])
            for inst in rec["targets"]:
                checks.append((rec["asset"],inst,rec["month"],required_hours(inst,rec["month"])))
    gaps=defaultdict(set)
    for asset,inst,month,required in checks:
        for h in required-source[(asset,inst)]:
            if h>=epoch(TRAIN_END):raise ValueError("SEALED_VALIDATION_HOUR")
            venue_day=(datetime.fromtimestamp(h/1000,UTC)+timedelta(hours=8)).strftime("%Y-%m-%d")
            if venue_day>="2023-10-01":raise ValueError("SEALED_VALIDATION_ARCHIVE_CROSSING")
            gaps[(asset,venue_day)].add((inst,h))
    jobs=[]
    for (asset,day),items in sorted(gaps.items()):
        jobs.append({"asset":asset,"venue_day":day,
                     "hours":[{"contract":inst,"hour_ms":h} for inst,h in sorted(items)]})
    count=sum(len(x["hours"]) for x in jobs)
    if count!=155:raise ValueError(f"UNEXPECTED_GAP_COUNT_{count}_EXPECTED_155")
    report={"schema":"G1_INDEPENDENT_EXACT_MISSING_HOURS_PLAN",
            "missing_required_hours":count,"daily_original_archive_jobs":len(jobs),
            "jobs":jobs,"economic_train_executed":False,"roi_computed":False,
            "validation_opened":False,"holdout_opened":False,"orders_enabled":False}
    (out/"plan.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("EXACT G1 GAPS",count,"ORIGINAL VENUE-DAY ARCHIVES",len(jobs),flush=True)

def parse_original_day(raw,asset,day,targets):
    start=datetime.fromisoformat(day).replace(tzinfo=UTC)-timedelta(hours=8)
    lo,hi=epoch(start),epoch(start+timedelta(days=1))
    requested={(x["contract"],x["hour_ms"]) for x in targets}
    grouped=defaultdict(list);ids=defaultdict(dict)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for member in z.infolist():
            if not member.filename.lower().endswith(".csv"):continue
            if member.file_size>2_000_000_000:raise ValueError("OVERSIZED_ORIGINAL_DAILY_MEMBER")
            with z.open(member) as f:
                reader=csv.DictReader(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""))
                if not {"instrument_name","created_time","trade_id","price","size"}<=set(reader.fieldnames or []):
                    raise ValueError("ORIGINAL_DAILY_SCHEMA_MISMATCH")
                for row in reader:
                    inst=row["instrument_name"]
                    if not inst.startswith(asset+"-USDT-"):continue
                    t=int(row["created_time"])
                    if not lo<=t<hi:continue
                    h=(t//HOUR)*HOUR
                    if (inst,h) not in requested:continue
                    trade_id=int(row["trade_id"])
                    px,sz=Decimal(row["price"]),Decimal(row["size"])
                    if not px.is_finite() or px<=0 or not sz.is_finite() or sz<=0:
                        raise ValueError("INVALID_NATIVE_DAILY_TRADE")
                    identity=(t,px,sz)
                    if trade_id in ids[inst]:
                        if ids[inst][trade_id]!=identity:raise ValueError("CONFLICTING_DAILY_TRADE_ID")
                        continue
                    ids[inst][trade_id]=identity
                    grouped[(inst,h)].append((t,trade_id,px,sz))
    bars=[]
    for inst,h in sorted(requested):
        rows=sorted(grouped[(inst,h)],key=lambda x:(x[0],x[1]))
        if rows:
            bars.append({"contract":inst,"hour_ms":h,"original_trades":len(rows),
                         "open":str(rows[0][2]),"high":str(max(x[2] for x in rows)),
                         "low":str(min(x[2] for x in rows)),"close":str(rows[-1][2]),
                         "volume_contracts":str(sum((x[3] for x in rows),Decimal(0)))})
        else:
            bars.append({"contract":inst,"hour_ms":h,"original_trades":0,
                         "status":"NO_ORIGINAL_DAILY_TRADES"})
    return bars

def collect(plan_dir,outdir):
    p=json.loads((Path(plan_dir)/"plan.json").read_text())
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    records=[]
    for i,job in enumerate(p["jobs"]):
        asset,day=job["asset"],job["venue_day"]
        record={"asset":asset,"venue_day":day,"requested_hours":len(job["hours"]),"status":"BLOCKED"}
        try:
            start=epoch(datetime.fromisoformat(day).replace(tzinfo=UTC))
            params={"module":"1","instType":"FUTURES","instFamilyList":asset+"-USDT",
                    "dateAggrType":"daily","begin":str(start),"end":str(start+86400000-1)}
            listing=get("https://www.okx.com/api/v5/public/market-data-history?"+urlencode(params),200000)
            obj=json.loads(listing)
            if obj.get("code")!="0":raise ValueError("OKX_DAILY_LISTING_CODE_"+str(obj.get("code")))
            details=[v for g in obj.get("data",[]) for d in g.get("details",[]) for v in d.get("groupDetails",[])]
            filename=f"{asset}-USDT-futureschain-trades-{day}.zip"
            found=[v for v in details if v.get("filename")==filename]
            if len(found)!=1:raise ValueError("NO_UNIQUE_ORIGINAL_DAILY_ARCHIVE")
            raw=get(found[0]["url"],180_000_000)
            prefix=f"daily_{i:03d}"
            (out/(prefix+".listing.json")).write_bytes(listing)
            (out/(prefix+".zip")).write_bytes(raw)
            bars=parse_original_day(raw,asset,day,job["hours"])
            dest=out/(prefix+".bars.json")
            dest.write_text(json.dumps(bars,sort_keys=True,separators=(",",":"))+"\n")
            record.update({"status":"ORIGINAL_DAILY_REEXECUTABLE","prefix":prefix,
                "listing_sha256":hashlib.sha256(listing).hexdigest(),
                "archive_sha256":hashlib.sha256(raw).hexdigest(),
                "bars_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                "recovered_hours":sum(x.get("original_trades",0)>0 for x in bars)})
        except Exception as exc:
            record["issue"]=type(exc).__name__+":"+str(exc)[:250]
        records.append(record)
        print(json.dumps(record,sort_keys=True),flush=True)
        time.sleep(.15)
    report={"schema":"G1_ORIGINAL_DAILY_MISSING_HOURS_REPAIR","records":records,
            "missing_required_hours":p["missing_required_hours"],
            "economic_train_executed":False,"roi_computed":False,
            "validation_opened":False,"holdout_opened":False,"orders_enabled":False,
            "promotion_authorized":False}
    (out/"daily_repair.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")

def audit(plan_dir,source_dir,outdir):
    p=json.loads((Path(plan_dir)/"plan.json").read_text())
    src=Path(source_dir);o=json.loads((src/"daily_repair.json").read_text())
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    if len(o["records"])!=len(p["jobs"]):raise ValueError("MISSING_ORIGINAL_DAILY_JOB")
    recovered=0;remaining=[];blocked=[]
    for job,rec in zip(p["jobs"],o["records"]):
        if job["asset"]!=rec["asset"] or job["venue_day"]!=rec["venue_day"]:
            raise ValueError("DAILY_SOURCE_IDENTITY_MISMATCH")
        if rec["status"]!="ORIGINAL_DAILY_REEXECUTABLE":
            blocked.append(rec);continue
        prefix=rec["prefix"]
        raw=(src/(prefix+".zip")).read_bytes()
        listing=(src/(prefix+".listing.json")).read_bytes()
        stored=(src/(prefix+".bars.json")).read_bytes()
        for data,digest in ((raw,rec["archive_sha256"]),(listing,rec["listing_sha256"]),
                            (stored,rec["bars_sha256"])):
            if hashlib.sha256(data).hexdigest()!=digest:raise ValueError("ORIGINAL_DAILY_SHA_MISMATCH")
        expected=parse_original_day(raw,rec["asset"],rec["venue_day"],job["hours"])
        if expected!=json.loads(stored):raise ValueError("INDEPENDENT_DAILY_ORACLE_MISMATCH")
        for row in expected:
            if row["original_trades"]:recovered+=1
            else:remaining.append({"asset":rec["asset"],"day":rec["venue_day"],
                                   "contract":row["contract"],"hour_ms":row["hour_ms"]})
    result={"schema":"G1_DAILY_FIRSTPARTY_INDEPENDENT_SOURCE_VERDICT",
            "initial_missing_hours":p["missing_required_hours"],"recovered_original_trade_hours":recovered,
            "confirmed_no_trade_hours":len(remaining),"blocked_original_archives":len(blocked),
            "remaining_hours":remaining,"blocked_archives":blocked,
            "status":"SOURCE_REPAIRED_NOT_ECONOMICS" if recovered==155 and not blocked else "DATA_ONLY_HOLD",
            "economic_train_executed":False,"roi_computed":False,
            "validation_opened":False,"holdout_opened":False,"orders_enabled":False,
            "promotion_authorized":False}
    (out/"daily_audit.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("remaining_hours","blocked_archives")},sort_keys=True))

if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("plan MONTHLY OUT | collect PLAN OUT | audit PLAN SOURCE OUT")
    if sys.argv[1]=="plan":plan(sys.argv[2],sys.argv[3])
    elif sys.argv[1]=="collect":collect(sys.argv[2],sys.argv[3])
    else:raise SystemExit("use: plan MONTHLY OUT | collect PLAN OUT | audit PLAN SOURCE OUT")
