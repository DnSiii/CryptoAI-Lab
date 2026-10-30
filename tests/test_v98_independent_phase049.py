from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
from cryptoai_v13.data import FuturesData
PROJECT=Path(__file__).resolve().parents[1]
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,PROJECT/path); assert spec and spec.loader; mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
P049=load_module('v98_independent_phase049','scripts/v98_independent_phase049_positioning_divergence.py')
def synthetic(hours=6500):
 idx=pd.date_range('2024-01-01',periods=hours,freq='h',tz='UTC'); syms=('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','ADAUSDT','LINKUSDT','LTCUSDT','DOGEUSDT','SOLUSDT','AVAXUSDT'); rng=np.random.default_rng(49); br=rng.normal(.00002,.007,hours); close={'BTCUSDT':100*np.exp(np.cumsum(br))}
 for i,s in enumerate(syms[1:],1): close[s]=100*np.exp(np.cumsum((.5+.03*i)*br+rng.normal(0,.005,hours)))
 c=pd.DataFrame(close,index=idx); o=c.shift(1).fillna(c.iloc[0]); frames={'open':o,'high':np.maximum(o,c)*1.002,'low':np.minimum(o,c)*.998,'close':c,'volume':pd.DataFrame(1000.,index=idx,columns=syms),'quote_volume':pd.DataFrame({s:1e6*(11-i)*np.ones(hours) for i,s in enumerate(syms)},index=idx),'trades':pd.DataFrame(1000.,index=idx,columns=syms)}; funding=pd.DataFrame(0.,index=idx,columns=syms); sig=pd.DataFrame({s:.2*np.sin(np.arange(hours)/37+i)+.01*i for i,s in enumerate(syms)},index=idx); return FuturesData(frames,funding,syms),sig
def test_phase049_future_signal_invariant():
 d,s=synthetic(); cut=5600; a=P049.build_targets(d,d.close.notna(),s); m=s.copy(); m.iloc[cut+1:]+=100; b=P049.build_targets(d,d.close.notna(),m); pd.testing.assert_frame_equal(a.iloc[:cut+1],b.iloc[:cut+1])
def test_phase049_constraints_clock_and_dollar_neutrality():
 d,s=synthetic(); t=P049.build_targets(d,d.close.notna(),s); assert float(t.abs().sum(axis=1).max())<=P049.PHASE['gross_cap']+1e-12; changed=t.diff().abs().sum(axis=1)>1e-12; hours=np.flatnonzero(changed.to_numpy()); assert not len(hours) or all(h%P049.PHASE['rebalance_hours']==0 for h in hours); active=t.abs().sum(axis=1)>1e-8
 if active.any(): assert float(t.loc[active].sum(axis=1).abs().max())<1e-8
def test_phase049_strict_lag_and_no_final_holdout_access():
 text=(PROJECT/'scripts'/'v98_independent_phase049_positioning_divergence.py').read_text(); assert '.shift(1)' in text; forbidden=("cfg['final_holdout_start']","cfg[\"final_holdout_start\"]","cfg['final_holdout_end']","cfg[\"final_holdout_end\"]"); assert not any(token in text for token in forbidden)
def test_phase049_canonicalization_is_sorted_positive_and_deterministic():
 raw=pd.DataFrame({'create_time':['2024-01-01 01:50:00','2024-01-01 00:10:00','2024-01-01 01:10:00'],'sum_toptrader_long_short_ratio':[2.,1.5,1.8],'count_long_short_ratio':[1.,1.,1.]}); h=P049.canonical_positioning(raw); assert list(h.hour)==sorted(h.hour.tolist()); assert len(h)==2; assert np.isfinite(h.divergence).all()
