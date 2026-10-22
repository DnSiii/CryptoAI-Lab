#!/usr/bin/env python3
"""V98 N complete seven-slot composed SOURCE ONLY; Phase919 prereg, NO PnL.

Six frozen M slots + new maximal-retention 16-corner causal Risk Governor.
No funding/mark/2025+/benchmarks, no changes to M/K/J frozen targets.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from phase866_k_sevenslot_source import ASSETS, START, END, PINS, pinned_training_frames
from phase900_m_persistent_growth_source import compose_m
from phase903_m_frozen_paths import PATHS as M_PATHS, EXCLUDE, FULL_PIN

ROOT=Path(__file__).resolve().parent
LOOKBACK=336
TAIL_QUANTILE=.99
MIN_SHOCK=.02
ASSET_CAP=.70
GROSS_CAP=1.75
N_PATHS=('N_core_only','N_full','N_minus_opportunity','N_minus_relative_value','N_minus_recovery')


def envelope(open_:np.ndarray, high:np.ndarray, low:np.ndarray):
    """At close(t), only bars <=t contribute to the NEXT open's stress."""
    op=np.asarray(open_,float);hi=np.asarray(high,float);lo=np.asarray(low,float)
    if op.ndim!=2 or op.shape[1]!=4 or hi.shape!=op.shape or lo.shape!=op.shape:
        raise ValueError('aligned four-asset arrays required')
    if not all(np.isfinite(a).all() for a in (op,hi,lo)) or (op<=0).any() or (lo<=0).any() or (hi<op).any() or (lo>op).any():
        raise ValueError('invalid OHLC geometry')
    u=pd.DataFrame(hi/op-1).rolling(LOOKBACK,min_periods=LOOKBACK).quantile(TAIL_QUANTILE).to_numpy()
    d=pd.DataFrame(1-lo/op).rolling(LOOKBACK,min_periods=LOOKBACK).quantile(TAIL_QUANTILE).to_numpy()
    valid=np.isfinite(u).all(axis=1)&np.isfinite(d).all(axis=1)
    u=np.where(valid[:,None],np.maximum(MIN_SHOCK,u),np.nan)
    d=np.where(valid[:,None],np.maximum(MIN_SHOCK,d),np.nan)
    if np.any(d[valid]>=1):raise ValueError('lower shock >=100%: fail closed')
    return d,u,valid


def maximal_retention(weights,lower,upper):
    """Exact linear-fractional 16-corner upper bound on scalar k in [0,1].

    Marked equity=1+k*sum_i(w_i*(f_i-1)). For each corner f:
    gross k*sum(w*f)/equity<=1.75, per asset k*w_i*f_i/equity<=.70.
    """
    w=np.asarray(weights,float);dn=np.asarray(lower,float);up=np.asarray(upper,float)
    if w.ndim!=2 or w.shape[1]!=4 or dn.shape!=w.shape or up.shape!=w.shape:
        raise ValueError('four-asset aligned arrays required')
    if not np.isfinite(w).all() or (w<0).any() or (w.max(axis=1)>ASSET_CAP+1e-9).any() or (w.sum(axis=1)>GROSS_CAP+1e-9).any():
        raise ValueError('invalid frozen M target')
    valid=np.isfinite(dn).all(axis=1)&np.isfinite(up).all(axis=1)
    if np.any(dn[valid]<0) or np.any(dn[valid]>=1) or np.any(up[valid]<0):
        raise ValueError('invalid stress envelope')
    k=np.ones(len(w),float)
    k[~valid]=0.
    for bits in range(16):
        factor=np.where(np.array([(bits>>j)&1 for j in range(4)],bool),1+np.where(valid[:,None],up,0),1-np.where(valid[:,None],dn,0))
        a=w*factor
        total=a.sum(axis=1)
        drift=total-w.sum(axis=1)
        gross_denom=total-GROSS_CAP*drift
        k=np.minimum(k,np.divide(GROSS_CAP,gross_denom,out=np.full(len(w),np.inf),where=gross_denom>0))
        asset_denom=a-ASSET_CAP*drift[:,None]
        bounds=np.divide(ASSET_CAP,asset_denom,out=np.full_like(a,np.inf),where=asset_denom>0)
        k=np.minimum(k,bounds.min(axis=1))
        k=np.minimum(k,np.divide(1-1e-12,-drift,out=np.full(len(w),np.inf),where=drift<0))
    return np.clip(k,0,1)


