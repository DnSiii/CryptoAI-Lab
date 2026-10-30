#!/usr/bin/env python3
"""V98 Independent M preregistered composed seven-slot SOURCE-ONLY engine.

No PnL, no funding, no future holdout. One frozen hypothesis, not a grid.
Every t signal uses only information known at close(t); orders not before open(t+1).
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from phase866_k_sevenslot_source import ASSETS, START, END, pinned_training_frames, _normalize, _cap_and_redistribute

SLEEVE_BUDGETS={'growth':.60,'opportunity':.15,'relative_value':.15,'recovery':.10}
GROSS_TARGETS={0:.35,1:1.15,2:1.65}


def compose_m(close:pd.DataFrame, high:pd.DataFrame, diagnostics=False, excluded=frozenset()):
    excluded=frozenset(excluded)
    if not excluded.issubset({'opportunity','relative_value','recovery'}):
        raise ValueError('only preregistered M sleeve ablations allowed')
    if tuple(close.columns)!=ASSETS or tuple(high.columns)!=ASSETS or not close.index.equals(high.index):
        raise ValueError('Clean-4 ordered aligned frames required')
    if len(close)!=18288 or close.index[0]!=START or close.index[-1]!=END or not close.index.equals(pd.date_range(START,END,freq='h')):
        raise ValueError('pinned pre-2025 training chronology required')
    if not (np.isfinite(close.to_numpy(float)).all() and np.isfinite(high.to_numpy(float)).all()) or (close<=0).any().any() or (high<close).any().any():
        raise ValueError('source geometry invalid')
    logc=np.log(close)
    ret=logc.diff()
    mom168=logc-logc.shift(168)
    mom672=logc-logc.shift(672)
    mom72=logc-logc.shift(72)
    mom72_prev=logc.shift(72)-logc.shift(144)
    vol168=ret.rolling(168,min_periods=168).std(ddof=0)
    growth=_normalize(((.70*mom672+.30*mom168).clip(lower=0)/vol168.where(vol168>1e-12)).fillna(0))
    prior336=high.shift(1).rolling(336,min_periods=336).max()
    breakout=(close>prior336)&(mom72>0)&(mom72>mom72_prev)
    opportunity=_normalize((breakout.astype(float).rolling(72,min_periods=1).max()*(mom168>0)).astype(float))
    rv336=logc-logc.shift(336)
    median=rv336.median(axis=1)
    rv=_normalize(rv336.sub(median,axis=0).clip(lower=0).where(mom672>0,0).fillna(0))
    market=ret.mean(axis=1).fillna(0)
    mlog=market.cumsum()
    mdd=np.exp(mlog-mlog.rolling(336,min_periods=336).max())-1
    stress=mdd.rolling(168,min_periods=168).min()<=-.12
    breadth=(mom168>0).sum(axis=1)
    recover=stress&(market.rolling(72,min_periods=72).sum()>0)&(breadth>breadth.shift(72))
    recovery=_normalize(growth.mul(recover.astype(float),axis=0))
    mvol=market.rolling(168,min_periods=168).std(ddof=0)
    volq=mvol.rolling(336,min_periods=336).quantile(.80)
    market_trend=market.rolling(168,min_periods=168).sum()
    raw_on=(breadth>=3)&(market_trend>0)&(mvol<volq)&volq.notna()
    raw_off=(breadth<=1)|(market_trend<0)
    raw=np.where(raw_on,2,np.where(raw_off,0,1))
    states=np.empty(len(close),dtype=np.int8)
    state=0
    run=0
    prior=-1
    for t,x in enumerate(raw):
        x=int(x)
        run=run+1 if x==prior else 1
        prior=x
        if x!=state and run>=24:state=x
        states[t]=state
    components={k:frame.to_numpy(float) for k,frame in
                [('growth',growth),('opportunity',opportunity),('relative_value',rv),('recovery',recovery)]}
    weights=np.zeros((len(close),4),dtype=float)
    prev=np.zeros(4,dtype=float)
    rebalance=np.zeros(len(close),dtype=bool)
    for t in range(len(close)):
        is_weekly=close.index[t].weekday()==0 and close.index[t].hour==0
        transition=t>0 and states[t]!=states[t-1]
        if is_weekly or transition:
            active={k:v[t] for k,v in components.items() if k not in excluded and v[t].sum()>0}
            budget=sum(SLEEVE_BUDGETS[k] for k in active)
            scores=np.zeros(4)
            if budget>0:
                for k,vector in active.items():scores+=vector*SLEEVE_BUDGETS[k]/budget
            prev=_cap_and_redistribute(scores,GROSS_TARGETS[int(states[t])])
            rebalance[t]=True
        weights[t]=prev
    frame=pd.DataFrame(weights,index=close.index,columns=ASSETS)
    if not diagnostics:return frame
    diag={'regime_hours':{str(s):int((states==s).sum()) for s in (0,1,2)},
          'rebalance_events':int(rebalance.sum()),
          'regime_transitions':int((states[1:]!=states[:-1]).sum()),
          'sleeve_positive_hours':{k:int((v.sum(axis=1)>0).sum()) for k,v in components.items()}}
    return frame,diag


def audit_source(root:Path):
    close,high=pinned_training_frames(Path(root)/'phase243_clean4_canonical')
    frame,diag=compose_m(close,high,True)
    w=frame.to_numpy(float)
    if w.min()<-1e-12 or w.max()>.700000001 or (w.sum(axis=1)>1.750000001).any():
        raise AssertionError('M risk cap invariant')
    years=close.index.year.to_numpy()
    diag['years']={}
    for y in (2023,2024):
        v=w[years==y]
        diag['years'][str(y)]={'hours':len(v),'target_l1_turnover':float(np.abs(np.diff(v,axis=0)).sum()),
                               'active_hours':int((v.sum(axis=1)>0).sum()),
                               'mean_gross':float(v.sum(axis=1).mean()),
                               'max_asset':float(v.max())}
    return {'phase':900,'source_only':True,'historical_pnl_computed':False,
            'validation_2025_read':False,'holdout_accessed':False,
            'external_benchmarks_used':False,'promotion_eligible':False,
            'sha256':hashlib.sha256(frame.to_csv(float_format='%.12g').encode()).hexdigest(),
            'diagnostics':diag}

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    out=audit_source(root)
    (root/'phase900_m_persistent_growth_source_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
