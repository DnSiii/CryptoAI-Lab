#!/usr/bin/env python3
"""V98-only: 2025 exposed-training OI native vendor source probe, no PnL."""
import datetime as dt
import json
from v98_oi_full_history_source_v2_20261027 import read_day
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
DAYS=(dt.date(2025,1,15),dt.date(2025,7,15))
def run():
    out=[]
    for day in DAYS:
        for asset in ASSETS:
            record={"asset":asset,"date":day.isoformat()}
            try:
                info,rows=read_day(asset,day)
                if not info["passed"] or len(rows)!=24 or any(row[1]!=asset for row in rows):
                    raise ValueError("V98_OI_2025_PROBE_CAUSAL_HOUR_COUNT")
                record.update({"status":"VENDOR_SHA_AND_FULL_DAY_PASS",
                               "zip_sha256":info["sha256"],"hourly_rows":len(rows),
                               "source_rows_reordered":info["source_rows_reordered"]})
            except Exception as exc:
                record.update({"status":"BLOCKED","first_fault":type(exc).__name__+": "+str(exc)[:220]})
            out.append(record)
            print("V98_OI_2025_SAMPLE",json.dumps(record,sort_keys=True),flush=True)
    passed=sum(x["status"]=="VENDOR_SHA_AND_FULL_DAY_PASS" for x in out)
    result={"decision":"PASS_NATIVE_2025_OI_SAMPLE_SOURCE_ONLY_NOT_PNL" if passed==8 else
            "BLOCK_NATIVE_2025_OI_SAMPLE_NO_FULL_ACQUISITION",
            "assets":list(ASSETS),"days":[x.isoformat() for x in DAYS],
            "samples_expected":8,"samples_passed":passed,"results":out,
            "2025_exposed_training_only":True,"2026_plus_accessed":False,
            "holdout_accessed":False,"pnl_computed":False,"paper_or_live_authorized":False}
    with open("v98_oi_2025_sample_source_receipt.json","w") as f:
        json.dump(result,f,sort_keys=True,indent=2);f.write("\n")
    print("V98_OI_2025_SOURCE_PROBE",result["decision"],passed,"/8",flush=True)
    return passed==8
if __name__=="__main__":
    raise SystemExit(0 if run() else 2)