def corners_safe(weights,lower,upper,tol=1e-8):
    """Independent direct corner check; no shared closed-form calculation."""
    w=np.asarray(weights,float);dn=np.asarray(lower,float);up=np.asarray(upper,float)
    valid=np.isfinite(dn).all(axis=1)&np.isfinite(up).all(axis=1)
    if np.any(w[~valid]!=0):return False
    for bits in range(16):
        factor=np.where(np.array([(bits>>j)&1 for j in range(4)],bool),1+np.nan_to_num(up,nan=0),1-np.nan_to_num(dn,nan=0))
        value=w*factor
        eq=1-w.sum(axis=1)+value.sum(axis=1)
        if (eq<=0).any() or (value.sum(axis=1)>GROSS_CAP*eq+tol).any() or (value>ASSET_CAP*eq[:,None]+tol).any():
            return False
    return True


def pinned_bars(root=ROOT):
    # The same immutable SHA256 pins already authenticated for frozen M.
    root=Path(root)
    close,high=pinned_training_frames(root/'phase243_clean4_canonical')
    fields={}
    for a in ASSETS:
        f=pd.read_csv(root/'phase243_clean4_canonical'/f'{a}_1h.csv')
        fields[a]=f
    def field(name):return np.column_stack([fields[a][name].to_numpy(float) for a in ASSETS])
    op,hi,lo=field('open'),field('high'),field('low')
    if not np.allclose(hi,high.to_numpy(float),rtol=0,atol=0):raise PermissionError('high field drift')
    return close,high,op,hi,lo


def freeze_n(root=ROOT):
    close,high,op,hi,lo=pinned_bars(root)
    down,up,valid=envelope(op,hi,lo)
    paths={};hashes={};stats={}
    for mp,npth in zip(M_PATHS,N_PATHS):
        m=compose_m(close,high,excluded=EXCLUDE[mp])
        mval=m.to_numpy(float)
        mhash=hashlib.sha256(m.to_csv(float_format='%.12g').encode()).hexdigest()
        if mp=='M_full' and mhash!=FULL_PIN:raise PermissionError('M_full frozen hash drift')
        k=maximal_retention(mval,down,up)
        nval=mval*k[:,None]
        if not corners_safe(nval,down,up):raise AssertionError('N target corner survival failure')
        if (nval>mval+1e-10).any() or (nval<0).any():raise AssertionError('N target violates maximal retention')
        frame=pd.DataFrame(nval,index=close.index,columns=ASSETS)
        paths[npth]=frame
        hashes[npth]=hashlib.sha256(frame.to_csv(float_format='%.12g').encode()).hexdigest()
        yy=close.index.year.to_numpy()
        stats[npth]={}
        for year in (2023,2024):
            ix=yy==year
            mw=mval[ix];nw=nval[ix]
            active=mw.sum(axis=1)>0
            stats[npth][str(year)]={
                'hours':int(ix.sum()),'active_hours':int(active.sum()),
                'retained_mean_gross':float(nw.sum(axis=1).mean()),
                'original_mean_gross':float(mw.sum(axis=1).mean()),
                'retention_ratio':float(nw.sum()/mw.sum()) if mw.sum()>0 else None,
                'hours_scaled':int(((k[ix]<1-1e-10)&active).sum()),
                'min_active_scale':float(k[ix][active].min()) if active.any() else None,
                'max_target_gross':float(nw.sum(axis=1).max()),
                'max_target_asset':float(nw.max()),
                'target_l1_turnover':float(np.abs(np.diff(nw,axis=0)).sum())}
    return paths,{'phase':920,'architecture':'N_complete_seven_slot','source_only':True,
                  'historical_pnl_computed':False,'promotion_eligible':False,
                  'validation_2025_read':False,'holdout_accessed':False,
                  'external_benchmarks_used':False,'envelope_valid_hours':int(valid.sum()),
                  'source_pins':PINS,'frozen_m_full_sha256':FULL_PIN,
                  'paths_sha256':hashes,'structural':stats}


if __name__=='__main__':
    _,result=freeze_n(ROOT)
    (ROOT/'phase920_n_composed_source_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
