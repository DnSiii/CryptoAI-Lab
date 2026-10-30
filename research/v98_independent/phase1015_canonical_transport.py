#!/usr/bin/env python3
"""V98 Phase1015: deterministic 8g-minus-one-quantum O transport; NO PnL."""
from __future__ import annotations
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import numpy as np
import pandas as pd
from phase1008_o_frozen_paths import ROOT, verify_o_source
from phase1006_o_sevenslot_source import (
    PATHS, pinned_o_bars, compose_o, causal_shocks, verify_corners,
    ASSET_CAP, GROSS_CAP, STRESS_EQUITY_FLOOR,
)

def canonical_scalar(x):
    x=float(x)
    if not np.isfinite(x) or x<0:
        raise ValueError("O_CANONICAL_INVALID_WEIGHT")
    if x==0:
        return 0.
    dec=Decimal(format(x,".8g"))
    quantum=Decimal(1).scaleb(dec.adjusted()-7)
    result=float(max(Decimal(0),dec-quantum))
    if result>x+1e-15:
        raise AssertionError("O_CANONICAL_EXPOSURE_INCREASE")
    return result


def canonical_array(weights):
    raw=np.asarray(weights,float)
    if raw.ndim!=2 or raw.shape[1]!=4 or not np.isfinite(raw).all() or (raw<0).any():
        raise ValueError("O_CANONICAL_CLEAN4_REQUIRED")
    flat=np.fromiter((canonical_scalar(x) for x in raw.flat),dtype=float,count=raw.size)
    return flat.reshape(raw.shape)


def canonical_o_paths(root=ROOT):
    verify_o_source(root)
    op,hi,lo,cl=pinned_o_bars(Path(root)/"phase243_clean4_canonical")
    paths=compose_o(op,hi,lo,cl)
    down,up,valid=causal_shocks(op.to_numpy(float),hi.to_numpy(float),lo.to_numpy(float))
    output, hashes, diagnostics={}, {}, {}
    for name in PATHS:
        raw=paths[name].to_numpy(float)
        canon=canonical_array(raw)
        if (canon>raw+1e-15).any() or (canon<0).any():
            raise AssertionError("O_CANONICAL_EXPOSURE_INCREASE")
        if canon.max()>ASSET_CAP+1e-12 or canon.sum(axis=1).max()>GROSS_CAP+1e-12:
            raise AssertionError("O_CANONICAL_GROSS_OR_ASSET_CAP")
        if not verify_corners(canon,down,up,tol=1e-9):
            raise AssertionError("O_CANONICAL_16_CORNER_SURVIVAL")
        frame=pd.DataFrame(canon,index=cl.index,columns=cl.columns)
        output[name]=frame
        hashes[name]=hashlib.sha256(frame.to_csv(float_format="%.12g").encode()).hexdigest()
        diagnostics[name]={
            "max_abs_reduction":float((raw-canon).max()),
            "total_l1_reduction":float((raw-canon).sum()),
            "active_mask_changes":int(np.count_nonzero((raw>0)!=(canon>0))),
            "max_gross":float(canon.sum(axis=1).max()),
            "max_asset":float(canon.max()),
            "source_only":True,
        }
    return output, {"phase":1015,"decision":"CANONICAL_SOURCE_ONLY_NOT_ECONOMIC",
                    "historical_pnl_computed":False,"validation_2025_read":False,
                    "holdout_accessed":False,"external_benchmarks_used":False,
                    "paths_sha256":hashes,"diagnostics":diagnostics,
                    "causal_shock_valid_hours":int(valid.sum())}


if __name__=="__main__":
    _,result=canonical_o_paths()
    (ROOT/"phase1015_canonical_transport_result.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps(result,sort_keys=True))
