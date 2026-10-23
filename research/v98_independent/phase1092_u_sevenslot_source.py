#!/usr/bin/env python3
"""V98 U seven-slot causal target source; UNFROZEN; NO HISTORICAL PNL."""
from __future__ import annotations
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS=('U_core_only','U_full','U_minus_opportunity','U_minus_relative_value','U_minus_stress')
SLEEVES=('growth','opportunity','relative_value','stress')
EXCLUDE={'U_core_only':('opportunity','relative_value','stress'),
         'U_full':(),'U_minus_opportunity':('opportunity',),
         'U_minus_relative_value':('relative_value',),'U_minus_stress':('stress',)}
BUDGET=np.array([[.20,.10,.20,.50],[.55,.15,.20,.10],[.65,.20,.10,.05]])
ASSET_CAP=.45;NET_CAP=.75;GROSS_CAP=1.35

def validate(op,hi,lo,cl,quote,funding):
    frames=(op,hi,lo,cl,quote,funding)
    if any(not isinstance(f,pd.DataFrame) or tuple(f.columns)!=ASSETS for f in frames):
        raise ValueError('U_CLEAN4_REQUIRED')
    idx=cl.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or
        len(idx)<1800 or idx[0]<pd.Timestamp('2022-12-01T00:00Z') or
        idx[-1]>=pd.Timestamp('2025-01-01T00:00Z') or
        not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h')) or
        any(not idx.equals(f.index) for f in frames)):
        raise ValueError('U_CHRONOLOGICAL_TRAINING_ONLY')
    if any(not np.isfinite(f.to_numpy(float)).all() for f in frames):
        raise ValueError('U_NONFINITE_SOURCE')
    if ((op<=0).any().any() or (lo<=0).any().any() or
        (quote<0).any().any() or (hi<np.maximum(op,cl)).any().any() or
        (lo>np.minimum(op,cl)).any().any()):
        raise ValueError('U_INVALID_OHLC')

def normalize_signed(x):
    a=np.nan_to_num(np.asarray(x,float),nan=0.,posinf=0.,neginf=0.)
    gross=np.abs(a).sum(axis=1,keepdims=True)
    return np.divide(a,gross,out=np.zeros_like(a),where=gross>1e-12)

def governor(raw):
    a=np.asarray(raw,float)
    if a.ndim!=2 or a.shape[1]!=4 or not np.isfinite(a).all():
        raise ValueError('U_TARGET_NONFINITE_OR_SHAPE')
    gross=np.abs(a).sum(axis=1);asset=np.abs(a).max(axis=1);net=np.abs(a.sum(axis=1))
    scale=np.minimum.reduce([np.ones(len(a)),
        (GROSS_CAP-2e-5)/np.maximum(gross,1e-12),
        (ASSET_CAP-2e-5)/np.maximum(asset,1e-12),
        (NET_CAP-2e-5)/np.maximum(net,1e-12)])
    out=np.round(a*scale[:,None],6)
    if (np.abs(out).max()>ASSET_CAP+1e-10 or
        np.abs(out).sum(axis=1).max()>GROSS_CAP+1e-10 or
        np.abs(out.sum(axis=1)).max()>NET_CAP+1e-10):
        raise AssertionError('U_SERIALIZED_TARGET_CAP')
    return out

def hysteresis(desired,hours=48,default=1):
    out=np.full(len(desired),default,dtype=np.int8)
    state=default;next_switch=0
    for i,d in enumerate(desired):
        d=int(d)
        if d!=state and i>=next_switch:
            state=d;next_switch=i+hours
        out[i]=state
    return out

def fixed_event_hold(raw,event,hold,cooldown):
    a=np.nan_to_num(np.asarray(raw,float),nan=0.,posinf=0.,neginf=0.)
    e=np.asarray(event,bool)
    if a.shape!=e.shape or a.ndim!=2:raise ValueError('U_EVENT_GEOMETRY')
    n,k=a.shape;out=np.zeros_like(a);remaining=np.zeros(k,int)
    blocked=np.zeros(k,int);last=np.zeros(k)
    for t in range(n):
        trigger=e[t]&(blocked==0)&(a[t]!=0)
        last[trigger]=a[t,trigger];remaining[trigger]=hold;blocked[trigger]=cooldown
        out[t]=np.where(remaining>0,last,0.)
        remaining=np.maximum(0,remaining-1);blocked=np.maximum(0,blocked-1)
    return out

