#!/usr/bin/env python3
"""V98 Independent S preregistered complete seven-slot source-only engine.

No 2025+, no historical PnL, no prior-engine alpha imports, t+1 execution.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS=('S_core_only','S_full','S_minus_opportunity','S_minus_relative_value','S_minus_recovery')
SLEEVES=('growth','opportunity','relative_value','recovery')
EXCLUDE={'S_core_only':('opportunity','relative_value','recovery'), 'S_full':(),
         'S_minus_opportunity':('opportunity',),'S_minus_relative_value':('relative_value',),
         'S_minus_recovery':('recovery',)}
BUDGET=np.array([[.35,.10,.40,.15],[.65,.20,.10,.05],[.75,.20,.03,.02]])
GROSS=np.array([.45,1.,1.35]);ASSET_CAP=.45;NET_CAP=.75;GROSS_CAP=1.35


def validate(op,hi,lo,cl,quote,funding):
    fs=(op,hi,lo,cl,quote,funding);idx=cl.index
    if any(not isinstance(x,pd.DataFrame) or tuple(x.columns)!=ASSETS for x in fs):raise ValueError('S_CLEAN4_REQUIRED')
    if not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or len(idx)<1600 or idx[0].year<2022 or idx[-1].year>2024 or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h')) or any(not x.index.equals(idx) for x in fs):
        raise ValueError('S_CHRONOLOGICAL_TRAINING_ONLY')
    if any(not np.isfinite(x.to_numpy(float)).all() for x in fs):raise ValueError('S_NONFINITE_SOURCE')
    if (op<=0).any().any() or (lo<=0).any().any() or (quote<0).any().any() or (hi<np.maximum(op,cl)).any().any() or (lo>np.minimum(op,cl)).any().any():
        raise ValueError('S_INVALID_OHLC')


def unit(x):
    a=np.nan_to_num(np.asarray(x,float),nan=0.,posinf=0.,neginf=0.)
    d=np.abs(a).sum(axis=1,keepdims=True)
    return np.divide(a,d,out=np.zeros_like(a),where=d>1e-12)


def hold(raw,event,hours=8,cooldown=0):
    n,k=raw.shape;out=np.zeros_like(raw);ttl=np.zeros(k,int);last=np.zeros(k);blocked=np.zeros(k,int)
    for t in range(n):
        fired=np.asarray(event[t],bool)&(raw[t]!=0)&(blocked==0)
        last[fired]=raw[t,fired];ttl[fired]=hours;blocked[fired]=cooldown
        out[t]=np.where(ttl>0,last,0.)
        ttl=np.maximum(ttl-1,0);blocked=np.maximum(blocked-1,0)
    return out


def router(market,dispersion):
    trend=market.rolling(168,min_periods=168).sum()
    vol72=market.rolling(72,min_periods=72).std(ddof=0)
    base=vol72.shift(1).rolling(720,min_periods=720).median()
    ratio=vol72/base.where(base>1e-12)
    disp=dispersion.rolling(72,min_periods=72).mean()
    dispbase=disp.shift(1).rolling(720,min_periods=720).median()
    stressed=(trend<0)&((ratio>1.4)|(disp>1.4*dispbase))
    expansion=(trend>0)&(ratio<1.15)
    desired=np.where(stressed,0,np.where(expansion,2,1))
    out=np.ones(len(desired),np.int8);state=1;last=1;streak=0
    for t,v in enumerate(desired):
        v=int(v);streak=streak+1 if v==last else 1;last=v
        if streak>=24:state=v
        out[t]=state
    return out


def governor(raw,states):
    out=np.zeros_like(raw)
    for t,v in enumerate(raw):
        if not np.isfinite(v).all():raise ValueError('S_NONFINITE_COMPOSED_WEIGHT')
        g=float(np.abs(v).sum());a=float(np.abs(v).max());net=float(abs(v.sum()))
        if g<1e-12:continue
        # Margin reserve > 1 quantization unit; post-serialization cap checks.
        scale=min(1.,(GROSS[int(states[t])]-2e-5)/g,(GROSS_CAP-2e-5)/g,
                  (ASSET_CAP-2e-5)/max(a,1e-12),(NET_CAP-2e-5)/max(net,1e-12))
        w=np.round(v*scale,6)
        if not np.isfinite(w).all() or np.abs(w).max()>ASSET_CAP+1e-10 or np.abs(w).sum()>GROSS[int(states[t])]+1e-10 or abs(w.sum())>NET_CAP+1e-10:
            raise ValueError('S_POST_SERIALIZATION_CAP_FAILURE')
        out[t]=w
    return out


def compose_s(op,hi,lo,cl,quote,funding,*,diagnostics=False):
    validate(op,hi,lo,cl,quote,funding)
    idx=cl.index;n=len(idx);log=np.log(cl);r=log.diff();market=r.mean(axis=1)
    # Growth: aligned EMA slopes and 96h path efficiency, long-biased.
    ema24=cl.ewm(span=24,adjust=False,min_periods=24).mean()
    ema168=cl.ewm(span=168,adjust=False,min_periods=168).mean()
    slope24=np.log(ema24/ema24.shift(24));slope168=np.log(ema168/ema168.shift(24))
    efficiency=(log-log.shift(96)).abs()/r.abs().rolling(96,min_periods=96).sum().where(lambda x:x>1e-12)
    g=(slope24.clip(lower=0)*slope168.clip(lower=0)).pow(.5)*efficiency
    growth=unit(g.where(efficiency>.25,0.))
    # Opportunity: prior range compression, 4h expansion and volume acceleration.
    rng12=(hi.rolling(12,min_periods=12).max()-lo.rolling(12,min_periods=12).min())/cl
    prior=rng12.shift(12).rolling(168,min_periods=168).median()
    compressed=(rng12.shift(4)<.60*prior.shift(4))
    move4=(log-log.shift(4));expanded=move4.abs()>1.2*rng12.shift(4)
    v4=quote.rolling(4,min_periods=4).mean()
    v168=quote.shift(4).rolling(168,min_periods=168).median()
    event=(compressed&expanded&(v4>1.5*v168)).to_numpy(bool)
    opportunity=unit(hold(np.sign(move4).to_numpy(float),event,8))
    # Relative-value: net-zero cross-sectional volatility-normalized 96h trend.
    vol96=r.rolling(96,min_periods=96).std(ddof=0)
    strength=(log-log.shift(96)).div(vol96.where(vol96>1e-12))
    rv=strength.sub(strength.mean(axis=1),axis=0)
    relative_value=unit(rv)
    # Recovery: higher lows after 48h market drawdown; 24h cooldown.
    m48=market.rolling(48,min_periods=48).sum()
    sigma48=m48.shift(1).rolling(336,min_periods=336).std(ddof=0)
    lows=lo.mean(axis=1)
    event_recovery=((m48<-2*sigma48)&(sigma48>0)&(lows>lows.shift(1))&(lows.shift(1)>lows.shift(2))).to_numpy(bool)
    recovery=unit(hold(np.ones((n,4)),np.repeat(event_recovery[:,None],4,axis=1),8,24))
    sleeves={'growth':growth,'opportunity':opportunity,'relative_value':relative_value,'recovery':recovery}
    states=router(market,r.std(axis=1,ddof=0))
    # Dynamic signal confidence, not shadow-return fitting.
    confidence={'growth':np.nan_to_num(efficiency.mean(axis=1).to_numpy(float),nan=0.).clip(0,1),
                'opportunity':np.where(np.abs(opportunity).sum(axis=1)>0,1.,0.),
                'relative_value':np.where(np.abs(relative_value).sum(axis=1)>0,1.,0.),
                'recovery':np.where(np.abs(recovery).sum(axis=1)>0,1.,0.)}
    funding_headroom=(1-np.minimum(.4,100*funding.abs().rolling(72,min_periods=1).mean().mean(axis=1))).to_numpy(float)
    result={}
    for name in PATHS:
        raw=np.zeros((n,4))
        for j,k in enumerate(SLEEVES):
            if k not in EXCLUDE[name]:raw+=((BUDGET[states,j]*confidence[k]*funding_headroom)[:,None])*sleeves[k]
        result[name]=pd.DataFrame(governor(raw,states),index=idx,columns=ASSETS)
    if diagnostics:
        return result,{'regime_hours':{str(i):int((states==i).sum()) for i in range(3)},
                       'active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum()) for k,v in sleeves.items()},
                       'historical_pnl_computed':False,'validation_2025_read':False,'external_benchmarks_used':False}
    return result
