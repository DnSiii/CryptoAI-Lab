#!/usr/bin/env python3
"""V98 AB independent seven-slot INTENTS, not fixed-NAV weights. Source only.
Decisions on completed Clean-4 t, actual-NAV allocation must execute at t+1.
No 2025 validation, XRP, historical PnL, or external engine dependency.
"""
from __future__ import annotations
import hashlib,io
import numpy as np
import pandas as pd
ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
CAPITAL={'immediate':10000.,'capacity_1m':1e6,'capacity_10m':1e7}
PATHS=('AB_core_only','AB_full','AB_minus_opportunity','AB_minus_relative_value','AB_minus_stress')
SLEEVES=('growth','opportunity','relative_value','stress')
EXCLUDE={'AB_core_only':('opportunity','relative_value','stress'),
         'AB_full':(),'AB_minus_opportunity':('opportunity',),
         'AB_minus_relative_value':('relative_value',),'AB_minus_stress':('stress',)}

def validate(op,hi,lo,cl,q,funding):
    f=(op,hi,lo,cl,q,funding)
    if any(not isinstance(x,pd.DataFrame) or tuple(x.columns)!=ASSETS for x in f):
        raise ValueError('AB1163_CLEAN4_COLUMNS')
    idx=cl.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or len(idx)<900
        or idx[0]<pd.Timestamp('2022-12-01T00:00Z')
        or idx[-1]>=pd.Timestamp('2025-01-01T00:00Z')
        or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h'))
        or any(not x.index.equals(idx) for x in f)):
        raise ValueError('AB1163_TRAINING_ONLY_CALENDAR')
    if (any(not np.isfinite(x.to_numpy(float)).all() for x in f)
        or (op<=0).any().any() or (lo<=0).any().any() or (cl<=0).any().any()
        or (hi<np.maximum(op,cl)).any().any() or (lo>np.minimum(op,cl)).any().any()
        or (q<0).any().any()):raise ValueError('AB1163_BAD_SOURCE')

def normalize(x):
    a=np.nan_to_num(np.asarray(x,float),nan=0.,posinf=0.,neginf=0.)
    n=np.abs(a).sum(axis=1,keepdims=True)
    return np.divide(a,n,out=np.zeros_like(a),where=n>1e-14)

def event_hold(direction,eligible,hold=24,lockout=120):
    d=np.asarray(direction,float);b=np.asarray(eligible,bool)
    if d.shape!=b.shape or d.ndim!=2:raise ValueError('AB1163_EVENT_SHAPE')
    out=np.zeros_like(d);until=np.zeros(d.shape[1],int);again=np.zeros(d.shape[1],int)
    active=np.zeros(d.shape[1])
    for t in range(len(d)):
        trigger=b[t]&(d[t]!=0)&(t>=again)
        active[trigger]=d[t,trigger];until[trigger]=t+hold;again[trigger]=t+lockout
        out[t]=np.where(t<until,active,0.)
    return out

def regime_dwell(raw,dwell=96):
    state=1;until=0;out=np.ones(len(raw),np.int8)
    for t,v in enumerate(raw):
        if int(v)!=state and t>=until:state=int(v);until=t+dwell
        out[t]=state
    return out

