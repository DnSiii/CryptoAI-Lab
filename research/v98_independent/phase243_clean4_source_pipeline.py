#!/usr/bin/env python3
"""V98 Phase243 Clean-4 authenticated source pipeline.

DATA_ONLY. Quarantines XRP by preregistered source-integrity policy and verifies
BTC/ETH/BNB/SOL only. No alpha, PnL, validation, holdout, V16 or V99.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import pandas as pd

from phase243_source_acquisition import acquire_one
from phase243_binance_archive_ingest import MONTHS, _parse_month
from phase243_funding_source_gate import audit_bytes

CLEAN4=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
EXPECTED_ROWS=27048
EXPECTED_ARCHIVES=148
EXPECTED_ASSET_HOURS=108192
START=pd.Timestamp("2022-12-01T00:00:00Z")
CUT=pd.Timestamp("2026-01-01T00:00:00Z")

def sha(b: bytes)->str:
    return hashlib.sha256(b).hexdigest()

def canonicalize(root: Path, dest: Path):
    dest.mkdir(parents=True,exist_ok=True)
    assets={}
    fingerprints={}
    total=0
    for asset in CLEAN4:
        pieces=[]; months={}
        for month in MONTHS:
            p=root/"klines"/asset/"1h"/f"{asset}-1h-{month}.zip"
            df,ev=_parse_month(p,asset,month)
            pieces.append(df); months[month]=ev
        joined=pd.concat(pieces,ignore_index=True)
        ix=pd.DatetimeIndex(joined.open_time)
        if (len(joined)!=EXPECTED_ROWS or ix.has_duplicates or
            not ix.is_monotonic_increasing or ix[0]!=START or
            ix[-1]!=CUT-pd.Timedelta(hours=1) or
            not (ix[1:]-ix[:-1]==pd.Timedelta(hours=1)).all()):
            raise ValueError(f"{asset}: Clean-4 canonical continuity failure")
        raw=joined.to_csv(index=False,float_format="%.12g").encode()
        (dest/f"{asset}_1h.csv").write_bytes(raw)
        fp=sha(joined[["open","close","volume","quote_volume"]].to_numpy(dtype="<f8").tobytes())
        if fp in fingerprints.values():
            raise ValueError(f"{asset}: suspicious identical cross-asset panel")
        fingerprints[asset]=fp
        assets[asset]={
            "rows":len(joined),"first":ix[0].isoformat(),"last":ix[-1].isoformat(),
            "canonical_sha256":sha(raw),"cross_asset_panel_fingerprint":fp,
            "months":months,
        }
        total+=len(joined)
    if total!=EXPECTED_ASSET_HOURS:
        raise ValueError("Clean-4 asset-hour count mismatch")
    return assets

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive-root",type=Path,default=Path("research/v98_independent/phase243_clean4_archives"))
    p.add_argument("--canonical-root",type=Path,default=Path("research/v98_independent/phase243_clean4_canonical"))
    p.add_argument("--funding-root",type=Path,default=Path("research/v98_independent/data/phase206_funding"))
    p.add_argument("--out",type=Path,default=Path("research/v98_independent/phase243_clean4_source_manifest.json"))
    p.add_argument("--attempts",type=int,default=3)
    a=p.parse_args()
    report={
        "engine":"V98 Independent","phase":243,"mode":"CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA",
        "universe":list(CLEAN4),"quarantined":["XRPUSDT"],
        "quarantine_reason":"source-integrity conflict before system PnL",
        "holdout_accessed":False,"alpha_or_pnl_computed":False,
        "v16_used":False,"v99_used":False,"promotion_eligible":False,
        "expected_archives":EXPECTED_ARCHIVES,"expected_asset_hours":EXPECTED_ASSET_HOURS,
    }
    acq=[]
    for asset in CLEAN4:
        for month in MONTHS:
            acq.append(acquire_one(a.archive_root,asset,month,attempts=a.attempts))
    if len(acq)!=EXPECTED_ARCHIVES or sum(x["rows"] for x in acq)!=EXPECTED_ASSET_HOURS:
        raise ValueError("Clean-4 acquisition completeness failure")
    report["acquisition"]={
        "archives":len(acq),"asset_hours":sum(x["rows"] for x in acq),
        "archive_manifest_sha256":sha(json.dumps(acq,sort_keys=True,separators=(",",":")).encode()),
    }
    report["prices"]=canonicalize(a.archive_root,a.canonical_root)
    funding={}
    for asset in CLEAN4:
        raw=(a.funding_root/f"{asset}_funding.csv").read_bytes()
        funding[asset]=audit_bytes(raw,asset)
    if len({x["selected_events"] for x in funding.values()})!=1:
        raise ValueError("Clean-4 funding coverage mismatch")
    report["funding"]=funding
    report["status"]="PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA"
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"archives":len(acq),
                      "asset_hours":report["acquisition"]["asset_hours"],
                      "funding_assets":len(funding)},sort_keys=True))

if __name__=="__main__":
    main()
