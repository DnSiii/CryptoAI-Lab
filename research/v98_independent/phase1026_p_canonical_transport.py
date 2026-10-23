#!/usr/bin/env python3
"""V98 P canonical source-only five-target transport; no historical PnL.

Each nonzero weight is rounded to eight significant decimal digits then reduced
by one decimal quantum. This never increases leverage or a position's exposure.
"""
from __future__ import annotations
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import numpy as np
import pandas as pd
from phase1024_p_sevenslot_source import (ROOT,PATHS,ASSET_CAP,GROSS_CAP,
    pinned_p_bars,compose_p)


def canonical_scalar(x):
    x=float(x)
    if not np.isfinite(x) or x<0:raise ValueError('P_CANONICAL_INVALID_WEIGHT')
    if x==0:return 0.
    d=Decimal(format(x,'.8g'))
    quantum=Decimal(1).scaleb(d.adjusted()-7)
    result=float(max(Decimal(0),d-quantum))
    if result>x+1e-15:raise AssertionError('P_CANONICAL_EXPOSURE_INCREASE')
    return result


def canonical_array(raw):
    x=np.asarray(raw,float)
    if x.ndim!=2 or x.shape[1]!=4 or not np.isfinite(x).all() or (x<0).any():
        raise ValueError('P_CANONICAL_CLEAN4_REQUIRED')
    return np.fromiter((canonical_scalar(v) for v in x.flat),dtype=float,count=x.size).reshape(x.shape)


def canonical_p_paths(root=ROOT):
    op,hi,lo,cl,q=pinned_p_bars(Path(root)/'phase243_clean4_canonical')
    raw=compose_p(op,hi,lo,cl,q)
    frames={}; hashes={}; diagnostics={}
    for name in PATHS:
        original=raw[name].to_numpy(float)
        canon=canonical_array(original)
        if (canon>original+1e-15).any() or (canon<0).any() or canon.max()>ASSET_CAP+1e-12 or canon.sum(axis=1).max()>GROSS_CAP+1e-12:
            raise AssertionError('P_CANONICAL_CAP_OR_EXPOSURE_INCREASE')
        frame=pd.DataFrame(canon,index=cl.index,columns=cl.columns)
        frames[name]=frame
        hashes[name]=hashlib.sha256(frame.to_csv(float_format='%.12g').encode()).hexdigest()
        diagnostics[name]={'max_abs_reduction':float((original-canon).max()),
                           'total_l1_reduction':float((original-canon).sum()),
                           'active_mask_changes':int(np.count_nonzero((original>0)!=(canon>0)))}
    return frames,{'phase':1026,'decision':'P_CANONICAL_SOURCE_ONLY_NOT_ECONOMIC',
                   'paths_sha256':hashes,'diagnostics':diagnostics,
                   'historical_pnl_computed':False,'validation_2025_read':False,
                   'holdout_accessed':False,'external_benchmarks_used':False}

if __name__=='__main__':
    _,out=canonical_p_paths()
    (ROOT/'phase1026_p_canonical_transport_result.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(out,sort_keys=True))
