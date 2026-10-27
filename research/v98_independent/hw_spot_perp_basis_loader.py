#!/usr/bin/env python3
"""HW SHA-pinned HQ spot calendar source; full-hour mask, no interpolation."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from phase1260_aj_authenticated_source_digest import HOURS,START

ROOT=Path(__file__).resolve().parent/"hw_spot_source"
CANONICAL_SHA="7bfa31bcb94865e6dada10c3b7a0848b93bae432b01fd4014c0c6f6d5621f681"
MANIFEST_SHA="02f1eef3fb3bd5a8a4f7ab7e60379474f091c961f9be98217b8b9792f75ef3a9"
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")

def load_spot():
    p=ROOT/"hq_spot_calendar_masked.csv"
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CANONICAL_SHA:
        raise ValueError("HW_SPOT_CANONICAL_PIN")
    receipt=json.loads((ROOT/"hq_masked_source_receipt.json").read_text())
    if (receipt.get("decision")!="PASS_HQ_MASKED_SOURCE_ONLY_NOT_ECONOMIC" or
        receipt.get("canonical_sha256")!=CANONICAL_SHA or
        receipt.get("publisher_manifest_sha256")!=MANIFEST_SHA or
        receipt.get("eligible_full_hour_asset_hours")!=73144 or
        receipt.get("masked_asset_hours")!=4 or
        receipt.get("publisher_early_close_partial_asset_hours")!=4 or
        receipt.get("validation_2025_read") is not False):
        raise ValueError("HW_SPOT_PROVENANCE")
    d=pd.read_csv(p)
    if (len(d)!=HOURS*4 or list(d.columns)!=
        ["asset","open_time_ms","observed","full_hour","open","high","low","close","quote_volume"]):
        raise ValueError("HW_SPOT_SCHEMA")
    assets=d["asset"].to_numpy().reshape(4,HOURS)
    if not np.all(assets==np.asarray(ASSETS)[:,None]):
        raise ValueError("HW_SPOT_ASSET_ORDER")
    times=d["open_time_ms"].to_numpy(dtype=np.int64).reshape(4,HOURS)
    expected=(START.value//1000000)+np.arange(HOURS,dtype=np.int64)*3600000
    if not np.array_equal(times,np.tile(expected,(4,1))):
        raise ValueError("HW_SPOT_UTC_CALENDAR")
    observed=d["observed"].to_numpy(dtype=np.int8).reshape(4,HOURS)
    full=d["full_hour"].to_numpy(dtype=np.int8).reshape(4,HOURS)
    if (not np.isin(observed,(0,1)).all() or
        not np.isin(full,(0,1)).all() or np.any(full>observed) or
        int(observed.sum())!=73148 or int(full.sum())!=73144):
        raise ValueError("HW_SPOT_ELIGIBILITY")
    valid=(full==1).T
    close=d["close"].to_numpy(dtype=float).reshape(4,HOURS).T
    if (not np.isfinite(close[valid]).all() or np.any(close[valid]<=0) or
        not np.isnan(close[~valid]).all()):
        raise ValueError("HW_SPOT_MISSINGNESS_NOT_MASKED")
    partial=int((pd.Timestamp("2023-03-24T12:00:00Z")-START).total_seconds()//3600)
    missing=partial+1
    if (not np.all(observed[:,partial]==1) or
        not np.all(full[:,partial]==0) or
        not np.all(observed[:,missing]==0) or
        not np.all(full[:,missing]==0) or
        int(np.count_nonzero(~valid))!=8):
        raise ValueError("HW_SPOT_KNOWN_GAP")
    return close,valid

if __name__=="__main__":
    spot,mask=load_spot()
    print("HW_SPOT_MASK_PIN_PASS",spot.shape,int(mask.sum()))
