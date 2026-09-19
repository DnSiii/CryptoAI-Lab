from __future__ import annotations
import importlib.util,json
from pathlib import Path
import numpy as np,pandas as pd
from cryptoai_v13.data import FuturesData
PROJECT=Path(__file__).resolve().parents[1]
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,PROJECT/path); assert spec and spec.loader; mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
BASE=load_module('v98_independent_baseline','scripts/v98_independent_baseline.py'); P003=load_module('v98_independent_phase003','scripts/v98_independent_phase003_dispersion_neutral.py'); P009=load_module('v98_independent_phase009','scripts/v98_independent_phase009_funding_carry_neutral.py'); P010=load_module('v98_independent_phase010','scripts/v98_independent_phase010_residual_lowvol.py'); P011=load_module('v98_independent_phase011','scripts/v98_independent_phase011_volume_attention.py'); P012=load_module('v98_independent_phase012','scripts/v98_independent_phase012_residual_skew.py'); P013=load_module('v98_independent_phase013','scripts/v98_independent_phase013_bull_dispersion.py'); P037=load_module('v98_independent_phase037','scripts/v98_independent_phase037_utc_block_seasonality.py'); P041=load_module('v98_independent_phase041','scripts/v98_independent_phase041_trade_size_pressure.py'); P042=load_module('v98_independent_phase042','scripts/v98_independent_phase042_funding_shock_reversal.py'); P043=load_module('v98_independent_phase043','scripts/v98_independent_phase043_trade_intensity.py')
def synthetic_data(hours=6500):
    index=pd.date_range('2024-01-01',periods=hours,freq='h',tz='UTC'); symbols=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','ADAUSDT','LINKUSDT','LTCUSDT','DOGEUSDT','SOLUSDT','AVAXUSDT'); rng=np.random.default_rng(42); btc_r=rng.normal(.00002,.007,hours); close={'BTCUSDT':100*np.exp(np.cumsum(btc_r))}
    for i,s in enumerate(symbols[1:],1): close[s]=100*np.exp(np.cumsum((.65+.03*i)*btc_r+rng.normal(.00001*((i%3)-1),.0045+i*.0002,hours)))
    c=pd.DataFrame(close,index=index); o=c.shift(1).fillna(c.iloc[0]); qv={s:1e6*(len(symbols)-i)*(1+.15*np.sin(np.arange(hours)/24+i)) for i,s in enumerate(symbols)}; trades={s:800+40*i+80*(1+np.sin(np.arange(hours)/31+i)) for i,s in enumerate(symbols)}; frames={'open':o,'high':pd.DataFrame(np.maximum(o,c)*1.002,index=index,columns=symbols),'low':pd.DataFrame(np.minimum(o,c)*.998,index=index,columns=symbols),'close':c,'volume':pd.DataFrame(1000.,index=index,columns=symbols),'quote_volume':pd.DataFrame(qv,index=index),'trades':pd.DataFrame(trades,index=index)}; funding=pd.DataFrame({s:.0001*np.sin(np.arange(hours)/8+i) for i,s in enumerate(symbols)},index=index); return FuturesData(frames,funding,symbols)
def membership_for(d): return d.close.notna()
def mutate_future(d,cut):
    frames={k:v.copy() for k,v in d.frames.items()}
    for f in frames.values(): f.iloc[cut+1:]*=1.75
    funding=d.funding.copy(); funding.iloc[cut+1:]=.05; return FuturesData(frames,funding,d.symbols)
def test_v98_baseline_targets_are_future_invariant():
    cfg=json.loads((PROJECT/'config'/'v98_independent.json').read_text()); d=synthetic_data(); a=BASE.build_targets(d,membership_for(d),cfg); cut=5600; m=mutate_future(d,cut); b=BASE.build_targets(m,membership_for(m),cfg); pd.testing.assert_frame_equal(a.iloc[:cut+1],b.iloc[:cut+1])
def test_v98_phase003_targets_are_future_invariant():
    d=synthetic_data(); a=P003.build_targets(d,membership_for(d)); cut=5600; m=mutate_future(d,cut); b=P003.build_targets(m,membership_for(m)); pd.testing.assert_frame_equal(a.iloc[:cut+1],b.iloc[:cut+1])
def test_v98_phase003_respects_gross_and_rebalance_constraints():
    d=synthetic_data(); t=P003.build_targets(d,membership_for(d)); assert float(t.abs().sum(axis=1).max())<=P003.PHASE['gross_cap']+1e-12; changed=t.diff().abs().sum(axis=1)>1e-12; hours=np.flatnonzero(changed.to_numpy()); assert not len(hours) or all(h%P003.PHASE['rebalance_hours']==0 for h in hours)
def test_v98_phase003_is_nearly_dollar_neutral_at_rebalances():
    d=synthetic_data(); t=P003.build_targets(d,membership_for(d)); active=t.abs().sum(axis=1)>1e-8
    if active.any(): assert float(t.loc[active].sum(axis=1).abs().max())<1e-8
def test_recent_v98_hypotheses_are_future_invariant():
    d=synthetic_data(); cut=5600; m=mutate_future(d,cut)
    for mod in (P009,P010,P011,P012,P013,P037,P041,P042,P043):
        a=mod.build_targets(d,membership_for(d)); b=mod.build_targets(m,membership_for(m)); pd.testing.assert_frame_equal(a.iloc[:cut+1],b.iloc[:cut+1],obj=mod.PHASE['id'])
def test_v98_phase037_constraints_and_clock():
    d=synthetic_data(); t=P037.build_targets(d,membership_for(d)); assert float(t.abs().sum(axis=1).max())<=P037.PHASE['gross_cap']+1e-12
    changed=t.diff().abs().sum(axis=1)>1e-12
    if changed.any(): assert set(t.index[changed].hour).issubset({0,8,16})
    active=t.abs().sum(axis=1)>1e-8
    if active.any(): assert float(t.loc[active].sum(axis=1).abs().max())<1e-8
def _assert_daily_neutral(mod):
    d=synthetic_data(); t=mod.build_targets(d,membership_for(d)); assert float(t.abs().sum(axis=1).max())<=mod.PHASE['gross_cap']+1e-12
    changed=t.diff().abs().sum(axis=1)>1e-12; hours=np.flatnonzero(changed.to_numpy()); assert not len(hours) or all(h%mod.PHASE['rebalance_hours']==0 for h in hours)
    active=t.abs().sum(axis=1)>1e-8
    if active.any(): assert float(t.loc[active].sum(axis=1).abs().max())<1e-8
def test_v98_phase041_constraints_and_neutrality(): _assert_daily_neutral(P041)
def test_v98_phase042_constraints_and_neutrality(): _assert_daily_neutral(P042)
def test_v98_phase043_constraints_and_neutrality(): _assert_daily_neutral(P043)
def test_final_holdout_is_reserved_and_not_accessed_by_research_scripts():
    cfg=json.loads((PROJECT/'config'/'v98_independent.json').read_text()); assert cfg['final_holdout_start']>cfg['validation_end']; assert cfg['research_rules']['final_holdout_single_open_only'] is True
    forbidden=("cfg['final_holdout_start']","cfg[\"final_holdout_start\"]","cfg['final_holdout_end']","cfg[\"final_holdout_end\"]")
    for path in (PROJECT/'scripts').glob('v98_independent_phase*.py'):
        text=path.read_text(); assert not any(token in text for token in forbidden),f'final holdout data access leaked into research script: {path.name}'
