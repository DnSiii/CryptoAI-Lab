#!/usr/bin/env python3
"""V98 Independent K: preregistered seven-slot SOURCE-ONLY signal construction.

NO historical PnL, mark/funding use, benchmark reads, holdout reads, or promotion.
All decisions at close(t) are eligible no earlier than open(t+1).
See phase865_k_composed_growth_prereg_20261021.md (created before this code).
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
PATHS=('K_core_only','K_full','K_minus_opportunity','K_minus_relative_value','K_minus_recovery')
SLEEVE_SHARES={'core':.55,'opportunity':.20,'relative_value':.15,'recovery':.10}
GROSS={'risk_on':1.50,'neutral':1.00,'risk_off':.35}
ASSET_CAP=.70
GROSS_CAP=1.75
START=pd.Timestamp('2022-12-01T00:00:00Z')
END=pd.Timestamp('2024-12-31T23:00:00Z')
PINS={'BTCUSDT':'5fecf1d58c8f998c9bba2a3f937c384896bf8d794b98a2755b17af807b3f0190',
      'ETHUSDT':'541748f469cddf34579a3f7865bdec04dab86f886dbd029e90b69ae24ab1325f',
      'BNBUSDT':'f0776970a530a37fe8f5c434b080fe46919ddb5194d3aa98d02589fed0a2d058',
      'SOLUSDT':'fa7b07c0892370da2375fb4be2ba1dc82fe700173f0eb8b0807ef16b303ca085'}


def pinned_training_frames(root:Path):
    """Only immutable Phase803 CSVs, not validation, PnL or other engines."""
    root=Path(root)
    fields={}
    index=pd.date_range(START,END,freq='h')
    for asset in ASSETS:
        raw=(root/f'{asset}_1h.csv').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=PINS[asset]:
            raise PermissionError('pinned Clean-4 training digest mismatch: '+asset)
        from io import BytesIO
        frame=pd.read_csv(BytesIO(raw))
        if tuple(frame.columns)!=('open_time','open','high','low','close','volume','quote_volume'):
            raise ValueError('Clean-4 schema mismatch')
        ts=pd.DatetimeIndex(pd.to_datetime(frame.open_time,utc=True))
        if not ts.equals(index):raise ValueError('training-only chronology mismatch')
        if not all(np.isfinite(frame[f]).all() for f in ('open','high','low','close','volume','quote_volume')):
            raise ValueError('nonfinite source')
        if (frame['low']<=0).any() or (frame['low']>frame[['open','close']].min(axis=1)).any() or (frame['high']<frame[['open','close']].max(axis=1)).any():
            raise ValueError('OHLC geometry mismatch')
        fields[asset]=frame
    close=pd.DataFrame({a:fields[a].close.to_numpy(float) for a in ASSETS},index=index)
    high=pd.DataFrame({a:fields[a].high.to_numpy(float) for a in ASSETS},index=index)
    return close,high


def _normalize(score:pd.DataFrame)->pd.DataFrame:
    v=score.to_numpy(dtype=float)
    v=np.where(np.isfinite(v)&(v>0),v,0.)
    denom=v.sum(axis=1,keepdims=True)
    return pd.DataFrame(np.divide(v,denom,out=np.zeros_like(v),where=denom>0),index=score.index,columns=score.columns)


def _cap_and_redistribute(target:np.ndarray,gross:float)->np.ndarray:
    """Long-only waterfill; unused gross remains in cash if no active capacity."""
    score=np.asarray(target,dtype=float)
    if score.shape!=(4,) or not np.isfinite(score).all() or (score<0).any():
        raise ValueError('invalid target score')
    if not 0<=gross<=GROSS_CAP:raise ValueError('invalid gross target')
    if score.sum()<=0:return np.zeros(4)
    out=np.zeros(4)
    remain=float(gross)
    active=score>0
    for _ in range(4):
        if not active.any() or remain<=1e-12:break
        part=remain*score*active/(score*active).sum()
        cap_left=np.maximum(ASSET_CAP-out,0)
        fill=np.minimum(part,cap_left)
        out+=fill
        remain-=float(fill.sum())
        active&=(cap_left-fill)>1e-12
    if out.max()>ASSET_CAP+1e-10 or out.sum()>GROSS_CAP+1e-10:
        raise AssertionError('K cap invariant')
    return out


def compose_k(close:pd.DataFrame,high:pd.DataFrame)->dict[str,pd.DataFrame]:
    if not isinstance(close,pd.DataFrame) or not isinstance(high,pd.DataFrame):
        raise TypeError('frames required')
    if tuple(close.columns)!=ASSETS or not close.index.equals(high.index) or tuple(high.columns)!=ASSETS:
        raise ValueError('Clean-4 aligned frames only')
    if len(close)<1000 or close.index[0]!=START or close.index[-1]!=END or not close.index.equals(pd.date_range(START,END,freq='h')):
        raise ValueError('no 2025+ or incomplete training calendar')
    if not np.isfinite(close.to_numpy(float)).all() or not np.isfinite(high.to_numpy(float)).all() or (close<=0).any().any() or (high<close).any().any():
        raise ValueError('invalid OHLC input')
    ret=np.log(close).diff()
    mom=np.log(close/close.shift(168))
    vol=ret.rolling(72,min_periods=72).std(ddof=0)*np.sqrt(24)
    core=_normalize((mom.clip(lower=0)/vol.where(vol>1e-12)).fillna(0))
    prior_high=high.shift(1).rolling(48,min_periods=48).max()
    breakout=(close>prior_high)&(mom>0)
    opp=_normalize((breakout.astype(float).rolling(24,min_periods=1).max()*(mom>0)).astype(float))
    residual=np.log(close/close.shift(72))
    rv=_normalize(residual.sub(residual.mean(axis=1),axis=0).clip(lower=0).fillna(0))
    market=ret.mean(axis=1)
    market_index=np.exp(market.fillna(0).cumsum())
    dd=market_index/market_index.rolling(24,min_periods=24).max()-1
    stress=(dd.rolling(168,min_periods=168).min()<=-.08)
    breadth=(mom>0).sum(axis=1)
    improving=breadth>breadth.shift(24)
    positive24=market.rolling(24,min_periods=24).sum()>0
    recovery=_normalize(core.mul((stress&improving&positive24).astype(float),axis=0))
    market_vol=market.rolling(72,min_periods=72).std(ddof=0)
    vol_q75=market_vol.rolling(336,min_periods=336).quantile(.75)
    risk_on=(breadth>=3)&(market_vol<vol_q75)&vol_q75.notna()
    neutral=(breadth>=2)&~risk_on
    gross=np.where(risk_on,GROSS['risk_on'],np.where(neutral,GROSS['neutral'],GROSS['risk_off']))
    sleeve={'core':core.to_numpy(float),'opportunity':opp.to_numpy(float),
            'relative_value':rv.to_numpy(float),'recovery':recovery.to_numpy(float)}
    out={}
    for path in PATHS:
        excluded=({'K_core_only':{'opportunity','relative_value','recovery'},
                   'K_full':set(),
                   'K_minus_opportunity':{'opportunity'},
                   'K_minus_relative_value':{'relative_value'},
                   'K_minus_recovery':{'recovery'}})[path]
        targets=np.zeros((len(close),4))
        last=np.zeros(4)
        for t in range(len(close)):
            shares=np.array([SLEEVE_SHARES[k] if k not in excluded and sleeve[k][t].sum()>0 else 0.
                             for k in SLEEVE_SHARES],dtype=float)
            combined=np.zeros(4)
            if shares.sum()>0:
                shares/=shares.sum()
                for j,k in enumerate(SLEEVE_SHARES):combined+=shares[j]*sleeve[k][t]
            desired=_cap_and_redistribute(combined,float(gross[t]))
            weekly=close.index[t].weekday()==0 and close.index[t].hour==0
            if weekly or np.abs(desired-last).sum()>.15:
                last=desired
            targets[t]=last
        out[path]=pd.DataFrame(targets,index=close.index,columns=ASSETS)
    return out


def summarize(paths):
    result={'phase':866,'source_only':True,'historical_pnl_computed':False,
            'vendor_origin_attested_in_this_run':False,'validation_2025_read':False,
            'holdout_accessed':False,'external_benchmarks_used':False,
            'promotion_eligible':False,'paths':{}}
    for name,frame in paths.items():
        w=frame.to_numpy(float)
        result['paths'][name]={
            'sha256':hashlib.sha256(frame.to_csv(float_format='%.12g').encode()).hexdigest(),
            'hours':len(frame),'max_gross':float(w.sum(axis=1).max()),
            'max_asset':float(w.max()),'active_hours':int((w.sum(axis=1)>0).sum()),
            'target_rebalance_hours':int((np.abs(np.diff(w,axis=0)).sum(axis=1)>1e-12).sum()),
            'target_l1_turnover':float(np.abs(np.diff(w,axis=0)).sum())}
    return result


if __name__=='__main__':
    here=Path(__file__).resolve().parent
    close,high=pinned_training_frames(here/'phase243_clean4_canonical')
    output=summarize(compose_k(close,high))
    (here/'phase866_k_sevenslot_source_result.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps(output,sort_keys=True))
