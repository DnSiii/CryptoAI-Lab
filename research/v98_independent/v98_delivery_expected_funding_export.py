#!/usr/bin/env python3
"""V98 expected native funding slots from authenticated 2022-25 exposed training.
No 2026+, holdout, external benchmark, system PnL, or trading authorization.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from v98_2025_full_training_source_bridge import load
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
START_MS=1669852800000
HOUR_MS=3600000
EXPECTED_HOURS=27048
EXPECTED_EVENTS=13524

def export(old_root,old_envelope,new_root,corrected_root,output_dir):
    d=load(old_root,old_envelope,new_root,corrected_root)
    if len(d["time"])!=EXPECTED_HOURS or int(np.sum(d["event"]))!=EXPECTED_EVENTS:
        raise ValueError("V98_EXPORT_SOURCE_CHRONOLOGY")
    if d["holdout_accessed"] or not d["training_only"] or not d["year_2025_exposed"]:
        raise ValueError("V98_EXPORT_TRAINING_FIREWALL")
    times=np.asarray(d["time"].asi8//10**6,dtype=np.int64)
    if not np.array_equal(times,START_MS+np.arange(EXPECTED_HOURS)*HOUR_MS):
        raise ValueError("V98_EXPORT_TIMESTAMP_GAP")
    if np.any(d["event"] & ~np.isfinite(d["rate"])) or np.any(np.abs(d["rate"][d["event"]])>1):
        raise ValueError("V98_EXPORT_INVALID_FUNDING_RATE")
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    p=out/"v98_expected_native_funding_2022_2025.csv";counts={}
    with p.open("w",newline="") as f:
        writer=csv.writer(f,lineterminator="\n")
        writer.writerow(("asset","funding_time_ms","funding_rate"))
        for j,asset in enumerate(ASSETS):
            ii=np.flatnonzero(d["event"][:,j])
            if len(ii)!=EXPECTED_EVENTS//len(ASSETS):
                raise ValueError("V98_EXPORT_ASSET_COUNT_"+asset)
            counts[asset]=len(ii)
            for i in ii:
                writer.writerow((asset,int(times[i]),format(float(d["rate"][i,j]),".12g")))
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    receipt={"decision":"PASS_EXPECTED_NATIVE_FUNDING_EXPORT_TRAINING_ONLY_NOT_MARK_ATTESTATION",
             "source":"V98 authenticated 2022-2025 Clean-4 bridge with SHA-pinned source artifacts",
             "expected_csv_sha256":digest,"event_count":EXPECTED_EVENTS,"per_asset":counts,
             "first_training_month":"2022-12","last_training_month":"2025-12",
             "2025_exposed_training_only":True,"2026_accessed":False,
             "holdout_accessed":False,"exact_mark_attested":False,
             "account_fees_attested":False,"pnl_computed":False,
             "external_benchmarks_accessed":False,"paper_live_authorized":False}
    (out/"v98_expected_native_funding_receipt.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("old-root","old-envelope","new-root","corrected-root","output-dir"):
        p.add_argument("--"+name,required=True)
    a=vars(p.parse_args())
    print(json.dumps(export(a["old_root"],a["old_envelope"],a["new_root"],
                            a["corrected_root"],a["output_dir"]),sort_keys=True))
