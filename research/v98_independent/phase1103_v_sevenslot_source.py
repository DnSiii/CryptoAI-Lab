#!/usr/bin/env python3
"""V seven-slot portfolio-first composed target source; no PnL or 2025."""
from __future__ import annotations
import numpy as np
import pandas as pd
from phase1101_v_robust_governor import max_feasible_weights

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS=('V_core_only','V_full','V_minus_opportunity','V_minus_relative_value','V_minus_stress')
SLEEVES=('growth','opportunity','relative_value','stress')
EXCLUDE={'V_core_only':('opportunity','relative_value','stress'),
         'V_full':(),'V_minus_opportunity':('opportunity',),
         'V_minus_relative_value':('relative_value',),'V_minus_stress':('stress',)}
REGIME_MULT=np.array([[.5,.5,1.,1.5],[1.,1.,1.,1.],[1.5,1.25,1.,.5]])

def _validate(op,hi,lo,cl,quote,funding):
    frames=(op,hi,lo,cl,quote,funding)
    if any(not isinstance(f,pd.DataFrame) or tuple(f.columns)!=ASSETS for f in frames):
        raise ValueError('V_CLEAN4_REQUIRED')
    idx=cl.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or len(idx)<1800 or
        idx[0]<pd.Timestamp('2022-12-01T00:00Z') or
        idx[-1]>=pd.Timestamp('2025-01-01T00:00Z') or
        not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h')) or
        any(not idx.equals(f.index) for f in frames)):
        raise ValueError('V_TRAINING_CALENDAR_OR_FUTURE')
    if (any(not np.isfinite(f.to_numpy(float)).all() for f in frames) or
        (op<=0).any().any() or (lo<=0).any().any() or (cl<=0).any().any() or
        (hi<np.maximum(op,cl)).any().any() or
        (lo>np.minimum(op,cl)).any().any() or (quote<0).any().any()):
        raise ValueError('V_INVALID_SOURCE')

def _normalize(a):
    x=np.nan_to_num(np.asarray(a,float),nan=0.,posinf=0.,neginf=0.)
    gross=np.abs(x).sum(axis=1,keepdims=True)
    return np.divide(x,gross,out=np.zeros_like(x),where=gross>1e-12)

def _event_hold(direction,eligible,hold,cooldown):
    a=np.nan_to_num(np.asarray(direction,float),nan=0.)
    e=np.asarray(eligible,bool)
    if a.shape!=e.shape or a.ndim!=2:raise ValueError('V_EVENT_GEOMETRY')
    n,k=a.shape;out=np.zeros_like(a);expiry=np.zeros(k,int);next_allowed=np.zeros(k,int)
    last=np.zeros(k)
    for t in range(n):
        trigger=e[t]&(t>=next_allowed)&(a[t]!=0)
        last[trigger]=a[t,trigger];expiry[trigger]=t+hold
        next_allowed[trigger]=t+cooldown
        out[t]=np.where(t<expiry,last,0.)
    return out

def _hysteresis(desired,dwell=48):
    state=1;next_switch=0;out=np.full(len(desired),1,dtype=np.int8)
    for t,x in enumerate(desired):
        if int(x)!=state and t>=next_switch:
            state=int(x);next_switch=t+dwell
        out[t]=state
    return out

