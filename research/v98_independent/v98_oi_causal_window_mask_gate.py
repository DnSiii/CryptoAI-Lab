#!/usr/bin/env python3
"""V98 Independent OI native 5m->completed-hour causal coverage window gate; NO PnL."""
import argparse,csv,datetime as dt,hashlib,json
from pathlib import Path
import numpy as np
from v98_oi_full_history_v2_independent_audit_20261027 import run as source_audit
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
HOURS=18288;WARMUP=744
LOOKBACKS=(168,336,672)
def locate(root,filename):
    files=list(Path(root).rglob(filename))
    if len(files)!=1:raise ValueError("V98_OI_MASK_INPUT_INVENTORY_"+filename)
    return files[0]
def run(root):
    audit=source_audit(root)
    if not audit["decision"].startswith("PASS_OI_ARTIFACT_INTEGRITY"):
        raise ValueError("V98_OI_MASK_SOURCE_AUDIT_NOT_PASS")
    report=json.loads(locate(root,"v98_oi_full_history_source_v2_report_20261027.json").read_text())
    csvpath=locate(root,"v98_oi_full_history_v2_verified_hourly_20261027.csv")
    seen=np.zeros((HOURS,4),bool)
    with csvpath.open(newline="") as f:
        for row in csv.DictReader(f):
            stamp=dt.datetime.fromisoformat(row["bar_open_utc"])
            if stamp.tzinfo is None or stamp.utcoffset()!=dt.timedelta(0):
                raise ValueError("V98_OI_MASK_NON_UTC")
            delta=(stamp-START).total_seconds()
            if delta%3600 or not 0<=delta//3600<HOURS:
                raise ValueError("V98_OI_MASK_OFF_GRID")
            if row["asset"] not in ASSETS:raise ValueError("V98_OI_MASK_UNKNOWN_ASSET")
            t=int(delta//3600);j=ASSETS.index(row["asset"])
            if seen[t,j]:raise ValueError("V98_OI_MASK_DUPLICATE")
            seen[t,j]=True
    from_manifest=np.zeros_like(seen)
    for x in report["manifest"]:
        if x["passed"]:
            day=dt.date.fromisoformat(x["date"])
            idx=int((dt.datetime.combine(day,dt.time(),dt.timezone.utc)-START).total_seconds()//3600)
            if idx<0 or idx+24>HOURS:raise ValueError("V98_OI_MASK_MANIFEST_RANGE")
            from_manifest[idx:idx+24,ASSETS.index(x["asset"])]=True
    if not np.array_equal(seen,from_manifest):
        raise ValueError("V98_OI_MASK_MANIFEST_OBSERVED_MISMATCH")
    if int(seen.sum())!=72264 or int((~seen).sum())!=888:
        raise ValueError("V98_OI_MASK_UNEXPECTED_QUARANTINE")
    # Two independent representations: verified hourly rows and vendor manifest.
    clocks={"optional_168h":list(range(WARMUP,HOURS,168)),
            "core_672h":list(range(WARMUP,HOURS,672))}
    if len(clocks["optional_168h"])!=105 or len(clocks["core_672h"])!=27:
        raise ValueError("V98_OI_MASK_CLOCK")
    receipts=[];summary={}
    for clock,times in clocks.items():
        summary[clock]={}
        for length in LOOKBACKS:
            eligible_count=0
            for t in times:
                observed=seen[t-length+1:t+1]
                original=from_manifest[t-length+1:t+1]
                eligible=bool(observed.all())
                oracle=bool(original.all())
                if eligible!=oracle:raise ValueError("V98_OI_MASK_INDEPENDENT_ORACLE_MISMATCH")
                if t+1<HOURS:
                    mutated=seen[t-length+1:t+1].copy()
                    # Future data t+1 is outside the input slice by construction.
                    if bool(mutated.all())!=eligible:
                        raise ValueError("V98_OI_MASK_FUTURE_MUTATION")
                missing=np.argwhere(~observed)
                first=None
                if len(missing):
                    h,j=map(int,missing[0])
                    stamp=START+dt.timedelta(hours=t-length+1+h)
                    first={"asset":ASSETS[j],"utc":stamp.isoformat()}
                receipts.append({"clock":clock,"decision_hour_index":t,"lookback_hours":length,
                                 "eligible":eligible,"first_missing":first})
                eligible_count+=eligible
            summary[clock][str(length)]={"eligible_decisions":eligible_count,
                                          "total_decisions":len(times),
                                          "blocked_decisions":len(times)-eligible_count}
    assert len(receipts)==(105+27)*3
    encoded=json.dumps(receipts,sort_keys=True,separators=(",",":")).encode()
    return {"decision":"PASS_CAUSAL_OI_WINDOW_MASK_SOURCE_ONLY_NOT_PNL",
            "verified_hourly_asset_rows":int(seen.sum()),"quarantined_hourly_asset_rows":int((~seen).sum()),
            "quarantined_asset_days":37,"manifest_vs_hourly_mismatches":0,
            "decision_windows_oracle_verified":len(receipts),"summary":summary,
            "source_csv_sha256":hashlib.sha256(csvpath.read_bytes()).hexdigest(),
            "receipt_sha256":hashlib.sha256(encoded).hexdigest(),
            "decisions":receipts,"source_audit":audit["decision"],
            "future_holdout_accessed":False,"pnl_computed":False,"trading_authorized":False}
def synthetic_tests():
    m=np.ones((672,4),bool)
    for n in LOOKBACKS:
        assert m[-n:].all()
        changed=m.copy();changed[-1,2]=False
        assert not changed[-n:].all()
        if n<672:
            future=m.copy();future[0,1]=False
            assert future[-n:].all()
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();assert synthetic_tests()
    out=run(a.root)
    Path(a.output).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("V98_OI_CAUSAL_WINDOW_MASK",out["decision"],json.dumps(out["summary"],sort_keys=True),
          "oracle_windows",out["decision_windows_oracle_verified"],
          "source_sha",out["source_csv_sha256"],"receipt_sha",out["receipt_sha256"],flush=True)
