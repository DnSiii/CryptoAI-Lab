#!/usr/bin/env python3
"""Phase176 deterministic OKX borrowing-rate archive manifest.

DATA/INTEGRITY ONLY: this tool never computes alpha/PnL and refuses rows outside
frozen TRAIN [2021-12-01, 2024-01-18). It is deliberately schema-tolerant only
for discovery: ambiguous timestamp/currency columns fail closed.

Important integrity semantics:
- duplicate identity is (timestamp, currency) when currency is present, not timestamp alone;
- monthly/sharded files are allowed: TRAIN month coverage is evaluated across the whole
  supplied archive set, not independently inside every CSV member;
- cross-member duplicate identities are detected globally;
- no alpha, return, price, PnL, or holdout-period row is consumed.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, pathlib, zipfile
from datetime import datetime, timezone

TRAIN_START = datetime(2021, 12, 1, tzinfo=timezone.utc)
TRAIN_END = datetime(2024, 1, 18, tzinfo=timezone.utc)
TS_NAMES = {"timestamp","ts","time","datetime","date","created_at","createdat"}
CCY_NAMES = {"currency","ccy","coin","asset","symbol"}

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def parse_ts(v):
    s=str(v).strip()
    if s.isdigit():
        x=int(s); x=x/1000 if x>10_000_000_000 else x
        return datetime.fromtimestamp(x,tz=timezone.utc)
    z=s.replace("Z","+00:00")
    d=datetime.fromisoformat(z)
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)

def months(a,b):
    out=[]; y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        out.append(f"{y:04d}-{m:02d}"); m+=1
        if m==13: y,m=y+1,1
    return out

def inspect_csv_bytes(name, raw):
    text=raw.decode("utf-8-sig")
    rows=csv.DictReader(text.splitlines())
    fields=rows.fieldnames or []
    norm={f.lower().replace(" ","").replace("-","_"):f for f in fields}
    ts_hits=[orig for k,orig in norm.items() if k in TS_NAMES]
    ccy_hits=[orig for k,orig in norm.items() if k in CCY_NAMES]
    if len(ts_hits)!=1: raise ValueError(f"{name}: ambiguous timestamp columns {ts_hits}")
    if len(ccy_hits)>1: raise ValueError(f"{name}: ambiguous currency columns {ccy_hits}")
    tscol=ts_hits[0]; ccycol=ccy_hits[0] if len(ccy_hits)==1 else None
    seen=set(); dup=0; mono=True; prev=None; lo=None; hi=None; n=0; ccy=set(); mon=set(); outside=0; identities=[]
    for r in rows:
        d=parse_ts(r[tscol]); n+=1
        if not (TRAIN_START <= d < TRAIN_END): outside+=1
        cv=(r.get(ccycol) or "").strip() if ccycol else ""
        key=(d.isoformat(),cv) if ccycol else (d.isoformat(),)
        if key in seen: dup+=1
        seen.add(key); identities.append(key)
        if prev is not None and d < prev: mono=False
        prev=d; lo=d if lo is None or d<lo else lo; hi=d if hi is None or d>hi else hi
        mon.add(d.strftime("%Y-%m"))
        if cv: ccy.add(cv)
    return {"member":name,"schema":fields,"timestamp_column":tscol,"currency_column":ccycol,
            "currencies":sorted(ccy),"rows":n,"min_timestamp":lo.isoformat() if lo else None,
            "max_timestamp":hi.isoformat() if hi else None,"duplicate_identities_within_member":dup,
            "monotonic":mono,"outside_frozen_train_rows":outside,"observed_train_months":sorted(mon),
            "_identities":identities}

def inspect(path):
    p=pathlib.Path(path); members=[]
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            for n in sorted(z.namelist()):
                if n.lower().endswith(".csv"): members.append(inspect_csv_bytes(n,z.read(n)))
    elif p.suffix.lower()==".csv": members=[inspect_csv_bytes(p.name,p.read_bytes())]
    else: raise ValueError(f"unsupported archive {p}")
    return {"file":p.name,"bytes":p.stat().st_size,"sha256":sha256(p),"members":members}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("files",nargs="+"); ap.add_argument("--out",default="phase176_borrow_manifest.json")
    a=ap.parse_args(); result={"phase":176,"scope":"DATA_INTEGRITY_ONLY","train_start":TRAIN_START.isoformat(),"train_end_exclusive":TRAIN_END.isoformat(),"archives":[]}
    for f in sorted(a.files): result["archives"].append(inspect(f))
    members=[m for x in result["archives"] for m in x["members"]]
    required=set(months(TRAIN_START, datetime(2024,1,1,tzinfo=timezone.utc)))
    observed=set().union(*(set(m["observed_train_months"]) for m in members)) if members else set()
    global_seen=set(); cross_dup=0
    for m in members:
        for key in m.pop("_identities"):
            if key in global_seen: cross_dup+=1
            global_seen.add(key)
    result["coverage"]={"required_train_months":sorted(required),"observed_train_months":sorted(observed),"missing_train_months":sorted(required-observed)}
    result["cross_member_duplicate_identities"]=cross_dup
    bad_member=[m for m in members if m["outside_frozen_train_rows"] or m["duplicate_identities_within_member"] or not m["monotonic"]]
    result["archive_gate_pass"]=bool(members) and not bad_member and not (required-observed) and cross_dup==0
    pathlib.Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"out":a.out,"archive_gate_pass":result["archive_gate_pass"],"problem_members":len(bad_member),"missing_train_months":len(required-observed),"cross_member_duplicate_identities":cross_dup},sort_keys=True))
    raise SystemExit(0 if result["archive_gate_pass"] else 2)
if __name__=="__main__": main()
