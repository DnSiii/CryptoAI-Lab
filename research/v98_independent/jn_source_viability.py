#!/usr/bin/env python3
"""JN source-only financed epoch viability on authenticated 100-archive taker flow; no PnL."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from phase1260_aj_authenticated_source_digest import load_official,HOURS,START
from phase803_training_ohlc_official_replay import ASSETS,PINS
from jn_native_taker_flow_sources import bundle,static_check,WARMUP,CLOCK
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"jn_source_viability.json"

def load_taker():
    receipt=json.loads((ROOT/"jn_native_taker_flow_source_receipt.json").read_text())
    if (receipt.get("decision")!="PASS_JN_NATIVE_TAKER_SOURCE_INTEGRITY_ONLY_NOT_ECONOMIC"
        or receipt.get("hours")!=HOURS or receipt.get("assets")!=list(ASSETS)
        or receipt.get("months",[None])[-1]!="2024-12"
        or receipt.get("canonical_pins")!={a:PINS[a][0] for a in ASSETS}
        or len(receipt.get("official_archive_sha256",{}))!=4
        or any(len(v)!=25 for v in receipt["official_archive_sha256"].values())):
        raise ValueError("JN_TAKER_SOURCE_RECEIPT_FIREWALL")
    # Preserve exact IEEE-754 17-digit CSV round trips for the signed source digest.
    df=pd.read_csv(ROOT/"jn_native_taker_flow_source.csv",float_precision="round_trip")
    if list(df.columns)!=["open_time",*ASSETS] or len(df)!=HOURS:
        raise ValueError("JN_TAKER_SOURCE_SCHEMA")
    ts=pd.to_datetime(df["open_time"],utc=True)
    expected=pd.date_range(START,periods=HOURS,freq="h",tz="UTC")
    if not ts.equals(pd.Series(expected)):
        raise ValueError("JN_TAKER_SOURCE_CHRONOLOGY")
    cols=[]
    for asset in ASSETS:
        ratio=pd.to_numeric(df[asset],errors="raise").to_numpy(dtype=float)
        digest=hashlib.sha256(np.nan_to_num(ratio,nan=-1.).astype("<f8").tobytes()).hexdigest()
        if digest!=receipt["taker_ratio_sha256"][asset]:
            raise ValueError("JN_TAKER_SOURCE_DIGEST_"+asset)
        cols.append(ratio)
    return np.column_stack(cols),receipt

def run():
    assert static_check()
    frames,manifest=load_official()
    taker,receipt=load_taker()
    o,h,l,c,q,r,e,ml,mh=frames
    targets,updates,regimes,valid,forecasts=bundle(o,h,l,c,r,e,q,taker)
    names=("opportunity","relative_value","stress_recovery")
    counts={y:{name:0 for name in names} for y in ("2023","2024")}
    invalid={y:0 for y in counts}
    states={y:{} for y in counts}
    for t in range(WARMUP,HOURS,CLOCK):
        year="2023" if t<9504 else "2024"
        if not updates[t] or not np.isfinite(targets[t]).all():
            raise ValueError("JN_EPOCH_NONFINITE")
        gross=np.abs(targets[t]).sum(axis=1)
        if valid[t]:
            if not np.allclose(gross,1.,atol=1e-10):
                raise ValueError("JN_GROSS_NONCONSERVATION")
        elif not (np.allclose(gross,1.,atol=1e-10) or np.allclose(gross,0.,atol=1e-10)):
            raise ValueError("JN_QUARANTINE_GROSS")
        if not valid[t]:
            invalid[year]+=1
            if not np.allclose(targets[t],targets[t,0]):
                raise ValueError("JN_INVALID_SOURCE_NOT_QUARANTINED")
            continue
        states[year][regimes[t]]=states[year].get(regimes[t],0)+1
        for j,name in enumerate(names,2):
            counts[year][name]+=int(np.abs(targets[t,1]-targets[t,j]).sum()>.025)
    viable=all(counts[y][name]>=8 for y in counts for name in names)
    result={"architecture":"JN","source_only":True,
            "historical_system_pnl_computed":False,"validation_2025_read":False,
            "external_benchmarks_used":False,"trading_authorized":False,
            "native_source_manifest":manifest,"taker_receipt":receipt,
            "financed_forecast_perturbation_epochs":counts,
            "invalid_epochs":invalid,"regimes":states,
            "decision":"PASS_JN_SOURCE_ONLY_NOT_ECONOMIC" if viable else
                       "REJECT_JN_SOURCE_ONLY_INSUFFICIENT_FUNDED_EPOCHS"}
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,default=str)+"\n")
    print("JN_SOURCE_ONLY",result["decision"],json.dumps(counts,sort_keys=True),flush=True)
    if not viable:raise SystemExit(2)
    return result

if __name__=="__main__":run()
