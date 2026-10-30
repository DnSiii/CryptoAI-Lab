from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
from cryptoai_v13.data import FuturesData
PROJECT=Path(__file__).resolve().parents[1]
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,PROJECT/path); assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
P109=load_module('v98_independent_phase109','scripts/v98_independent_phase109_fee_burden_rotation.py')

def synthetic(hours=24*180):
    idx=pd.date_range('2024-01-01',periods=hours,freq='h',tz='UTC'); syms=('BTCUSDT','ETHUSDT'); rng=np.random.default_rng(109)
    close=pd.DataFrame({'BTCUSDT':100*np.exp(np.cumsum(rng.normal(.00002,.006,hours))),
                        'ETHUSDT':100*np.exp(np.cumsum(rng.normal(.00003,.007,hours)))},index=idx)
    o=close.shift(1).fillna(close.iloc[0]);frames={'open':o,'high':np.maximum(o,close)*1.002,'low':np.minimum(o,close)*.998,'close':close,
    'volume':pd.DataFrame(1000.,index=idx,columns=syms),'quote_volume':pd.DataFrame(1e6,index=idx,columns=syms),'trades':pd.DataFrame(1000.,index=idx,columns=syms)}
    funding=pd.DataFrame(0.,index=idx,columns=syms);days=pd.date_range('2022-11-01','2025-12-31',freq='1D',tz='UTC')
    fees={'btc':pd.Series(10+np.sin(np.arange(len(days))/9),index=days),'eth':pd.Series(12+np.sin(np.arange(len(days))/11),index=days)}
    supply={'btc':pd.Series(19e6+np.arange(len(days))*900,index=days),'eth':pd.Series(120e6+np.arange(len(days))*500,index=days)}
    return FuturesData(frames,funding,syms),fees,supply

def test_phase109_future_metric_invariant():
    d,f,s=synthetic(); cut=pd.Timestamp('2024-04-01',tz='UTC'); a=P109.build_targets(d,f,s)
    mf={k:v.copy() for k,v in f.items()}; ms={k:v.copy() for k,v in s.items()}
    for k in mf:
        mf[k].loc[mf[k].index>cut]*=1000; ms[k].loc[ms[k].index>cut]*=.5
    b=P109.build_targets(d,mf,ms); pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_phase109_target_neutrality_gross_and_clock():
    d,f,s=synthetic(); t=P109.build_targets(d,f,s); active=t.abs().sum(axis=1)>1e-9
    if active.any():
        assert float(t.loc[active].sum(axis=1).abs().max())<1e-12
        assert float(t.loc[active].abs().sum(axis=1).max())<=P109.GROSS+1e-12
    changed=t.diff().abs().sum(axis=1)>1e-12
    if changed.any(): assert set(t.index[changed].hour)=={0}

def test_phase109_strict_lag_fixed_window_and_no_opened_holdout():
    text=(PROJECT/'scripts'/'v98_independent_phase109_fee_burden_rotation.py').read_text()
    assert '.shift(1)' in text and 'WINDOW=7' in text and "FeeTotNtv" in text and "SplyCur" in text
    forbidden=('final_holdout_start','final_holdout_end','2026-08','phase083_final_holdout')
    assert not any(token in text for token in forbidden)
