#!/usr/bin/env python3
"""V98 Phase1003: source-only ex-post forensic of rejected N's common breach.

No PnL, no retuning, no V16/V99, no 2025+.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from phase803_training_ohlc_official_replay import run as fresh_ohlc
from phase866_k_sevenslot_source import ASSETS, PINS
from phase877_k_official_economic_dispatch import PASS_OHLC
from phase920_n_composed_source import ROOT, freeze_n, pinned_bars, envelope, N_PATHS, corners_safe
from phase924_n_official_90cell_dispatch import FROZEN_N
from phase876_k_funded_ledger import _risk

OUT = ROOT / "phase1003_common_intrabar_forensic_result.json"
T = 2683


def static_corners(weights, opening, low, high):
    w = np.asarray(weights, dtype=float)
    units = w/np.asarray(opening, dtype=float)
    cash = float(1.-w.sum())
    points = [("all_low",np.asarray(low,dtype=float)),
              ("all_high",np.asarray(high,dtype=float))]
    for j in range(4):
        p = np.asarray(low,dtype=float).copy()
        p[j] = high[j]
        points.append(("high_only_"+ASSETS[j],p))
    observations = []
    for label,p in points:
        eq,gross,asset = _risk(cash,units,p)
        observations.append({
            "corner":label, "equity":eq, "gross":gross,
            "max_asset":asset,
            "survives":bool(eq>0 and gross<=1.75+1e-9 and asset<=.70+1e-9),
        })
    return observations


def run():
    receipt = {
        "phase":1003, "decision":"BLOCKED_SOURCE_ONLY",
        "historical_pnl_computed":False, "economic_clearance":False,
        "holdout_accessed":False, "validation_2025_read":False,
        "external_benchmarks_used":False, "frozen_source_modified":False,
        "bar_index":T,
    }
    try:
        o = fresh_ohlc()
        if not isinstance(o,dict) or o.get("decision")!=PASS_OHLC or o.get("vendor_origin_attested") is not True:
            raise PermissionError("FRESH_100_OHLC_NOT_ATTESTED")
        for asset in ASSETS:
            item=o.get("assets",{}).get(asset,{})
            if item.get("sha256")!=PINS[asset] or item.get("hours")!=18288:
                raise PermissionError("OHLC_PIN_DRIFT_"+asset)
        paths,info=freeze_n(ROOT)
        if tuple(info["paths_sha256"])!=N_PATHS or info["paths_sha256"]!=FROZEN_N:
            raise PermissionError("FROZEN_N_TARGET_SHA_DRIFT")
        close,high,op,hi,lo=pinned_bars(ROOT)
        down,up,valid=envelope(op,hi,lo)
        if not bool(valid[T-1]):
            raise ValueError("CAUSAL_ENVELOPE_UNAVAILABLE_AT_TMINUS1")
        asset_info={}
        for j,asset in enumerate(ASSETS):
            asset_info[asset]={
                "open":float(op[T,j]),"high":float(hi[T,j]),
                "low":float(lo[T,j]),"close":float(close.iloc[T,j]),
                "actual_up":float(hi[T,j]/op[T,j]-1),
                "actual_down":float(1-lo[T,j]/op[T,j]),
                "causal_tminus1_up_envelope":float(up[T-1,j]),
                "causal_tminus1_down_envelope":float(down[T-1,j]),
                "up_exceeds_envelope":bool(hi[T,j]/op[T,j]-1>up[T-1,j]),
                "down_exceeds_envelope":bool(1-lo[T,j]/op[T,j]>down[T-1,j]),
            }
        paths_info={}
        for name,frame in paths.items():
            w=frame.to_numpy(float)[T-1]
            corners=static_corners(w,op[T],lo[T],hi[T])
            paths_info[name]={
                "target_tminus1":{a:float(w[j]) for j,a in enumerate(ASSETS)},
                "target_gross":float(w.sum()),
                "causal_16_corner_envelope_safe":bool(corners_safe(
                    w.reshape(1,4),down[T-1].reshape(1,4),up[T-1].reshape(1,4))),
                "static_current_bar_survives":all(x["survives"] for x in corners),
                "static_current_bar_corners":corners,
            }
        receipt.update(
            decision="SOURCE_ONLY_COMMON_BREACH_GEOMETRY_CLASSIFIED",
            timestamp_utc=str(close.index[T]),causal_target_timestamp_utc=str(close.index[T-1]),
            asset_ohlc_and_envelope=asset_info,
            frozen_path_static_checks=paths_info,
            source_receipt=o["decision"],
        )
    except Exception as exc:
        receipt["reason"]=type(exc).__name__+": "+str(exc)[:350]
    OUT.write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "phase":1003,"decision":receipt["decision"],
        "timestamp":receipt.get("timestamp_utc"),
        "up_exceed_assets":[a for a,v in receipt.get("asset_ohlc_and_envelope",{}).items() if v["up_exceeds_envelope"]],
        "down_exceed_assets":[a for a,v in receipt.get("asset_ohlc_and_envelope",{}).items() if v["down_exceeds_envelope"]],
        "static_path_failures":[a for a,v in receipt.get("frozen_path_static_checks",{}).items() if not v["static_current_bar_survives"]],
        "reason":receipt.get("reason"),
    },sort_keys=True))
    return 0 if receipt["decision"].startswith("SOURCE_ONLY_") else 2


if __name__=="__main__":
    raise SystemExit(run())
