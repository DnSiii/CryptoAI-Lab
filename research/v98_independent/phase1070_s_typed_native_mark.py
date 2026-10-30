#!/usr/bin/env python3
"""V98 Independent S typed native funding mark low/high transport, source-only.

Explicitly distinguishes vendor conservative (n,4) from signed bounds (n,4,2).
No PnL, no external benchmark, no 2025+.
"""
from __future__ import annotations
import csv
import math
from pathlib import Path
import numpy as np
import pandas as pd
from phase1069_s_sevenslot_source import ASSETS

FIELDS=('asset','funding_slot_ms','funding_time_ms','funding_rate',
        'mark_low','mark_high','conservative_mark')


def signed_mark_bounds(path,index,rate,event,conservative,*,require_full=True):
    idx=pd.DatetimeIndex(index)
    n=len(idx);r=np.asarray(rate,float);ev=np.asarray(event);mark=np.asarray(conservative,float)
    if n<2 or idx.tz is None or not idx.equals(pd.date_range(idx[0],periods=n,freq='h')) or idx[-1].year>2024:
        raise ValueError('S_TYPED_TRAINING_CALENDAR')
    if r.shape!=(n,4) or ev.shape!=(n,4) or ev.dtype!=bool or mark.shape!=(n,4):
        raise ValueError('S_TYPED_MARK_TRANSPORT_SHAPE')
    if not np.isfinite(r).all() or np.any(r[~ev]!=0) or np.isfinite(mark[~ev]).any() or not np.isfinite(mark[ev]).all():
        raise ValueError('S_TYPED_NATIVE_EVENT_INTEGRITY')
    result=np.full((n,4,2),np.nan);seen=np.zeros((n,4),bool)
    first=int(idx[0].timestamp()*1000)
    with Path(path).open(newline='') as stream:
        reader=csv.DictReader(stream)
        if tuple(reader.fieldnames or ())!=FIELDS:raise ValueError('S_TYPED_MARK_SCHEMA')
        for row in reader:
            asset=row['asset']
            if asset not in ASSETS:raise ValueError('S_TYPED_NON_CLEAN4_ASSET')
            j=ASSETS.index(asset);slot=int(row['funding_slot_ms']);ts=int(row['funding_time_ms'])
            if (slot-first)%3_600_000 or not slot<=ts<=slot+29:
                raise ValueError('S_TYPED_EVENT_TIME')
            t=(slot-first)//3_600_000
            if t<0 or t>=n or seen[t,j] or not ev[t,j]:raise ValueError('S_TYPED_EVENT_DUPLICATE_OR_UNEXPECTED')
            f=float(row['funding_rate']);low=float(row['mark_low']);high=float(row['mark_high']);m=float(row['conservative_mark'])
            if not all(math.isfinite(v) for v in (f,low,high,m)) or low<=0 or high<low or f!=r[t,j] or m!=mark[t,j] or m!=(high if f>=0 else low):
                raise ValueError('S_TYPED_VENDOR_SIGNED_MARK_MISMATCH')
            result[t,j]=[low,high];seen[t,j]=True
    if not np.array_equal(seen,ev) or np.isfinite(result[~ev]).any() or not np.isfinite(result[ev]).all():
        raise ValueError('S_TYPED_INCOMPLETE_NATIVE_MARK_EVENTS')
    if require_full and (n!=18288 or int(seen.sum())!=9144 or any(int(seen[:,j].sum())!=2286 for j in range(4))):
        raise ValueError('S_TYPED_INCOMPLETE_OFFICIAL_CLEAN4')
    return result
