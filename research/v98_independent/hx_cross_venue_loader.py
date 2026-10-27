#!/usr/bin/env python3
"""HX authenticated cross-venue taker flow loader; no 2025, no PnL, no imputation."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from phase1260_aj_authenticated_source_digest import HOURS,START
from hm_taker_loader import load_taker as load_native_taker

ROOT=Path(__file__).resolve().parent
SPOT=ROOT/"hx_spot_flow_training"
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
MANIFEST="02f1eef3fb3bd5a8a4f7ab7e60379474f091c961f9be98217b8b9792f75ef3a9"

def load_spot():
    receipt=json.loads((SPOT/"hx_spot_flow_receipt.json").read_text())
    raw=(SPOT/"hx_spot_taker_quote.csv").read_bytes()
    if (receipt.get("decision")!="PASS_HX_SPOT_TAKER_SOURCE_ONLY" or
        receipt.get("csv_sha256")!=hashlib.sha256(raw).hexdigest() or
        receipt.get("publisher_manifest_sha256")!=MANIFEST or
        receipt.get("archives")!=100 or
        receipt.get("calendar_asset_hours")!=HOURS*4 or
        receipt.get("eligible_asset_hours")!=73144 or
        receipt.get("masked_asset_hours")!=8 or
        receipt.get("validation_2025_read") is not False):
        raise ValueError("HX_SPOT_PROVENANCE")
    d=pd.read_csv(SPOT/"hx_spot_taker_quote.csv")
    if len(d)!=HOURS*4 or list(d.columns)!=[
            "open_time_ms","asset","taker_buy_quote","spot_quote","full_hour"]:
        raise ValueError("HX_SPOT_SCHEMA")
    if not np.all(d["asset"].to_numpy().reshape(HOURS,4)==np.asarray(ASSETS)[None,:]):
        raise ValueError("HX_SPOT_ASSET_ORDER")
    times=d["open_time_ms"].to_numpy(dtype=np.int64).reshape(HOURS,4)
    expected=(START.value//1000000)+np.arange(HOURS,dtype=np.int64)*3600000
    if not np.array_equal(times,np.tile(expected[:,None],(1,4))):
        raise ValueError("HX_SPOT_UTC_CALENDAR")
    full=d["full_hour"].to_numpy(dtype=np.int8).reshape(HOURS,4)
    valid=full==1
    if not np.isin(full,(0,1)).all() or int(valid.sum())!=73144:
        raise ValueError("HX_SPOT_VALIDITY")
    gap=int((pd.Timestamp("2023-03-24T12:00:00Z")-START).total_seconds()//3600)
    if (not np.all(~valid[gap:gap+2]) or np.count_nonzero(~valid)!=8):
        raise ValueError("HX_SPOT_PARTIAL_MISSING_MASK")
    buy=d["taker_buy_quote"].to_numpy(dtype=float).reshape(HOURS,4)
    quote=d["spot_quote"].to_numpy(dtype=float).reshape(HOURS,4)
    if (not np.isfinite(buy[valid]).all() or
        not np.isfinite(quote[valid]).all() or
        np.any(quote[valid]<=0) or np.any(buy[valid]<0) or
        np.any(buy[valid]>quote[valid]+1e-6*np.maximum(1,quote[valid])) or
        not np.isnan(buy[~valid]).all() or not np.isnan(quote[~valid]).all()):
        raise ValueError("HX_SPOT_TAKER_CONSERVATION")
    return buy,quote,valid

def load_cross_venue(official_quote):
    sb,sq,mask=load_spot()
    pb,pq=load_native_taker(official_quote)
    if np.any(pq<0) or np.any(pb<0) or np.any(pb>pq+1e-5) or np.any((pq==0)&(pb!=0)):
        raise ValueError("HX_PERP_TAKER_CONSERVATION")
    return sb,sq,mask,pb,pq
if __name__=="__main__":
    print("HX_REQUIRES_PINNED_OFFICIAL_INPUT")
