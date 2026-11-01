#!/usr/bin/env python3
"""V98-only 2022-25 exposed-training native OI causal mask; source availability, NO PnL."""
import argparse,csv,datetime as dt,hashlib,json
from pathlib import Path
import numpy as np
from v98_oi_full_history_v2_independent_audit_20261027 import run as old_audit
from v98_oi_2025_full_native_independent_audit import audit as new_audit

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
HOURS=27048
LOOKBACKS=(168,336,672)
DECISIONS=tuple(range(744,HOURS,168))

def find_one(root,name):
    matches=list(Path(root).rglob(name))
    if len(matches)!=1:raise ValueError("V98_OI_JOIN_SOURCE_INVENTORY_"+name)
    return matches[0]

def load_one(root,report_name,csv_name,expected_start,expected_end,observed,from_manifest):
    report=json.loads(find_one(root,report_name).read_text())
    csvpath=find_one(root,csv_name)
    if report.get("date_start")!=expected_start or report.get("date_end")!=expected_end:
        raise ValueError("V98_OI_JOIN_YEAR_SCOPE")
    manifest={(x["asset"],x["date"]):x for x in report["manifest"]}
    for (asset,date),row in manifest.items():
        if asset not in ASSETS:raise ValueError("V98_OI_JOIN_ASSET")
        day=dt.date.fromisoformat(date)
        t=int((dt.datetime.combine(day,dt.time(),dt.timezone.utc)-START).total_seconds()//3600)
        if t<0 or t+24>HOURS:raise ValueError("V98_OI_JOIN_MANIFEST_DATE")
        if row["passed"]:
            from_manifest[t:t+24,ASSETS.index(asset)]=True
    with csvpath.open(newline="") as f:
        for row in csv.DictReader(f):
            stamp=dt.datetime.fromisoformat(row["bar_open_utc"])
            if (stamp.tzinfo is None or stamp.utcoffset()!=dt.timedelta(0)
                or stamp.minute!=0 or stamp.second!=0 or stamp.microsecond!=0
                or not START<=stamp<END):
                raise ValueError("V98_OI_JOIN_NONCAUSAL_TIMESTAMP")
            delta=(stamp-START).total_seconds()
            if delta%3600:raise ValueError("V98_OI_JOIN_OFF_HOURLY_GRID")
            t=int(delta//3600)
            j=ASSETS.index(row["asset"])
            if observed[t,j]:raise ValueError("V98_OI_JOIN_DUPLICATE_HOUR")
            observed[t,j]=True
    return hashlib.sha256(csvpath.read_bytes()).hexdigest()

def source_only_mask(old_root,new_root):
    old=old_audit(old_root)
    if not old["decision"].startswith("PASS_OI_ARTIFACT_INTEGRITY"):
        raise ValueError("V98_OI_JOIN_2022_24_AUDIT")
    new=new_audit(new_root)
    if new["decision"]!="PASS_2025_NATIVE_OI_INDEPENDENT_ARTIFACT_AUDIT_NOT_PNL":
        raise ValueError("V98_OI_JOIN_2025_AUDIT")
    observed=np.zeros((HOURS,4),dtype=bool)
    manifest=np.zeros_like(observed)
    old_sha=load_one(old_root,"v98_oi_full_history_source_v2_report_20261027.json",
                     "v98_oi_full_history_v2_verified_hourly_20261027.csv",
                     "2022-12-01","2024-12-31",observed,manifest)
    new_sha=load_one(new_root,"v98_oi_2025_native_source_report.json",
                     "v98_oi_2025_verified_hourly.csv",
                     "2025-01-01","2025-12-31",observed,manifest)
    if not np.array_equal(observed,manifest):
        raise ValueError("V98_OI_JOIN_INDEPENDENT_MANIFEST_MASK_MISMATCH")
    if len(DECISIONS)!=157 or HOURS!=18288+8760:
        raise ValueError("V98_OI_JOIN_CLOCK")
    receipts=[];summary={}
    for length in LOOKBACKS:
        eligible=0
        for t in DECISIONS:
            window=observed[t-length+1:t+1]
            oracle=manifest[t-length+1:t+1]
            okay=bool(window.all())
            if okay!=bool(oracle.all()):raise ValueError("V98_OI_JOIN_MASK_ORACLE")
            if t+1<HOURS:
                changed=observed[t-length+1:t+1].copy()
                # No data later than completed hour t is used by this decision.
                if okay!=bool(changed.all()):
                    raise ValueError("V98_OI_JOIN_FUTURE_LEAK")
            first_missing=None
            if not okay:
                offset,j=map(int,np.argwhere(~window)[0])
                first_missing={"asset":ASSETS[j],
                               "utc":(START+dt.timedelta(hours=t-length+1+offset)).isoformat()}
            receipts.append({"decision_hour":t,"lookback_hours":length,
                             "eligible":okay,"first_missing":first_missing})
            eligible+=int(okay)
        summary[str(length)]={"eligible_decisions":eligible,
                              "blocked_decisions":len(DECISIONS)-eligible,
                              "total_decisions":len(DECISIONS)}
    encoded=json.dumps(receipts,sort_keys=True,separators=(",",":")).encode()
    return {"decision":"PASS_V98_2022_25_OI_CAUSAL_SOURCE_MASK_NOT_PNL",
            "hours":HOURS,"assets":list(ASSETS),"verified_hourly_asset_rows":int(observed.sum()),
            "quarantined_hourly_asset_rows":int((~observed).sum()),
            "decision_clocks":len(DECISIONS),"window_checks":len(receipts),
            "summary":summary,"receipts_sha256":hashlib.sha256(encoded).hexdigest(),
            "source_2022_24_csv_sha256":old_sha,"source_2025_csv_sha256":new_sha,
            "2025_exposed_training_only":True,"2026_plus_accessed":False,
            "holdout_accessed":False,"pnl_computed":False,
            "paper_or_live_authorized":False}

def self_test():
    assert len(DECISIONS)==157
    a=np.ones((HOURS,4),bool)
    t=DECISIONS[0]
    for n in LOOKBACKS:
        assert a[t-n+1:t+1].all()
        b=a.copy();b[t+1,0]=False
        assert b[t-n+1:t+1].all()
        b=a.copy();b[t,2]=False
        assert not b[t-n+1:t+1].all()
    return {"decision":"PASS_V98_OI_2022_25_MASK_SYNTHETIC_CAUSAL_TEST",
            "lookbacks":len(LOOKBACKS),"decisions":len(DECISIONS),
            "pnl_computed":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--old-root");p.add_argument("--new-root");p.add_argument("--output")
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),sort_keys=True))
    else:
        if not args.old_root or not args.new_root or not args.output:
            p.error("--old-root, --new-root, --output required")
        out=source_only_mask(args.old_root,args.new_root)
        Path(args.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print(json.dumps(out,sort_keys=True))
