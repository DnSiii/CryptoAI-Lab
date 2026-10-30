#!/usr/bin/env python3
"""V98 Independent AA source-only seven-slot portfolio. No historical PnL.
Preregistered Phase1155. Targets at completed t, fills no earlier than t+1.
Only Clean-4 2022-24; no external engines or future validation.
"""
from __future__ import annotations
import hashlib
import io
import numpy as np
import pandas as pd
from phase1156_aa_exit_reserve_governor import gate,allocate

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
CAPITAL={'immediate':10000.,'capacity_1m':1000000.,'capacity_10m':10000000.}
PATHS=('AA_core_only','AA_full','AA_minus_opportunity','AA_minus_relative_value','AA_minus_stress')
SLEEVES=('growth','opportunity','relative_value','stress')
EXCLUDE={'AA_core_only':('opportunity','relative_value','stress'),
         'AA_full':(), 'AA_minus_opportunity':('opportunity',),
         'AA_minus_relative_value':('relative_value',), 'AA_minus_stress':('stress',)}
REBALANCE,REGIME_DWELL=24,72

def validate(op,hi,lo,cl,quote,funding):
    frames=(op,hi,lo,cl,quote,funding)
    if any(not isinstance(x,pd.DataFrame) or tuple(x.columns)!=ASSETS for x in frames):
        raise ValueError('AA1157_CLEAN4_COLUMNS')
    idx=cl.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or len(idx)<850
        or idx[0]<pd.Timestamp('2022-12-01T00:00Z')
        or idx[-1]>=pd.Timestamp('2025-01-01T00:00Z')
        or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h'))
        or any(not x.index.equals(idx) for x in frames)):
        raise ValueError('AA1157_TRAINING_ONLY_CALENDAR')
    if (any(not np.isfinite(x.to_numpy(dtype=float)).all() for x in frames)
        or (op<=0).any().any() or (lo<=0).any().any() or (cl<=0).any().any()
        or (hi<np.maximum(op,cl)).any().any()
        or (lo>np.minimum(op,cl)).any().any() or (quote<0).any().any()):
        raise ValueError('AA1157_BAD_MARKET_DATA')

def norm(a):
    a=np.nan_to_num(np.asarray(a,float),nan=0.,posinf=0.,neginf=0.)
    scale=np.abs(a).sum(axis=1,keepdims=True)
    return np.divide(a,scale,out=np.zeros_like(a),where=scale>1e-14)

def event_hold(direction,trigger,hold=12,lockout=96):
    d=np.asarray(direction,float);b=np.asarray(trigger,bool)
    if d.shape!=b.shape or d.ndim!=2:raise ValueError('AA1157_EVENT_SHAPE')
    out=np.zeros_like(d);until=np.zeros(d.shape[1],int)
    again=np.zeros(d.shape[1],int);held=np.zeros(d.shape[1])
    for t in range(len(d)):
        fresh=b[t]&(d[t]!=0)&(t>=again)
        held[fresh]=d[t,fresh];until[fresh]=t+hold;again[fresh]=t+lockout
        out[t]=np.where(t<until,held,0.)
    return out

def hysteresis(raw,dwell=REGIME_DWELL):
    state=1;until=0;out=np.ones(len(raw),dtype=np.int8)
    for t,v in enumerate(raw):
        if int(v)!=state and t>=until:
            state=int(v);until=t+dwell
        out[t]=state
    return out

def rolling_slope(frame,window=240):
    # Winsorize each hourly return by +/-3 trailing MAD, then rolling OLS.
    returns=frame.diff().fillna(0.)
    med=returns.shift(1).rolling(window,min_periods=window).median()
    mad=(returns.shift(1)-med).abs().rolling(window,min_periods=window).median()
    bound=(3*1.4826*mad).clip(lower=1e-7)
    robust=returns.clip(lower=med-bound,upper=med+bound).fillna(0.).cumsum()
    x=np.arange(window,dtype=float);mean=(window-1)/2
    denom=((x-mean)**2).sum()
    return robust.rolling(window,min_periods=window).apply(
        lambda z:float(np.dot(z,x-mean)/denom),raw=True)

