#!/usr/bin/env python3
"""V98 Independent Q native mark LOW/HIGH bounds, signed adverse settlement.

Conservative for BOTH long and short positions; never reuse long-only mark.
No alpha, no PnL, no future data; caller supplies authenticated CSV.
"""
from __future__ import annotations
import csv
import math
from pathlib import Path
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
FIELDS=('asset','funding_slot_ms','funding_time_ms','funding_rate',
        'mark_low','mark_high','conservative_mark')


def signed_bounds(path,index,expected_events=9144):
    if not isinstance(index,pd.DatetimeIndex) or index.tz is None or len(index)<1 or index[0].year<2022 or index[-1].year>2024 or not index.equals(pd.date_range(index[0],periods=len(index),freq='h')):
        raise ValueError('Q_SIGNED_BOUNDS_TRAINING_CALENDAR')
    mark=np.full((len(index),4,2),np.nan)
    event=np.zeros((len(index),4),bool)
    rate=np.zeros((len(index),4),float)
    first=int(index[0].timestamp()*1000);last=int(index[-1].timestamp()*1000)
    with Path(path).open(newline='') as stream:
        reader=csv.DictReader(stream)
        if tuple(reader.fieldnames or ())!=FIELDS:
            raise ValueError('Q_SIGNED_BOUNDS_SCHEMA')
        for row in reader:
            a=row['asset']
            if a not in ASSETS:raise ValueError('Q_SIGNED_BOUNDS_NON_CLEAN4')
            j=ASSETS.index(a);slot=int(row['funding_slot_ms']);ts=int(row['funding_time_ms'])
            if not first<=slot<=last or (slot-first)%28_800_000 or not slot<=ts<=slot+29:
                raise ValueError('Q_SIGNED_BOUNDS_EVENT_TIME')
            t=(slot-first)//3_600_000
            if event[t,j]:raise ValueError('Q_SIGNED_BOUNDS_DUPLICATE')
            r=float(row['funding_rate']);low=float(row['mark_low']);high=float(row['mark_high']);legacy=float(row['conservative_mark'])
            if not all(map(math.isfinite,(r,low,high,legacy))) or low<=0 or high<low or legacy!=(high if r>=0 else low):
                raise ValueError('Q_SIGNED_BOUNDS_UNAUTHENTICATED')
            mark[t,j]=[low,high];rate[t,j]=r;event[t,j]=True
    if int(event.sum())!=expected_events:raise ValueError('Q_SIGNED_BOUNDS_INCOMPLETE')
    return mark,rate,event


def adverse_debit(units,rate,mark_bounds):
    u,r,m=np.asarray(units,float),np.asarray(rate,float),np.asarray(mark_bounds,float)
    if u.shape!=(4,) or r.shape!=(4,) or m.shape!=(4,2) or not np.isfinite(u).all() or not np.isfinite(r).all() or not np.isfinite(m).all() or (m[:,0]<=0).any() or (m[:,1]<m[:,0]).any():
        raise ValueError('Q_SIGNED_MARK_INVALID')
    signed=u*r
    return float(np.dot(signed,np.where(signed>=0,m[:,1],m[:,0])))
