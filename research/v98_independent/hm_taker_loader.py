#!/usr/bin/env python3
"""HM pinned authenticated executed-taker-flow loader, strictly Dec-2022..Dec-2024."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from phase1260_aj_authenticated_source_digest import HOURS,START
ROOT=Path(__file__).resolve().parent
SHA="a8ee661e4b5db6e12ea20b4ee1070c24e5b8cb095a316af4dc3a89869421eaf7"
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
def load_taker(official_quote):
    p=ROOT/"native_taker_flow_clean4_2022_2024.csv"
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:
        raise ValueError("HM_TAKER_ORIGINAL_PIN_MISMATCH")
    d=pd.read_csv(p)
    if len(d)!=HOURS*4 or list(d.columns)!=[
        "open_time","asset","taker_buy_base","taker_buy_quote",
        "total_base","total_quote","taker_buy_quote_share"]:
        raise ValueError("HM_TAKER_SCHEMA")
    names=d["asset"].to_numpy().reshape(HOURS,4)
    if not np.all(names==np.array(ASSETS)[None,:]):
        raise ValueError("HM_TAKER_ASSET_ORDER")
    timestamps=pd.to_datetime(d["open_time"],utc=True)
    expected=pd.date_range(START,periods=HOURS,freq="h",tz="UTC")
    if not np.array_equal(timestamps.to_numpy().reshape(HOURS,4)[:,0],expected.to_numpy()) or not np.all(
        timestamps.to_numpy().reshape(HOURS,4)==expected.to_numpy()[:,None]):
        raise ValueError("HM_TAKER_UTC_CALENDAR")
    buy=d["taker_buy_quote"].to_numpy(dtype=float).reshape(HOURS,4)
    quote=d["total_quote"].to_numpy(dtype=float).reshape(HOURS,4)
    if (not np.isfinite(buy).all() or not np.isfinite(quote).all()
        or np.any(buy<0) or np.any(quote<0) or np.any(buy>quote+1e-5)
        or not np.allclose(quote,official_quote,rtol=1e-9,atol=1e-7)):
        raise ValueError("HM_TAKER_CANONICAL_RECONCILIATION")
    return buy,quote
if __name__=="__main__":
    print("HM_TAKER_LOADER_REQUIRES_OFFICIAL_SOURCE")