def compose_u(op,hi,lo,cl,quote,funding,*,diagnostics=False):
    validate(op,hi,lo,cl,quote,funding)
    idx=cl.index;n=len(idx);log=np.log(cl);r=log.diff().fillna(0.)
    m=r.mean(axis=1);vol168=r.rolling(168,min_periods=168).std(ddof=0)
    # Growth: 336h signed channel, 72h persistence, 168h vol scaling.
    prior_hi=hi.shift(1).rolling(336,min_periods=336).max()
    prior_lo=lo.shift(1).rolling(336,min_periods=336).min()
    dir72=np.sign(log-log.shift(72))
    breakout=np.where((cl>prior_hi)&(dir72>0),1.,
             np.where((cl<prior_lo)&(dir72<0),-1.,0.))
    direction=np.zeros((n,4))
    for t in range(1,n):
        new=breakout[t]
        direction[t]=np.where(new!=0,new,
                        np.where(dir72.iloc[t].to_numpy()*direction[t-1]>0,direction[t-1],0.))
    v=vol168.to_numpy(float)
    growth=normalize_signed(direction/np.maximum(v,1e-5))
    # Opportunity: volatility acceleration, quote shock, 24h continuation.
    v8=r.rolling(8,min_periods=8).std(ddof=0)
    v168=r.rolling(168,min_periods=168).std(ddof=0)
    qbaseline=quote.shift(1).rolling(24,min_periods=24).mean()
    qshock=quote/qbaseline.replace(0,np.nan)
    cont=np.sign(log-log.shift(24))
    event=((v8>v168)&(qshock>1)&(cont!=0)).fillna(False).to_numpy(bool)
    opportunity=normalize_signed(fixed_event_hold(cont.to_numpy(float),event,24,72))
    # Relative value: 336h beta, 24h idiosyncratic momentum, 48h hold.
    market_var=m.rolling(336,min_periods=336).var(ddof=0)
    beta=r.rolling(336,min_periods=336).cov(m,ddof=0).div(market_var,axis=0)
    residual=(log-log.shift(24)).sub(beta.mul(m.rolling(24,min_periods=24).sum(),axis=0))
    scores=residual.to_numpy(float);betas=beta.to_numpy(float)
    rv_raw=np.zeros((n,4));next_allowed=0;pair=np.zeros(4)
    for t in range(n):
        if t>=next_allowed:
            pair=np.zeros(4)
            if t>=336 and np.isfinite(scores[t]).all() and np.isfinite(betas[t]).all():
                winner=int(np.argmax(scores[t]));loser=int(np.argmin(scores[t]))
                bw,bl=betas[t,winner],betas[t,loser]
                if winner!=loser and bw>0 and bl>0 and scores[t,winner]>scores[t,loser]:
                    pair[winner]=bl/(bw+bl);pair[loser]=-bw/(bw+bl)
            next_allowed=t+48
        rv_raw[t]=pair
    relative_value=normalize_signed(rv_raw)
    # Stress/recovery: 24h breadth and 72h downside vs prior 720h median.
    ret24=log-log.shift(24)
    neg_breadth=(ret24<0).sum(axis=1);pos_breadth=(ret24>0).sum(axis=1)
    downside=np.sqrt(r.clip(upper=0).pow(2).mean(axis=1).rolling(72,min_periods=72).mean())
    baseline=downside.shift(1).rolling(720,min_periods=720).median()
    stress_raw=np.where((neg_breadth>=3)&(downside>baseline),0,
               np.where((pos_breadth>=3)&(downside<baseline),2,1))
    stress_state=hysteresis(stress_raw,72,default=1)
    stress=np.zeros((n,4))
    for t in range(n):
        if stress_state[t]==0:stress[t]=-.25
        elif stress_state[t]==2:stress[t]=.25
    # Router: breadth, lagged cross-correlation and downside ratio.
    corr=[r[a].rolling(336,min_periods=336).corr(r[b]).shift(1)
          for i,a in enumerate(ASSETS) for b in ASSETS[i+1:]]
    mean_corr=pd.concat(corr,axis=1).mean(axis=1)
    d_ratio=downside/baseline.replace(0,np.nan)
    desired=np.where((neg_breadth>=3)&(d_ratio>1)&(mean_corr>.35),0,
            np.where((pos_breadth>=3)&(d_ratio<1)&(mean_corr<.75),2,1))
    states=hysteresis(desired,48,default=1)
    sleeves={'growth':growth,'opportunity':opportunity,'relative_value':relative_value,'stress':stress}
    # Allocator: 8h decisions, 48h persistence, prior-only funding headroom.
    funding_drag=funding.abs().rolling(72,min_periods=1).mean().mean(axis=1)
    headroom=(1-np.minimum(.4,100*funding_drag)).to_numpy(float)
    confidence=np.minimum(1.,np.maximum(.25,np.abs((log-log.shift(72)).to_numpy(float))/
                              np.maximum(v*np.sqrt(72),1e-5)))
    confidence=np.nan_to_num(confidence,nan=.25,posinf=1.,neginf=.25)
    paths={}
    for name in PATHS:
        target=np.zeros((n,4));last=np.zeros(4);expiry=0
        for t in range(n):
            if t%8==0:
                raw=np.zeros(4)
                for j,sleeve in enumerate(SLEEVES):
                    if sleeve not in EXCLUDE[name] and np.abs(sleeves[sleeve][t]).sum()>1e-12:
                        raw+=BUDGET[states[t],j]*sleeves[sleeve][t]*confidence[t]
                raw*=headroom[t]
                proposed=governor(raw[None,:])[0]
                if np.any(proposed):last=proposed;expiry=t+48
                elif t>=expiry:last=np.zeros(4)
            target[t]=last
        paths[name]=pd.DataFrame(target,index=idx,columns=ASSETS)
    if diagnostics:
        return paths,{'regime_hours':{str(s):int((states==s).sum()) for s in range(3)},
                      'active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum()) for k,v in sleeves.items()},
                      'historical_pnl_computed':False,'validation_2025_read':False,
                      'holdout_accessed':False,'external_benchmarks_used':False,
                      'contingent_order_validation_required':True}
    return paths
