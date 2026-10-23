#!/usr/bin/env python3
"""V98 Independent Q seven-slot signed source-only targets, no historical PnL.

Synthetic inputs allowed for testing. Official Clean-4 native funding + pinned
OHLC must be independently authenticated before any historical target freeze.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS=('Q_core_only','Q_full','Q_minus_opportunity','Q_minus_relative_value','Q_minus_recovery')
SHARES={'growth':.50,'opportunity':.20,'relative_value':.20,'recovery':.10}
EXCLUDE={'Q_core_only':('opportunity','relative_value','recovery'),
         'Q_full':(), 'Q_minus_opportunity':('opportunity',),
         'Q_minus_relative_value':('relative_value',), 'Q_minus_recovery':('recovery',)}
GROSS={0:.35,1:.95,2:1.35}


def _unit_signed(a):
    x=np.nan_to_num(np.asarray(a,float),nan=0.,posinf=0.,neginf=0.)
    s=np.abs(x).sum(axis=1,keepdims=True)
    return np.divide(x,s,out=np.zeros_like(x),where=s>1e-12)


def _validate(op,hi,lo,cl,quote,funding):
    frames=(op,hi,lo,cl,quote,funding)
    if not all(isinstance(f,pd.DataFrame) and tuple(f.columns)==ASSETS for f in frames):
        raise ValueError('Q_CLEAN4_COLUMNS_REQUIRED')
    idx=cl.index
    if len(idx)<1600 or not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or idx[0].year<2022 or idx[-1].year>2024 or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h')) or any(not f.index.equals(idx) for f in frames):
        raise ValueError('Q_TRAINING_CHRONOLOGY_ONLY')
    if not all(np.isfinite(f.to_numpy(float)).all() for f in frames):
        raise ValueError('Q_NONFINITE_SOURCE')
    if (op<=0).any().any() or (lo<=0).any().any() or (quote<0).any().any() or (hi<np.maximum(op,cl)).any().any() or (lo>np.minimum(op,cl)).any().any():
        raise ValueError('Q_INVALID_OHLC_VOLUME')


def _hold_events(raw, strength, hours=12):
    result=np.zeros_like(raw)
    last=np.zeros(raw.shape[1]);ttl=np.zeros(raw.shape[1],int)
    for t in range(len(raw)):
        event=np.isfinite(strength[t]) & (strength[t]>0) & (raw[t]!=0)
        last[event]=raw[t,event]
        ttl[event]=hours
        result[t]=np.where(ttl>0,last,0)
        ttl=np.maximum(ttl-1,0)
    return result


def _regime(market):
    neg=market.clip(upper=0).pow(2).rolling(336,min_periods=336).mean()
    pos=market.clip(lower=0).pow(2).rolling(336,min_periods=336).mean()
    asym=neg/pos.where(pos>1e-15)
    v168=market.rolling(168,min_periods=168).std(ddof=0)
    ratio=v168/v168.shift(1).rolling(720,min_periods=720).median()
    defensive=(asym>1.6)&(ratio>1.4)
    expansion=(asym<.9)&(ratio<1.1)
    raw=np.where(defensive,0,np.where(expansion,2,1))
    state=1;last=-1;streak=0;out=np.ones(len(market),np.int8)
    for t,v in enumerate(raw):
        v=int(v);streak=streak+1 if v==last else 1;last=v
        if streak>=36:state=v
        out[t]=state
    return out


def _shadow(sleeves,close,funding):
    ret=close.pct_change().fillna(0).to_numpy(float)
    fr=funding.to_numpy(float)
    out={}
    for k,s in sleeves.items():
        # shadow positions are signals at completed t-1; t native funding
        pnl=np.zeros(len(ret))
        pnl[1:]=np.sum(s[:-1]*(ret[1:]-fr[1:]),axis=1)
        turnover=np.zeros(len(ret))
        turnover[2:]=np.abs(s[1:-1]-s[:-2]).sum(axis=1)
        pnl-=.0012*turnover
        out[k]=pnl
    return out


def _online_shares(shadow,index):
    n=len(index);keys=tuple(SHARES);prior=np.array([SHARES[k] for k in keys]);current=prior.copy()
    out=np.tile(prior,(n,1))
    for t in range(n):
        if index[t].hour==0 and t>=336:
            gains=[]
            for k in keys:
                window=shadow[k][t-336:t]
                if not np.isfinite(window).all() or np.any(window<=-1):
                    raise ValueError('Q_INVALID_CAUSAL_SHADOW_RETURN')
                gains.append(np.log1p(window).sum()/14.)
            logits=np.clip(.20*np.array(gains),-40,40)
            v=prior*np.exp(logits-logits.max())
            v=v/v.sum()
            current=.85*v+.15*prior
            current=np.maximum(current,.05);current=current/current.sum()
        out[t]=current
    return {k:out[:,i] for i,k in enumerate(keys)}


def compose_q(op,hi,lo,cl,quote,funding,*,diagnostics=False):
    """Pure Q target builder: input at close(t), executable no earlier than open(t+1)."""
    _validate(op,hi,lo,cl,quote,funding)
    idx=cl.index;n=len(idx)
    log=np.log(cl);r=log.diff();market=r.mean(axis=1)
    ret72=log-log.shift(72);ret504=log-log.shift(504)
    vol240=r.rolling(240,min_periods=240).std(ddof=0)
    agree=(np.sign(ret72)==np.sign(ret504))&(ret72!=0)
    core=np.sign(ret72)*np.sqrt(np.abs(ret72*ret504))/vol240.where(vol240>1e-12)
    core=core.where(agree,0).to_numpy(float)
    vol6=quote.rolling(6,min_periods=6).median()
    volprior=quote.shift(6).rolling(168,min_periods=168).median()
    r6=log-log.shift(6)
    sigma6=r6.shift(1).rolling(168,min_periods=168).std(ddof=0)
    opp_event=((vol6/volprior.where(volprior>0))>=2.)&(r6.abs()>1.25*sigma6)&(sigma6>0)
    opp=_hold_events(np.sign(r6).to_numpy(float),opp_event.to_numpy(float))
    beta_var=market.rolling(504,min_periods=504).var(ddof=0)
    beta=r.rolling(504,min_periods=504).cov(market).div(beta_var.where(beta_var>1e-16),axis=0)
    residual=(r-beta.mul(market,axis=0)).rolling(72,min_periods=72).sum()
    residual_std=residual.shift(1).rolling(504,min_periods=504).std(ddof=0)
    z=residual.div(residual_std.where(residual_std>1e-12))
    raw=-np.sign(z)*(z.abs()-1.25).clip(lower=0)
    rv=np.zeros((n,4));b=beta.to_numpy(float);rawv=raw.to_numpy(float)
    for t in range(n):
        v=np.nan_to_num(rawv[t],nan=0.,posinf=0.,neginf=0.)
        if np.abs(v).sum()==0 or not np.isfinite(b[t]).all():continue
        # Orthogonal projection onto net-zero and rolling-beta-zero signed book.
        basis=np.column_stack((np.ones(4),b[t]))
        rv[t]=v-basis@np.linalg.pinv(basis,rcond=1e-10)@v
    m6=market.rolling(6,min_periods=6).sum()
    s336=m6.shift(1).rolling(336,min_periods=336).std(ddof=0)
    impulse=(m6.abs()>2.5*s336)&(s336>0)
    same=(np.sign(r6).eq(np.sign(m6),axis=0)).sum(axis=1)>=3
    loc=((cl-lo)/(hi-lo).where(hi>lo)-.5).mean(axis=1)
    oppose=(np.sign(m6)*loc<0)
    recovery_event=impulse&same&oppose
    rec=_hold_events(np.repeat((-np.sign(m6)).to_numpy(float)[:,None],4,axis=1),
                     np.repeat(recovery_event.to_numpy(float)[:,None],4,axis=1))
    sleeves={'growth':_unit_signed(core),'opportunity':_unit_signed(opp),
             'relative_value':_unit_signed(rv),'recovery':_unit_signed(rec)}
    shadow=_shadow(sleeves,cl,funding)
    shares=_online_shares(shadow,idx)
    states=_regime(market)
    paths={}
    for name in PATHS:
        w=np.zeros((n,4))
        for t in range(n):
            active=[k for k in SHARES if k not in EXCLUDE[name] and np.abs(sleeves[k][t]).sum()>1e-12]
            if not active:continue
            total=sum(shares[k][t] for k in active)
            score=sum((shares[k][t]/total*sleeves[k][t] for k in active),np.zeros(4))
            gross=float(np.abs(score).sum())
            if gross<=1e-12:continue
            v=score*(GROSS[int(states[t])]/gross)
            v=np.clip(v,-.55,.55)
            if abs(v.sum())>.65:v*=.65/abs(v.sum())
            if np.abs(v).sum()>1.40:v*=1.40/np.abs(v).sum()
            w[t]=v
        paths[name]=pd.DataFrame(w,index=idx,columns=ASSETS)
    if diagnostics:
        return paths,{'regime_hours':{str(i):int((states==i).sum()) for i in range(3)},
                      'sleeve_active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum()) for k,v in sleeves.items()},
                      'historical_pnl_computed':False,'validation_2025_read':False,'external_benchmarks_used':False}
    return paths
