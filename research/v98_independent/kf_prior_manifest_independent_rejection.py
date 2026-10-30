#!/usr/bin/env python3
"""Reproduce KF terminal 2023-24 source rejection from earlier independent native publisher manifest; NO PnL."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"kf_prior_source"/"v98_oi_full_history_source_v2_report_20261027.json"
OUT=ROOT/"kf_prior_manifest_independent_rejection.json"
PIN="da1629050845995d16102670b9067354236b00b7f1d6ae15ee0b044d1e2aa933"
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")

def main():
    raw=SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError("KF_ORIGINAL_PRIOR_SOURCE_REPORT_SHA_MISMATCH")
    d=json.loads(raw)
    if d.get("files_expected")!=3048 or d.get("files_verified_complete")!=3011 or d.get("files_quarantined")!=37:
        raise ValueError("KF_PRIOR_MANIFEST_EXPECTATIONS_MISMATCH")
    records=[x for x in d["manifest"] if "2023-01-01"<=x["date"]<="2024-12-31"]
    if len(records)!=2924:raise ValueError("KF_2023_2024_UNIVERSE_WRONG")
    bad_native=sum(not x["passed"] for x in records)
    unordered=sum(bool(x.get("source_rows_reordered",False)) for x in records)
    bad=sum(not x["passed"] or bool(x.get("source_rows_reordered",False)) for x in records)
    eligible=len(records)-bad
    gaps={}
    for asset in ASSETS:
        arr=sorted((x for x in records if x["asset"]==asset),key=lambda x:x["date"])
        if len(arr)!=731 or len({x["date"] for x in arr})!=731:raise ValueError("KF_ASSET_DATE_COVERAGE_WRONG")
        longest=cur=0
        for x in arr:
            cur=cur+1 if not x["passed"] or x.get("source_rows_reordered",False) else 0
            longest=max(longest,cur)
        gaps[asset]=longest
    eligible_gate=eligible>=2895 and max(gaps.values())<=1
    if eligible_gate:raise ValueError("KF_PRIOR_MANIFEST_UNEXPECTED_GATE_PASS")
    report={"candidate":"KF","source_only":True,"historical_pnl_computed":False,
            "source_run_id":40477513000,"source_artifact_id":12720854329,
            "source_report_sha256":PIN,"original_asset_days":2924,
            "invalid_native_days":bad_native,"unordered_original_days":unordered,
            "union_disqualified_days":bad,"eligible_days_upper_bound":eligible,
            "required_eligible_days":2895,"max_consecutive_disqualified_by_asset":gaps,
            "preregistered_gate_pass":False,"decision":"KF_TERMINAL_SOURCE_REJECTION_NO_PNL"}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("KF_INDEPENDENT_PRIOR_MANIFEST",report["decision"],"eligible",eligible,
          "native_invalid",bad_native,"unordered",unordered,"union",bad,"gaps",gaps,flush=True)

if __name__=="__main__":main()
