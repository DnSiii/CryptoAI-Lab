#!/usr/bin/env python3
"""V98 ONLY: authenticated 2025 exposed-training native OI extension; source only, no PnL.
Run full acquisition only after the independent 8-file sample source probe passes.
Quarantines incomplete days, never fills; does not access 2026+ or future holdout.
"""
import argparse,concurrent.futures,csv,datetime as dt,hashlib,json
from pathlib import Path
from v98_oi_full_history_source_v2_20261027 import read_day

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START=dt.date(2025,1,1)
END=dt.date(2025,12,31)
FIELDS=("bar_open_utc","asset","oi_contracts","oi_value_usdt","taker_ratio","source_zip_sha256")
DAYS=(END-START).days+1

def inventory():
    assert DAYS==365 and START.year==2025 and END.year==2025
    return [(asset,START+dt.timedelta(days=i)) for asset in ASSETS for i in range(DAYS)]

def acquire(pair):
    asset,day=pair
    try:
        meta,rows=read_day(asset,day)
        if not meta["passed"] or len(rows)!=24:
            raise ValueError("V98_OI_2025_INCOMPLETE_NATIVE_DAY")
        return meta,rows
    except Exception as exc:
        return {"asset":asset,"date":day.isoformat(),"passed":False,
                "first_fault":type(exc).__name__+": "+str(exc)[:220]},[]

def run(output_dir):
    root=Path(output_dir)
    root.mkdir(parents=True,exist_ok=True)
    if any(root.iterdir()):
        raise ValueError("V98_OI_2025_OUTPUT_DIRECTORY_NOT_EMPTY")
    entries=[];hours=[]
    pairs=inventory()
    assert len(pairs)==1460
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for index,result in enumerate(pool.map(acquire,pairs),1):
            meta,rows=result
            entries.append(meta);hours.extend(rows)
            if index%100==0:
                print("V98_OI_2025_NATIVE_PROGRESS",index,"/",len(pairs),
                      "verified",sum(x["passed"] for x in entries),flush=True)
    entries.sort(key=lambda x:(x["asset"],x["date"]))
    hours.sort(key=lambda x:(x[0],x[1]))
    csv_path=root/"v98_oi_2025_verified_hourly.csv"
    with csv_path.open("w",newline="") as handle:
        writer=csv.writer(handle);writer.writerow(FIELDS);writer.writerows(hours)
    passed=sum(bool(x["passed"]) for x in entries)
    report={"decision":"PASS_2025_NATIVE_OI_SOURCE_NO_GAPS_NOT_PNL" if passed==1460 else
            "QUARANTINE_2025_NATIVE_OI_GAPS_NOT_PNL",
            "source_only":True,"2025_exposed_training_only":True,
            "2026_plus_accessed":False,"holdout_accessed":False,
            "external_benchmarks_used":False,"pnl_computed":False,
            "paper_or_live_authorized":False,"date_start":START.isoformat(),
            "date_end":END.isoformat(),"assets":list(ASSETS),
            "files_expected":len(pairs),"files_verified_complete":passed,
            "files_quarantined":len(pairs)-passed,
            "verified_hourly_rows":len(hours),"expected_hourly_rows":len(pairs)*24,
            "hourly_csv_sha256":hashlib.sha256(csv_path.read_bytes()).hexdigest(),
            "first_quarantined":[x for x in entries if not x["passed"]][:30],
            "manifest":entries}
    (root/"v98_oi_2025_native_source_report.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("V98_OI_2025_FULL_SOURCE",report["decision"],passed,"/",len(pairs),
          "hours",len(hours),"first_faults",report["first_quarantined"][:5],flush=True)
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",default="v98-oi-2025-native-source")
    parser.add_argument("--inventory-only",action="store_true")
    args=parser.parse_args()
    if args.inventory_only:
        print(json.dumps({"expected_asset_days":len(inventory()),"start":str(START),
                          "end":str(END),"2026_plus_accessed":False,"pnl_computed":False}))
    else:
        report=run(args.output_dir)
        raise SystemExit(0 if report["files_quarantined"]==0 else 2)
