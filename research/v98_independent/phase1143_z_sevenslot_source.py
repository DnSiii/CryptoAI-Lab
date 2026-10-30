#!/usr/bin/env python3
"""V98 Independent Z: preregistered seven-slot capital-aware targets; NO historical PnL.

Training scope: Dec-2022 warmup, Jan-2023--Dec-2024 only. At timestamp t
only observations through t enter targets[t]; any fills belong to t+1.
This source does not inspect other engines, validation, or economic receipts.
"""
from __future__ import annotations
import hashlib
import io
import itertools
import numpy as np
import pandas as pd

ASSETS = ('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS = ('Z_core_only','Z_full','Z_minus_opportunity','Z_minus_relative_value','Z_minus_stress')
CAPITAL = {'immediate':10_000.,'capacity_1m':1_000_000.,'capacity_10m':10_000_000.}
SLEEVES = ('growth','opportunity','relative_value','stress')
EXCLUDE = {'Z_core_only':('opportunity','relative_value','stress'),
           'Z_full':(), 'Z_minus_opportunity':('opportunity',),
           'Z_minus_relative_value':('relative_value',), 'Z_minus_stress':('stress',)}
CORNERS = np.array(tuple(itertools.product(range(3), repeat=4)),dtype=int)
ASSET_CAP,NET_CAP,GROSS_CAP,FLOOR,PARTICIPATION = .45,.75,1.35,.25,.01
SLIPPAGE,BASE_FEE,REBALANCE,MIN_DWELL = .002,.0007,12,48

def validate(op,hi,lo,cl,quote,funding):
    fs=(op,hi,lo,cl,quote,funding)
    if any(not isinstance(x,pd.DataFrame) or tuple(x.columns)!=ASSETS for x in fs):
        raise ValueError('Z1143_CLEAN4_COLUMNS')
    idx=cl.index
    if (not isinstance(idx,pd.DatetimeIndex) or idx.tz is None or len(idx)<800
        or idx[0]<pd.Timestamp('2022-12-01T00:00Z')
        or idx[-1]>=pd.Timestamp('2025-01-01T00:00Z')
        or not idx.equals(pd.date_range(idx[0],periods=len(idx),freq='h'))
        or any(not x.index.equals(idx) for x in fs)):
        raise ValueError('Z1143_TRAINING_ONLY_CALENDAR')
    if (any(not np.isfinite(x.to_numpy(float)).all() for x in fs)
        or (op<=0).any().any() or (cl<=0).any().any() or (lo<=0).any().any()
        or (hi<np.maximum(op,cl)).any().any()
        or (lo>np.minimum(op,cl)).any().any() or (quote<0).any().any()):
        raise ValueError('Z1143_INVALID_SOURCE')

def normalize(x):
    a=np.nan_to_num(np.asarray(x,float),nan=0.,posinf=0.,neginf=0.)
    s=np.sum(np.abs(a),axis=1,keepdims=True)
    return np.divide(a,s,out=np.zeros_like(a),where=s>1e-12)

def hysteresis(raw,dwell=MIN_DWELL):
    out=np.ones(len(raw),np.int8);state=1;next_switch=0
    for t,v in enumerate(raw):
        if int(v)!=state and t>=next_switch:
            state=int(v);next_switch=t+dwell
        out[t]=state
    return out

def event_hold(direction,eligible,hold_hours=16,lockout=72):
    direction=np.asarray(direction,float);eligible=np.asarray(eligible,bool)
    if direction.shape!=eligible.shape or direction.ndim!=2:
        raise ValueError('Z1143_EVENT_GEOMETRY')
    n,k=direction.shape;out=np.zeros((n,k));until=np.zeros(k,int)
    eligible_again=np.zeros(k,int);held=np.zeros(k)
    for t in range(n):
        trigger=eligible[t]&(t>=eligible_again)&(direction[t]!=0)
        held[trigger]=direction[t,trigger]
        until[trigger]=t+hold_hours
        eligible_again[trigger]=t+lockout
        out[t]=np.where(t<until,held,0.)
    return out

def beta_neutral(long_beta,short_beta):
    if not np.isfinite(long_beta+short_beta) or long_beta*short_beta<=1e-12:
        return None
    a,b=abs(long_beta),abs(short_beta)
    return b/(a+b),-a/(a+b)

def sleeves_and_regimes(op,hi,lo,cl,quote,funding):
    validate(op,hi,lo,cl,quote,funding)
    n=len(cl);log=np.log(cl);r=log.diff().fillna(0.)
    downside=np.sqrt(r.clip(upper=0).pow(2).rolling(168,min_periods=168).mean())
    # 1. Donchian breakout with 48h efficiency, downside-vol sizing.
    high168=hi.shift(1).rolling(168,min_periods=168).max()
    low168=lo.shift(1).rolling(168,min_periods=168).min()
    signed=((cl>high168).astype(int)-(cl<low168).astype(int)).to_numpy(float)
    eff=(log-log.shift(48)).abs()/r.abs().rolling(48,min_periods=48).sum().clip(lower=1e-12)
    growth=normalize(signed*eff.to_numpy(float)/np.maximum(downside.to_numpy(float),1e-6))
    # 2. 24h range escape + robust 168h quote impulse; event 16h/lockout 72h.
    q24=quote.rolling(24,min_periods=24).sum()
    med=q24.shift(1).rolling(168,min_periods=168).median()
    mad=(q24.shift(1)-med).abs().rolling(168,min_periods=168).median()
    impulse=(q24-med)/np.maximum(1.4826*mad,1e-12)
    breakout=((cl>hi.shift(1).rolling(24,min_periods=24).max()).astype(int)
             -(cl<lo.shift(1).rolling(24,min_periods=24).min()).astype(int))
    eligible=(impulse>1.5).fillna(False).to_numpy(bool)
    opportunity=normalize(event_hold(breakout.to_numpy(float),eligible))
    # 3. Funding-dispersion carry; signed funding >0 paid by longs.
    carry=funding.rolling(168,min_periods=168).mean().to_numpy(float)
    btc=r['BTCUSDT'].shift(1)
    btcvar=btc.rolling(336,min_periods=336).var(ddof=0).clip(lower=1e-12)
    beta=r.shift(1).rolling(336,min_periods=336).cov(btc).div(btcvar,axis=0).to_numpy(float)
    rv=np.zeros((n,4))
    for t in range(n):
        if np.isfinite(carry[t]).all() and np.isfinite(beta[t]).all() and np.ptp(carry[t])>1e-15:
            long=int(np.argmin(carry[t]));short=int(np.argmax(carry[t]))
            pair=beta_neutral(beta[t,long],beta[t,short])
            if pair is not None:
                rv[t,long],rv[t,short]=pair
    relative_value=normalize(rv)
    # 4. Prior 12h breadth crash hedge, separate causal 72h reclaim.
    market12=r.mean(axis=1).rolling(12,min_periods=12).sum()
    shock_ref=market12.abs().shift(1).rolling(168,min_periods=168).median()
    breadth12=((log-log.shift(12))>0).sum(axis=1)
    breadth72=((log-log.shift(72))>0).sum(axis=1)
    crash=((market12 < -2*shock_ref)&(breadth12<=1)).fillna(False)
    reclaim=((cl>hi.shift(1).rolling(72,min_periods=72).max()).sum(axis=1)>=3)&(breadth72>=3)
    inv=1/np.maximum(downside.to_numpy(float),1e-6)
    stress=normalize(np.where(crash.to_numpy()[:,None],-inv,
                      np.where(reclaim.to_numpy()[:,None],inv,0.)))
    # 5. Three regimes: 168h volatility median, 72h breadth, 48h dwell.
    vol=r.rolling(168,min_periods=168).std(ddof=0).median(axis=1)
    baseline=vol.shift(1).rolling(336,min_periods=336).median()
    raw=np.where((vol>1.5*baseline)&(breadth72<=1),0,
          np.where((vol<=baseline)&(breadth72>=3),2,1))
    regime=hysteresis(raw)
    return {'growth':growth,'opportunity':opportunity,
            'relative_value':relative_value,'stress':stress},regime,r

def prior_adverse_bounds(cl,hi,lo,funding):
    """All t shock bounds are historical and observable by end of t."""
    prev=cl.shift(1)
    down=(1-lo/prev).clip(lower=0).rolling(336,min_periods=336).max()
    up=(hi/prev-1).clip(lower=0).rolling(336,min_periods=336).max()
    fund=funding.abs().rolling(720,min_periods=720).max()
    return down.to_numpy(float),up.to_numpy(float),fund.to_numpy(float)

def corner_gate(w,down,up,funding_bound,prior_w=None,margin=1.):
    """Pretrade 81-corner self-financing conservative weight gate.

    Prior equity normalized to 1. All 81 adverse price corners and worst
    funding debit included; transaction costs paid before mark stress.
    """
    w=np.asarray(w,float);d=np.asarray(down,float);u=np.asarray(up,float)
    f=np.asarray(funding_bound,float)
    old=np.zeros(4) if prior_w is None else np.asarray(prior_w,float)
    if any(x.shape!=(4,) or not np.isfinite(x).all() for x in (w,d,u,f,old)):
        return False
    if (d<0).any() or (d>=1).any() or (u<0).any() or (f<0).any():return False
    if np.max(np.abs(w))>ASSET_CAP*margin+1e-10 or np.sum(np.abs(w))>GROSS_CAP*margin+1e-10 or abs(w.sum())>NET_CAP*margin+1e-10:
        return False
    friction=(SLIPPAGE+BASE_FEE)*np.sum(np.abs(w-old))
    debit=np.sum(np.abs(w)*f)
    prices=np.stack((1-d,np.ones(4),1+u),axis=0)[CORNERS,np.arange(4)]
    exposures=prices*w
    equity=1+np.sum(exposures-w,axis=1)-friction-debit
    return bool(np.all(equity>=FLOOR-1e-10) and
       np.all(np.abs(exposures)<=ASSET_CAP*margin*equity[:,None]+1e-10) and
       np.all(np.abs(exposures).sum(axis=1)<=GROSS_CAP*margin*equity+1e-10) and
       np.all(np.abs(exposures.sum(axis=1))<=NET_CAP*margin*equity+1e-10))

def optimize_joint(alpha,cov,prior_w,down,up,funding_bound,quote,capital):
    """Fixed 12-step deterministic joint log-growth surrogate + hard feasibility.

    2nd-order Taylor of expected log(1+portfolio return) net of friction,
    adverse native funding, and turnover. The optimizer has no CAGR ceiling.
    Capital-native 1% quote participation constrains turnover per asset.
    """
    mu=np.asarray(alpha,float);sigma=np.asarray(cov,float)
    old=np.asarray(prior_w,float);q=np.asarray(quote,float)
    if (mu.shape!=(4,) or sigma.shape!=(4,4) or old.shape!=(4,) or
        q.shape!=(4,) or not np.isfinite(mu).all() or
        not np.isfinite(sigma).all() or not np.isfinite(q).all() or (q<0).any()
        or capital<=0 or not np.isfinite(capital)):
        raise ValueError('Z1143_ALLOCATOR_INPUT')
    # A fixed 80% participation budget leaves a 20% execution-gap reserve.
    turnover_cap=.8*PARTICIPATION*q/(capital*(1+SLIPPAGE))
    base=old.copy()
    if not corner_gate(old,down,up,funding_bound,old):
        # Phase1149 preregistered pre-PnL inventory-first reduce-only feedback.
        # No risk-cap relaxation and no impossible liquidity assumption.
        if not corner_gate(np.zeros(4),down,up,funding_bound,old):
            raise ValueError('Z1149_NO_FEASIBLE_REDUCE_ONLY_BASE')
        left,right=0.,1.
        for _ in range(24):
            mid=(left+right)/2
            if corner_gate(old*mid,down,up,funding_bound,old,margin=.98):left=mid
            else:right=mid
        base=old*left
        if np.any(np.abs(base-old)>turnover_cap+1e-10):
            raise ValueError('Z1149_UNEXECUTABLE_PRIOR_INVENTORY')
    lower=np.maximum(-ASSET_CAP,old-turnover_cap)
    upper=np.minimum( ASSET_CAP,old+turnover_cap)
    # PSD regularization is numerical, not a fitted signal parameter.
    eig=np.linalg.eigvalsh(sigma)
    if eig[0]<-1e-10:raise ValueError('Z1143_NON_PSD_COV')
    sigma=sigma+np.eye(4)*1e-7
    step=1/max(.05,float(np.linalg.eigvalsh(sigma)[-1])*8)
    w=base.copy()
    for _ in range(12):
        # Subgradient of quadratic log-growth approximation.
        grad=mu-sigma@w-(SLIPPAGE+BASE_FEE)*np.sign(w-old)-np.asarray(funding_bound)*np.sign(w)
        candidate=np.clip(w+step*grad,lower,upper)
        # Preserve signed net/gross bounds via deterministic scalar projection.
        gross=np.abs(candidate).sum();net=abs(candidate.sum())
        scale=min(1.,GROSS_CAP/max(gross,1e-12),NET_CAP/max(net,1e-12))
        candidate=np.clip(candidate*scale,lower,upper)
        if corner_gate(candidate,down,up,funding_bound,old,margin=.98):
            w=candidate
        else:
            # Fixed 12 bisection rounds toward the feasible reduce-only base.
            a,b=0.,1.
            for _ in range(12):
                mid=(a+b)/2;probe=base+mid*(candidate-base)
                if corner_gate(probe,down,up,funding_bound,old,margin=.98):a=mid
                else:b=mid
            w=base+a*(candidate-base)
    if not corner_gate(w,down,up,funding_bound,old):
        raise AssertionError('Z1143_GOVERNOR_FAILED')
    if np.any(np.abs(w-old)>turnover_cap+1e-10):
        raise AssertionError('Z1143_CAPACITY_FAILED')
    # Quantize to six decimals WITHOUT crossing original capacity limits.
    loq=np.ceil(lower*1e6-1e-9)/1e6
    hiq=np.floor(upper*1e6+1e-9)/1e6
    if np.any(loq>hiq):raise AssertionError('Z1149_NO_EXECUTABLE_QUANTUM')
    out=np.clip(np.sign(w)*np.floor(np.abs(w)*1e6+1e-9)/1e6,loq,hiq)
    if not corner_gate(out,down,up,funding_bound,old):
        raise AssertionError('Z1143_QUANTIZED_GOVERNOR_FAILED')
    if np.any(np.abs(out-old)>turnover_cap+1e-10):
        raise AssertionError('Z1149_QUANTIZED_CAPACITY_FAILED')
    return out

def compose_z(op,hi,lo,cl,quote,funding,*,diagnostics=False):
    sleeves,regime,r=sleeves_and_regimes(op,hi,lo,cl,quote,funding)
    n=len(cl);dn,up,fb=prior_adverse_bounds(cl,hi,lo,funding)
    # 12h covariance is prior-price causal; independent from funding carry.
    rr=r.to_numpy(float)
    covs=[]
    for t in range(n):
        if t<720:covs.append(None)
        else:
            a=rr[t-168:t+1]
            covs.append(np.cov(a,rowvar=False,ddof=0)*12)
    # Ex-ante sleeve weights are structural, never selected using PnL.
    regime_weight=np.array([[.5,.7,1.2,1.6],[1.,1.,1.,1.],[1.5,1.3,.7,.6]])
    result={};counts={};first_valid=720
    for mode,capital in CAPITAL.items():
        for path in PATHS:
            target=np.zeros((n,4));last=np.zeros(4);changes=0
            for t in range(first_valid,n):
                if t%REBALANCE==0:
                    scores=np.array([0. for _ in SLEEVES])
                    for j,sleeve in enumerate(SLEEVES):
                        if sleeve not in EXCLUDE[path]:
                            scores[j]=regime_weight[regime[t],j]
                    blend=sum(scores[j]*sleeves[key][t] for j,key in enumerate(SLEEVES))
                    # Volatility-scaled 12h expected edge, fixed before PnL.
                    alpha=.018*blend/max(float(scores.sum()),1.)
                    if (np.isfinite(dn[t]).all() and np.isfinite(up[t]).all()
                        and np.isfinite(fb[t]).all() and covs[t] is not None):
                        last=optimize_joint(alpha,covs[t],last,dn[t],up[t],fb[t],
                                            quote.iloc[t].to_numpy(float),capital)
                        changes+=1
                target[t]=last
            result[(path,mode)]=pd.DataFrame(target,index=cl.index,columns=ASSETS)
            counts[path,mode]=changes
    if diagnostics:
        return result,{'source_only':True,'historical_pnl_computed':False,
            'validation_2025_read':False,'external_benchmarks_used':False,
            'regime_hours':{str(i):int((regime==i).sum()) for i in range(3)},
            'sleeve_active_hours':{k:int((np.abs(v).sum(axis=1)>0).sum()) for k,v in sleeves.items()},
            'governor_calls':counts,'t_plus_one_execution':True}
    return result

def canonical_hash(frame):
    x=frame.to_numpy(float)
    if x.shape[1]!=4 or not np.isfinite(x).all():raise ValueError('Z1143_CANONICAL_SHAPE')
    raw=frame.to_csv(float_format='%.6f',lineterminator='\n').encode()
    if not np.allclose(pd.read_csv(io.BytesIO(raw),index_col=0).to_numpy(float),x,rtol=0,atol=1e-12):
        raise ValueError('Z1143_CANONICAL_ROUNDTRIP')
    return hashlib.sha256(raw).hexdigest()