def sleeves_and_router(op,hi,lo,cl,quote,funding):
    validate(op,hi,lo,cl,quote,funding)
    log=np.log(cl);r=log.diff().fillna(0.)
    down=(r.clip(upper=0).pow(2).rolling(240,min_periods=240).mean()).pow(.5)
    slope=rolling_slope(log);accel=slope-slope.shift(48)
    growth=norm((slope+2*accel).to_numpy()/np.maximum(down.to_numpy(),1e-6))
    # Opportunity: 6h dislocation AND observed signed funding reversal.
    lastfund=funding.replace(0.,np.nan).ffill();previous=lastfund.shift(1)
    reversal=(funding!=0)&(previous.notna())&(np.sign(funding)!=np.sign(previous))
    ret6=log-log.shift(6)
    robust_scale=(r.abs().rolling(240,min_periods=240).median()*1.4826*np.sqrt(6)).clip(lower=1e-8)
    disloc=ret6/robust_scale
    direction=-np.sign(disloc.to_numpy(float))
    agree=(np.sign(funding.to_numpy(float))==np.sign(disloc.to_numpy(float)))
    eligible=reversal.to_numpy(bool)&agree&(np.abs(disloc.to_numpy(float))>=2.)
    opportunity=norm(event_hold(direction,eligible))
    # Relative-value: 240h factor residual and 336h prior beta neutrality.
    market=r.mean(axis=1)
    mvar=market.rolling(240,min_periods=240).var(ddof=0).clip(lower=1e-12)
    beta=r.rolling(240,min_periods=240).cov(market).div(mvar,axis=0)
    residual=r-beta.mul(market,axis=0)
    residual_sum=residual.rolling(240,min_periods=240).sum()
    residual_std=residual.rolling(240,min_periods=240).std(ddof=0).clip(lower=1e-8)*np.sqrt(240)
    z=(residual_sum/residual_std).to_numpy(float)
    prior_beta=beta.shift(1).rolling(336,min_periods=336).mean().to_numpy(float)
    rv=np.zeros_like(z)
    for t in range(len(rv)):
        if not np.isfinite(z[t]).all() or not np.isfinite(prior_beta[t]).all():continue
        a=int(np.argmin(z[t]));b=int(np.argmax(z[t]))
        if a==b or z[t,a]>=0 or z[t,b]<=0:continue
        x,y=prior_beta[t,a],prior_beta[t,b]
        if x*y<=1e-12:continue
        rv[t,a]=abs(y)/(abs(x)+abs(y));rv[t,b]=-abs(x)/(abs(x)+abs(y))
    relative=norm(rv)
    # Stress: 96h correlation breakdown + 24h negative breadth.
    corr=r.rolling(96,min_periods=96).corr()
    mean_corr=np.full(len(r),np.nan)
    for t in range(95,len(r)):
        matrix=corr.loc[r.index[t]].to_numpy(float)
        mean_corr[t]=np.mean(matrix[np.triu_indices(4,1)])
    breadth=((log-log.shift(24))<0).sum(axis=1).to_numpy()
    breakdown=(mean_corr<.2)&(breadth>=3)
    normalized=(mean_corr>.5)&(breadth<=1)
    stress=np.zeros_like(rv);state=False
    for t in range(len(stress)):
        if breakdown[t]:state=True
        elif normalized[t]:state=False
        if state:
            b=np.maximum(prior_beta[t],0.)
            if np.isfinite(b).all() and b.sum()>1e-10:stress[t]=-b/b.sum()
    # Router: 336h correlation, vol-of-vol, 72h dwell.
    corr336=r.rolling(336,min_periods=336).corr()
    corr_avg=np.full(len(r),np.nan)
    for t in range(335,len(r)):
        matrix=corr336.loc[r.index[t]].to_numpy(float)
        corr_avg[t]=np.mean(matrix[np.triu_indices(4,1)])
    v24=r.rolling(24,min_periods=24).std(ddof=0).mean(axis=1)
    vov=v24.rolling(336,min_periods=336).std(ddof=0).to_numpy()
    raw=np.where((corr_avg>.75)&(vov>.002),0,
          np.where((corr_avg<.5)&(vov<=.002),2,1))
    regimes=hysteresis(raw)
    return {'growth':growth,'opportunity':opportunity,
            'relative_value':relative,'stress':stress},regimes,r

