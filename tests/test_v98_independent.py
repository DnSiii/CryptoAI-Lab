from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

PROJECT = Path(__file__).resolve().parents[1]

def load_module(name: str, path: str):
    spec=importlib.util.spec_from_file_location(name,PROJECT/path); assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

BASE=load_module('v98_independent_baseline','scripts/v98_independent_baseline.py')
P003=load_module('v98_independent_phase003','scripts/v98_independent_phase003_dispersion_neutral.py')
P009=load_module('v98_independent_phase009','scripts/v98_independent_phase009_funding_carry_neutral.py')
P010=load_module('v98_independent_phase010','scripts/v98_independent_phase010_residual_lowvol.py')
P011=load_module('v98_independent_phase011','scripts/v98_independent_phase011_volume_attention.py')
P012=load_module('v98_independent_phase012','scripts/v98_independent_phase012_residual_skew.py')

def synthetic_data(hours:int=6500)->FuturesData:
    index=pd.date_range('2024-01-01',periods=hours,freq='h',tz='UTC'); symbols=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','ADAUSDT','LINKUSDT','LTCUSDT','DOGEUSDT','SOLUSDT','AVAXUSDT'); rng=np.random.default_rng(42); btc_r=rng.normal(0.00002,0.007,hours); close={'BTCUSDT':100*np.exp(np.cumsum(btc_r))}
    for i,symbol in enumerate(symbols[1:],start=1):
        idio=rng.normal(0.00001*((i%3)-1),0.0045+i*0.0002,hours); close[symbol]=100*np.exp(np.cumsum((0.65+0.03*i)*btc_r+idio))
    close_df=pd.DataFrame(close,index=index); opened=close_df.shift(1).fillna(close_df.iloc[0]); qv={symbol:1_000_000.0*(len(symbols)-i)*(1+0.15*np.sin(np.arange(hours)/24+i)) for i,symbol in enumerate(symbols)}
    frames={'open':opened,'high':pd.DataFrame(np.maximum(opened,close_df)*1.002,index=index,columns=symbols),'low':pd.DataFrame(np.minimum(opened,close_df)*0.998,index=index,columns=symbols),'close':close_df,'volume':pd.DataFrame(1000.0,index=index,columns=symbols),'quote_volume':pd.DataFrame(qv,index=index),'trades':pd.DataFrame(1000.0,index=index,columns=symbols)}
    funding=pd.DataFrame({s:0.0001*np.sin(np.arange(hours)/8+i) for i,s in enumerate(symbols)},index=index); return FuturesData(frames=frames,funding=funding,symbols=symbols)

def membership_for(data:FuturesData)->pd.DataFrame: return data.close.notna()

def mutate_future(data:FuturesData,cut:int)->FuturesData:
    frames={k:v.copy() for k,v in data.frames.items()}
    for frame in frames.values(): frame.iloc[cut+1:]*=1.75
    funding=data.funding.copy(); funding.iloc[cut+1:]=0.05
    return FuturesData(frames,funding,data.symbols)

def test_v98_baseline_targets_are_future_invariant():
    cfg=json.loads((PROJECT/'config'/'v98_independent.json').read_text()); data=synthetic_data(); a=BASE.build_targets(data,membership_for(data),cfg); cut=5600; changed=BASE.build_targets(mutate_future(data,cut),membership_for(data),cfg); pd.testing.assert_frame_equal(a.iloc[:cut+1],changed.iloc[:cut+1])

def test_v98_phase003_targets_are_future_invariant():
    data=synthetic_data(); a=P003.build_targets(data,membership_for(data)); cut=5600; mutated=mutate_future(data,cut); changed=P003.build_targets(mutated,membership_for(mutated)); pd.testing.assert_frame_equal(a.iloc[:cut+1],changed.iloc[:cut+1])

def test_v98_phase003_respects_gross_and_rebalance_constraints():
    data=synthetic_data(); targets=P003.build_targets(data,membership_for(data)); assert float(targets.abs().sum(axis=1).max())<=P003.PHASE['gross_cap']+1e-12; changed=targets.diff().abs().sum(axis=1)>1e-12; hours=np.flatnonzero(changed.to_numpy()); assert not len(hours) or all(h%P003.PHASE['rebalance_hours']==0 for h in hours)

def test_v98_phase003_is_nearly_dollar_neutral_at_rebalances():
    data=synthetic_data(); targets=P003.build_targets(data,membership_for(data)); active=targets.abs().sum(axis=1)>1e-8
    if active.any(): assert float(targets.loc[active].sum(axis=1).abs().max())<1e-8

def test_recent_v98_hypotheses_are_future_invariant():
    data=synthetic_data(); cut=5600; mutated=mutate_future(data,cut)
    for mod in (P009,P010,P011,P012):
        a=mod.build_targets(data,membership_for(data)); b=mod.build_targets(mutated,membership_for(mutated)); pd.testing.assert_frame_equal(a.iloc[:cut+1],b.iloc[:cut+1],obj=mod.PHASE['id'])

def test_final_holdout_is_reserved_and_not_referenced_by_research_scripts():
    cfg=json.loads((PROJECT/'config'/'v98_independent.json').read_text()); assert cfg['final_holdout_start']>cfg['validation_end']; assert cfg['research_rules']['final_holdout_single_open_only'] is True
    for path in (PROJECT/'scripts').glob('v98_independent_phase*.py'):
        text=path.read_text()
        assert 'final_holdout_start' not in text and 'final_holdout_end' not in text, f'final holdout leaked into research script: {path.name}'
