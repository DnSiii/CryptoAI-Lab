#!/usr/bin/env python3
"""Independent artifact-only V98 OI source integrity audit; never downloads or runs PnL."""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,math,re
from collections import Counter,defaultdict
from pathlib import Path
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=dt.date(2022,12,1);END=dt.date(2024,12,31)
def run(root):
    root=Path(root)
    reports=list(root.rglob("v98_oi_full_history_source_report_20261027.json"))
    csvs=list(root.rglob("v98_oi_full_history_verified_hourly_20261027.csv"))
    if len(reports)!=1 or len(csvs)!=1:raise ValueError("OI_AUDIT_ARTIFACT_INVENTORY")
    report=json.loads(reports[0].read_text())
    assert report["source_only"] and report["historical_training_only"]
    assert report["holdout_2025_read"] is False and report["pnl_computed"] is False
    assert report["external_benchmarks_used"] is False and report["trading_authorized"] is False
    assert report["date_start"]==START.isoformat() and report["date_end"]==END.isoformat()
    expected={(asset,(START+dt.timedelta(days=i)).isoformat()) for asset in ASSETS
              for i in range((END-START).days+1)}
    manifest=report["manifest"]
    index={(x["asset"],x["date"]):x for x in manifest}
    if len(manifest)!=len(expected) or set(index)!=expected:
        raise ValueError("OI_AUDIT_SOURCE_MANIFEST_COMPLETENESS")
    if report["files_expected"]!=len(expected):raise ValueError("OI_AUDIT_EXPECTED_COUNT")
    good={key for key,x in index.items() if x["passed"]}
    bad=set(index)-good
    if len(good)!=report["files_verified_complete"] or len(bad)!=report["files_quarantined"]:
        raise ValueError("OI_AUDIT_SOURCE_COUNTS")
    if any(not re.fullmatch(r"[a-f0-9]{64}",index[k].get("sha256","")) for k in good):
        raise ValueError("OI_AUDIT_VENDOR_SHA")
    if hashlib.sha256(csvs[0].read_bytes()).hexdigest()!=report["hourly_csv_sha256"]:
        raise ValueError("OI_AUDIT_CSV_SHA")
    counts=Counter();seen=set();previous=None
    with csvs[0].open(newline="") as f:
        for row in csv.DictReader(f):
            ts=dt.datetime.fromisoformat(row["bar_open_utc"])
            if ts.tzinfo is None or ts.utcoffset()!=dt.timedelta(0) or ts.minute!=0 or ts.second!=0:
                raise ValueError("OI_AUDIT_NONCAUSAL_HOURLY_STAMP")
            key=(row["asset"],ts.date().isoformat())
            if key not in good:raise ValueError("OI_AUDIT_QUARANTINED_DAY_LEAK")
            if row["source_zip_sha256"]!=index[key]["sha256"]:
                raise ValueError("OI_AUDIT_SOURCE_SHA_PER_HOUR")
            if not (math.isfinite(float(row["oi_contracts"])) and float(row["oi_contracts"])>0):
                raise ValueError("OI_AUDIT_INVALID_OI")
            for col in ("oi_value_usdt","taker_ratio"):
                if row[col] and not math.isfinite(float(row[col])):
                    raise ValueError("OI_AUDIT_INVALID_OPTIONAL_FIELD")
            unique=(row["asset"],row["bar_open_utc"])
            if unique in seen:raise ValueError("OI_AUDIT_DUPLICATE_HOUR")
            seen.add(unique);counts[key]+=1
            sortkey=(row["bar_open_utc"],row["asset"])
            if previous is not None and sortkey<=previous:
                raise ValueError("OI_AUDIT_NONMONOTONIC_HOURLY_CSV")
            previous=sortkey
    if any(counts[key]!=24 for key in good) or any(counts[key]!=0 for key in bad):
        raise ValueError("OI_AUDIT_HOURLY_DAY_COMPLETENESS")
    if len(seen)!=report["verified_hourly_rows"] or len(seen)!=24*len(good):
        raise ValueError("OI_AUDIT_HOURLY_TOTAL")
    return {"decision":"PASS_OI_ARTIFACT_INTEGRITY_WITH_GAPS_NOT_TRAINING_APPROVAL" if bad else
            "PASS_OI_FULL_ARTIFACT_INTEGRITY_SOURCE_ONLY",
            "files_expected":len(expected),"verified_days":len(good),
            "quarantined_days":len(bad),"verified_hourly_rows":len(seen),
            "first_quarantined":[index[k] for k in sorted(bad)[:30]],
            "csv_sha256":report["hourly_csv_sha256"],"no_2025_read":True,
            "pnl_computed":False,"trading_authorized":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    out=run(a.root)
    Path(a.output).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("V98_OI_INDEPENDENT",out["decision"],
          out["verified_days"],"/",out["files_expected"],
          "quarantined",out["quarantined_days"],
          "hours",out["verified_hourly_rows"],
          "first",out["first_quarantined"][:5],flush=True)