def prior_bounds(cl,hi,lo,funding):
    prev=cl.shift(1)
    dn=(1-lo/prev).clip(lower=0).rolling(336,min_periods=336).max()
    up=(hi/prev-1).clip(lower=0).rolling(336,min_periods=336).max()
    fb=funding.abs().rolling(720,min_periods=720).max()
    return dn.to_numpy(float),up.to_numpy(float),fb.to_numpy(float)

def compose_aa(op,hi,lo,cl,quote,funding,*,diagnostics=False):
    sleeves,regime,r=sleeves_and_router(op,hi,lo,cl,quote,funding)
    n=len(cl);dn,up,fb=prior_bounds(cl,hi,lo,funding)
    min72=quote.rolling(72,min_periods=72).min().to_numpy(float)
    q=quote.to_numpy(float);rr=r.to_numpy(float)
    weights=np.array([[.3,.4,1.3,1.5],[1.,1.,1.,1.],[1.5,1.2,.8,.5]])
    cov=[None]*n
    for t in range(720,n):cov[t]=np.cov(rr[t-239:t+1],rowvar=False,ddof=0)*24
    result={};calls={};events=np.any(sleeves['opportunity']!=0,axis=1)
    for mode,capital in CAPITAL.items():
        for path in PATHS:
            target=np.zeros((n,4));last=np.zeros(4);count=0
            for t in range(720,n):
                transition=events[t]!=events[t-1]
                if t%REBALANCE==0 or (path not in ('AA_core_only','AA_minus_opportunity') and transition):
                    scales=np.array([weights[regime[t],j] if k not in EXCLUDE[path]
                                     else 0. for j,k in enumerate(SLEEVES)])
                    blend=sum(scales[j]*sleeves[k][t] for j,k in enumerate(SLEEVES))
                    alpha=.012*blend/max(scales.sum(),1.)
                    if all(np.isfinite(x[t]).all() for x in (dn,up,fb,min72)):
                        last=allocate(alpha,cov[t],last,dn[t],up[t],fb[t],q[t],min72[t],capital)
                        count+=1
                if all(np.isfinite(x[t]).all() for x in (dn,up,fb,min72)):
                    if not gate(last,last,dn[t],up[t],fb[t],q[t],min72[t],capital):
                        last=allocate(np.zeros(4),cov[t],last,dn[t],up[t],fb[t],q[t],min72[t],capital)
                        count+=1
                target[t]=last
            result[path,mode]=pd.DataFrame(target,index=cl.index,columns=ASSETS)
            calls[path,mode]=count
    if diagnostics:
        return result,{'source_only':True,'historical_pnl_computed':False,
            'validation_2025_read':False,'external_benchmarks_used':False,
            't_plus_one_execution':True,'governor_calls':calls,
            'regime_hours':{str(i):int((regime==i).sum()) for i in range(3)},
            'sleeve_active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum()) for k,v in sleeves.items()}}
    return result

def canonical_hash(frame):
    a=frame.to_numpy(float)
    if a.shape[1]!=4 or not np.isfinite(a).all():raise ValueError('AA1157_HASH_SHAPE')
    raw=frame.to_csv(float_format='%.6f',lineterminator='\n').encode()
    if not np.array_equal(pd.read_csv(io.BytesIO(raw),index_col=0).to_numpy(float),a):
        raise ValueError('AA1157_HASH_PRECISION')
    return hashlib.sha256(raw).hexdigest()
