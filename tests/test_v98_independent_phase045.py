from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
from cryptoai_v13.data import FuturesData
PROJECT=Path(__file__).resolve().parents[1]
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,PROJECT/path); assert spec and spec.loader; mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
P045=load_module('v98_independent_phase045','scripts/v98_independent_phase045_liquidity_stability.py')
def synthetic_data(hours=6500):
 index=pd.date_range('2024-01-01',periods=hours,freq='h',tz='UTC'); symbols=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','ADAUSDT','LINKUSDT','LTCUSDT','DOGEUSDT','SOLUSDT','AVAXUSDT'); rng=np.random.default_rng(45); btc_r=rng.normal(.00002,.007,hours); close={'BTCUSDT':100*np.exp(np.cumsum(btc_r))}
 for i,s in enumerate(symbols[1:],1): close[s]=100*np.exp(np.cumsum((.65+.03*i)*btc_r+rng.normal(.00001*((i%3)-1),.0045+i*.0002,hours)))
 c=pd.DataFrame(close,index=index); o=c.shift(1).fillna(c.iloc[0]); qv={s:1e6*(len(symbols)-i)*(1+.15*np.sin(np.arange(hours)/24+i)+.03*rng.normal(size=hours)) for i,s in enumerate(symbols)}; trades={s:800+40*i+80*(1+np.sin(np.arange(hours)/31+i)) for i,s in enumerate(symbols)}; frames={'open':o,'high':pd.DataFrame(np.maximum(o,c)*1.002,index=index,columns=symbols),'low':pd.DataFrame(np.minimum(o,c)*.998,index=index,columns=symbols),'close':c,'volume':pd.DataFrame(1000.,index=index,columns=symbols),'quote_volume':pd.DataFrame(qv,index=index),'trades':pd.DataFrame(trades,index=index)}; funding=pd.DataFrame({s:.0001*np.sin(np.arange(hours)/8+i) for i,s in enumerate(symbols)},index=index); return FuturesData(frames,funding,symbols)
def membership_for(d): return d.close.notna()
def mutate_future(d,cut):
 frames={k:v.copy() for k,v in d.frames.items()}
 for f in frames.values(): f.iloc[cut+1:]*=1.75
 funding=d.funding.copy(); funding.iloc[cut+1:]=.05; return FuturesData(frames,funding,d.symbols)
def test_phase045_future_invariant():
 d=synthetic_data(); cut=5600; a=P045.build_targets(d,membership_for(d)); m=mutate_future(d,cut); b=P045.build_targets(m,membership_for(m)); pd.testing.assert_frame_equal(a.iloc[:cut+1],b.iloc[:cut+1])
def test_phase045_constraints_neutrality_and_clock():
 d=synthetic_data(); t=P045.build_targets(d,membership_for(d)); assert float(t.abs().sum(axis=1).max())<=P045.PHASE['gross_cap']+1e-12; changed=t.diff().abs().sum(axis=1)>1e-12; hours=np.flatnonzero(changed.to_numpy()); assert not len(hours) or all(h%P045.PHASE['rebalance_hours']==0 for h in hours); active=t.abs().sum(axis=1)>1e-8
 if active.any(): assert float(t.loc[active].sum(axis=1).abs().max())<1e-8
def test_phase045_has_no_final_holdout_access():
 text=(PROJECT/'scripts'/'v98_independent_phase045_liquidity_stability.py').read_text(); forbidden=("cfg['final_holdout_start']","cfg[\"final_holdout_start\"]","cfg['final_holdout_end']","cfg[\"final_holdout_end\"]"); assert not any(token in text for token in forbidden)