def four_sleeves(op,hi,lo,cl,q,funding):
    validate(op,hi,lo,cl,q,funding)
    log=np.log(cl);r=log.diff().fillna(0.)
    vol24=r.rolling(24,min_periods=24).std(ddof=0).clip(lower=1e-8)
    vol168=r.rolling(168,min_periods=168).std(ddof=0).clip(lower=1e-8)
    vol336=r.rolling(336,min_periods=336).std(ddof=0).clip(lower=1e-8)
    down=r.clip(upper=0).pow(2).rolling(336,min_periods=336).mean().pow(.5).clip(lower=1e-8)
    # Growth: 24/96/336 signed agreement, scaled by downside persistence.
    r24=log-log.shift(24);r96=log-log.shift(96);r336=log-log.shift(336)
    agree=(np.sign(r24)==np.sign(r96))&(np.sign(r96)==np.sign(r336))
    trend=np.sign(r336)*(r24.abs()/np.sqrt(24)+r96.abs()/np.sqrt(96)+r336.abs()/np.sqrt(336))/down
    growth=normalize(trend.where(agree,0.).to_numpy(float))
    # Opportunity: prior 24h compression and subsequent 12h range expansion.
    compressed=(vol24.shift(12)<.7*vol336.shift(12))
    r12=log-log.shift(12)
    expansion=(r12.abs()>1.5*vol24.shift(12)*np.sqrt(12))
    persistent=np.sign(r12)==np.sign(log-log.shift(6))
    opportunity=normalize(event_hold(np.sign(r12.to_numpy(float)),
                       (compressed&expansion&persistent).fillna(False).to_numpy(bool)))
    # RV: alt/BTC 336h log spread with 96h negative error-correction slope.
    btc=log['BTCUSDT'];v=btc.rolling(336,min_periods=336).var(ddof=0).clip(lower=1e-12)
    beta=log.rolling(336,min_periods=336).cov(btc).div(v,axis=0)
    spread=log-beta.mul(btc,axis=0)
    lag=spread.shift(1);change=spread.diff()
    lagvar=lag.rolling(96,min_periods=96).var(ddof=0).clip(lower=1e-12)
    ec=change.rolling(96,min_periods=96).cov(lag).div(lagvar,axis=0)
    center=spread.shift(1).rolling(336,min_periods=336).mean()
    scale=spread.shift(1).rolling(336,min_periods=336).std(ddof=0).clip(lower=1e-8)
    z=(spread-center)/scale
    rv=np.zeros((len(log),4))
    for j in range(1,4):
        eligible=(ec.iloc[:,j]<-.01)&(z.iloc[:,j].abs()>1.)
        alt=np.where(eligible,-np.sign(z.iloc[:,j]),0.)
        b=beta.iloc[:,j].to_numpy(float)
        good=np.isfinite(b)&(b>0)
        rv[:,j]+=np.where(good,alt,0.)
        rv[:,0]-=np.where(good,alt*b,0.)
    relative=normalize(rv)
    # Stress: 48h synchronized downside co-jumps, 72h recovery confirmation.
    r48=log-log.shift(48)
    tail=r48.abs().shift(1).rolling(336,min_periods=336).quantile(.9).clip(lower=1e-8)
    breadth=(r48< -1.5*tail).sum(axis=1).to_numpy()
    recovery=((log-log.shift(72))>0).sum(axis=1).to_numpy()
    vol_ratio=(vol24/vol168).median(axis=1).to_numpy()
    stress=np.zeros_like(rv);state=False
    for t in range(len(rv)):
        if breadth[t]>=3:state=True
        elif recovery[t]>=3 and np.isfinite(vol_ratio[t]) and vol_ratio[t]<.9:state=False
        if state:
            inv=1/np.maximum(vol168.iloc[t].to_numpy(float),1e-8)
            stress[t]=-inv/inv.sum()
    # Router: 336h dispersion, 24/168h volatility ratio, 96h dwell.
    dispersion=r.rolling(336,min_periods=336).std(ddof=0).std(axis=1)
    baseline=dispersion.shift(1).rolling(336,min_periods=336).median()
    raw=np.where((vol_ratio>1.5)&(dispersion>baseline),0,
          np.where((vol_ratio<.9)&(dispersion<=baseline),2,1))
    return {'growth':growth,'opportunity':opportunity,
            'relative_value':relative,'stress':normalize(stress)},regime_dwell(raw)

def compose_ab_intents(op,hi,lo,cl,q,funding,*,diagnostics=False):
    sleeves,regime=four_sleeves(op,hi,lo,cl,q,funding)
    n=len(cl);qmin=q.rolling(336,min_periods=336).min().to_numpy(float)
    weights=np.array([[.4,.5,1.1,1.5],[1.,1.,1.,1.],[1.6,1.2,.8,.4]])
    result={};counts={}
    for mode,capital in CAPITAL.items():
        liquidity=np.clip(.0025*qmin/capital,0,1.)
        for path in PATHS:
            out=np.zeros((n,4))
            for t in range(720,n):
                scales=np.array([weights[regime[t],j] if k not in EXCLUDE[path]
                                 else 0. for j,k in enumerate(SLEEVES)])
                combined=sum(scales[j]*sleeves[k][t] for j,k in enumerate(SLEEVES))
                out[t]=.012*combined/max(scales.sum(),1.)*liquidity[t]
            result[path,mode]=pd.DataFrame(out,index=cl.index,columns=ASSETS)
            counts[path,mode]=int(np.count_nonzero(np.abs(out).sum(axis=1)))
    if diagnostics:
        return result,{'source_only':True,'historical_pnl_computed':False,
            'validation_2025_read':False,'external_benchmarks_used':False,
            'stateful_nav_execution_required':True,'t_plus_one_execution':True,
            'nonzero_intent_hours':counts,
            'regime_hours':{str(i):int((regime==i).sum()) for i in range(3)},
            'sleeve_active_hours':{k:int(np.count_nonzero(np.abs(v).sum(axis=1))) for k,v in sleeves.items()}}
    return result

def canonical_hash(frame):
    x=frame.to_numpy(float)
    if x.shape[1]!=4 or not np.isfinite(x).all():raise ValueError('AB1163_HASH_SHAPE')
    raw=frame.to_csv(float_format='%.10f',lineterminator='\n').encode()
    if not np.allclose(pd.read_csv(io.BytesIO(raw),index_col=0).to_numpy(float),x,rtol=0,atol=5e-11):
        raise ValueError('AB1163_HASH_PRECISION')
    return hashlib.sha256(raw).hexdigest()
