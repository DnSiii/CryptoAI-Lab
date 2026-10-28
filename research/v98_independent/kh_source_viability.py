#!/usr/bin/env python3
"""KH source-only pre-economic gate and original temporal-flow feature materialization."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from kh_temporal_taker_sources import build_intrabar,bundle,static_check,WARMUP,CLOCK
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"kh_source_viability.json"
FEATURE=ROOT/"kh_intrabar_features.npz"
RECEIPT=ROOT/"kh_intrabar_features_receipt.json"
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    assert static_check()
    frames,manifest=load_official()
    early,late,lr,valid_hour,origin=build_intrabar()
    o,h,l,c,q,r,e,ml,mh=frames
    targets,updates,regimes,valid,budgets=bundle(o,h,l,c,r,e,q,early,late,lr,valid_hour)
    if len(c)!=HOURS or HOURS!=18288:raise ValueError("KH_TRAINING_HOURS")
    all_epochs=np.arange(WARMUP,HOURS,CLOCK)
    counts={};fail=[]
    for year,lo,hi in (("2023",744,9504),("2024",9504,HOURS)):
        epochs=all_epochs[(all_epochs>=lo)&(all_epochs<hi)]
        counts[year]={}
        for i,name in enumerate(("Opportunity","Relative_Value","Stress_Recovery")):
            diff=np.abs(targets[epochs,1]-targets[epochs,i+2]).sum(axis=1)
            count=int(np.sum(diff>.025))
            counts[year][name]=count
            if count<8:fail.append("KH_INSUFFICIENT_"+year+"_"+name)
    if np.any(np.abs(targets[all_epochs]).sum(axis=2)>1.+1e-10):
        fail.append("KH_GROSS")
    if np.any((np.abs(targets[all_epochs,1]-targets[all_epochs,0]).sum(axis=1)>1e-10)&(~valid[all_epochs])):
        fail.append("KH_SOURCE_QUARANTINE")
    digest=sha(b"".join(np.asarray(z,dtype="<f8").tobytes() for z in (early,late,lr))+
               valid_hour.astype("uint8").tobytes())
    np.savez_compressed(FEATURE,early=early,late=late,late_return=lr,valid=valid_hour)
    info={"feature_sha256":digest,"npz_sha256":sha(FEATURE.read_bytes()),
          "original_receipts":origin,"canonical_manifest_sha256":sha(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()),
          "source_only":True,"validation_2025_read":False}
    RECEIPT.write_text(json.dumps(info,indent=2,sort_keys=True,allow_nan=False)+"\n")
    report={"architecture":"KH","historical_training_only":True,
        "validation_2025_read":False,"future_holdout_read":False,
        "external_benchmarks_used":False,"economic_pnl_computed":False,
        "trading_authorized":False,"native_funding_events":int(e.sum()),
        "source":"full_100_month_official_1m_temporal_taker_and_pinned_1h_funding",
        "source_manifest_sha256":info["canonical_manifest_sha256"],
        "feature_sha256":digest,"epoch_count":int(updates.sum()),
        "invalid_source_epochs":int(np.sum(~valid[all_epochs])),
        "valid_hourly_asset_observations":int(valid_hour.sum()),
        "material_funded_epochs_by_year":counts,"violations":fail,
        "decision":"PASS_KH_SOURCE_ONLY_NEEDS_INDEPENDENT_FEATURE_AUDIT" if not fail else "REJECT_KH_SOURCE_ONLY_NO_PNL"}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print("KH_SOURCE",report["decision"],"counts",counts,
          "valid_hours",int(valid_hour.sum()),"violations",fail,flush=True)
    return report
if __name__=="__main__":
    x=main()
    raise SystemExit(0 if not x["violations"] else 2)