def compose_v(op,hi,lo,cl,quote,funding,*,diagnostics=False):
    _validate(op,hi,lo,cl,quote,funding)
    idx=cl.index;n=len(idx)
    log=np.log(cl);r=log.diff().fillna(0.)
    market=r.mean(axis=1)
    vol168=r.rolling(168,min_periods=168).std(ddof=0)
    vol720=r.rolling(720,min_periods=720).std(ddof=0)
    # 1. Dual momentum and acceleration growth; no U channel breakout.
    mom168=(log-log.shift(168)).to_numpy(float)
    mom720=(log-log.shift(720)).to_numpy(float)
    mom72=log-log.shift(72)
    accel=(mom72-mom72.shift(72)).to_numpy(float)
    s168=np.maximum(vol168.to_numpy(float)*np.sqrt(168),1e-8)
    s720=np.maximum(vol720.to_numpy(float)*np.sqrt(720),1e-8)
    growth_raw=.4*np.tanh(mom168/s168)+.4*np.tanh(mom720/s720)+\
               .2*np.tanh(accel/np.maximum(vol168.to_numpy(float)*np.sqrt(72),1e-8))
    growth=_normalize(growth_raw)
    # 2. Compression-to-expansion opportunity with fixed event cooldown.
    v48=r.rolling(48,min_periods=48).std(ddof=0)
    baseline_v48=v48.shift(1).rolling(336,min_periods=336).median()
    quote24=quote.rolling(24,min_periods=24).sum()
    impulse=quote24>quote24.shift(24)
    follow=np.sign((log-log.shift(24)).to_numpy(float))
    eligible=((v48<baseline_v48)&impulse).fillna(False).to_numpy(bool)
    opportunity=_normalize(_event_hold(follow,eligible,24,96))
    # 3. Native funding-carry dispersion relative-value pair.
    carry=funding.rolling(72,min_periods=72).mean()
    dispersion=carry.max(axis=1)-carry.min(axis=1)
    dispersion_base=dispersion.shift(1).rolling(336,min_periods=336).median()
    carry_arr=carry.to_numpy(float);rv_raw=np.zeros((n,4))
    pair=np.zeros(4);expiry=0
    for t in range(n):
        if t>=expiry:
            pair=np.zeros(4)
            if (np.isfinite(carry_arr[t]).all() and np.isfinite(dispersion_base.iloc[t]) and
                dispersion.iloc[t]>dispersion_base.iloc[t] and dispersion.iloc[t]>0):
                lo_asset=int(np.argmin(carry_arr[t]));hi_asset=int(np.argmax(carry_arr[t]))
                if lo_asset!=hi_asset:
                    pair[lo_asset]=.5;pair[hi_asset]=-.5;expiry=t+48
        rv_raw[t]=pair
    relative_value=_normalize(rv_raw)
    # 4. Directional crash/recovery weighted by signed semivolatility.
    down168=np.sqrt(r.clip(upper=0).pow(2).rolling(168,min_periods=168).mean())
    up168=np.sqrt(r.clip(lower=0).pow(2).rolling(168,min_periods=168).mean())
    breadth_neg=((log-log.shift(24))<0).sum(axis=1)
    breadth_pos=((log-log.shift(24))>0).sum(axis=1)
    market72=market.rolling(72,min_periods=72).sum()
    market48=market.rolling(48,min_periods=48).sum()
    market_vol48=market.rolling(48,min_periods=48).std(ddof=0)
    market_vol_prior=market_vol48.shift(1).rolling(168,min_periods=168).mean()
    crash=((breadth_neg>=3)&(market72<0)).to_numpy(bool)
    recovery=((breadth_pos>=3)&(market48>0)&(market_vol48<market_vol_prior)).to_numpy(bool)
    stress_raw=np.where(crash[:,None],-down168.to_numpy(float),
               np.where(recovery[:,None],up168.to_numpy(float),0.))
    stress=_normalize(stress_raw)
    # 5. Volatility-of-vol and breadth router, minimum dwell 48h.
    market_vol24=market.rolling(24,min_periods=24).std(ddof=0)
    vov=market_vol24.rolling(168,min_periods=168).std(ddof=0)
    vov_base=vov.shift(1).rolling(720,min_periods=720).median()
    regime_raw=np.where((breadth_neg>=3)&(vov>vov_base),0,
               np.where((breadth_pos>=3)&(vov<vov_base),2,1))
    regime=_hysteresis(regime_raw,48)
    # 6/7. Joint conviction allocator + pretrade robust governor.
    prev=cl.shift(1)
    d=(1-lo/prev).clip(lower=0).rolling(336,min_periods=336).max().round(8)
    h=(hi/prev-1).clip(lower=0).rolling(336,min_periods=336).max().round(8)
    f=funding.abs().rolling(720,min_periods=720).max()
    sleeves={'growth':growth,'opportunity':opportunity,'relative_value':relative_value,'stress':stress}
    paths={}
    for name in PATHS:
        out=np.zeros((n,4));last=np.zeros(4);expiry=0
        for t in range(n):
            if t%12==0:
                if (not np.isfinite(d.iloc[t]).all() or not np.isfinite(h.iloc[t]).all() or
                    not np.isfinite(f.iloc[t]).all()):
                    last=np.zeros(4);expiry=0
                else:
                    scores=[];signals=[]
                    for j,sleeve in enumerate(SLEEVES):
                        sig=sleeves[sleeve][t]
                        score=0. if sleeve in EXCLUDE[name] else min(1.,float(np.abs(sig).sum()))
                        if sleeve=='relative_value' and score:
                            med=float(dispersion_base.iloc[t])
                            score*=min(1.,float(dispersion.iloc[t])/med) if np.isfinite(med) and med>0 else 0.
                        scores.append(score*REGIME_MULT[regime[t],j]);signals.append(sig)
                    total=sum(scores)
                    raw=sum((scores[j]/total)*signals[j] for j in range(4)) if total>0 else np.zeros(4)
                    proposal=max_feasible_weights(raw,cl.iloc[t].to_numpy(float),
                         d.iloc[t].to_numpy(float),h.iloc[t].to_numpy(float),f.iloc[t].to_numpy(float))
                    if np.any(proposal):last=proposal;expiry=t+36
                    elif t>=expiry:last=np.zeros(4)
            out[t]=last
        paths[name]=pd.DataFrame(out,index=idx,columns=ASSETS)
    if diagnostics:
        return paths,{'regime_hours':{str(i):int((regime==i).sum()) for i in range(3)},
            'active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum()) for k,v in sleeves.items()},
            'historical_pnl_computed':False,'validation_2025_read':False,
            'holdout_accessed':False,'external_benchmarks_used':False,
            'requires_authenticated_source_and_full_ledger_freeze':True}
    return paths
