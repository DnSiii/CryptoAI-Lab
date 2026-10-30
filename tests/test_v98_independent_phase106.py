from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
from cryptoai_v13.data import FuturesData
PROJECT=Path(__file__).resolve().parents[1]
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,PROJECT/path); assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
P106=load_module('v98_independent_phase106','scripts/v98_independent_phase106_txcount_rotation.py')

def synthetic(hours=24*180):
    idx=pd.date_range('2024-01-01',periods=hours,freq='h',tz='UTC')
    syms=('BTCUSDT','ETHUSDT')
    rng=np.random.default_rng(106)
    close=pd.DataFrame({
        'BTCUSDT':100*np.exp(np.cumsum(rng.normal(.00002,.006,hours))),
        'ETHUSDT':100*np.exp(np.cumsum(rng.normal(.00003,.007,hours)))
    },index=idx)
    o=close.shift(1).fillna(close.iloc[0])
    frames={'open':o,'high':np.maximum(o,close)*1.002,'low':np.minimum(o,close)*.998,'close':close,
            'volume':pd.DataFrame(1000.,index=idx,columns=syms),
            'quote_volume':pd.DataFrame(1e6,index=idx,columns=syms),
            'trades':pd.DataFrame(1000.,index=idx,columns=syms)}
    funding=pd.DataFrame(0.,index=idx,columns=syms)
    days=pd.date_range('2022-11-01','2025-12-31',freq='1D',tz='UTC')
    s={'btc':pd.Series(np.exp(np.linspace(10,11,len(days))),index=days),
       'eth':pd.Series(np.exp(np.linspace(10,10.7,len(days))),index=days)}
    return FuturesData(frames,funding,syms),s

def test_phase106_future_metric_invariant():
    d,s=synthetic(); cut=pd.Timestamp('2024-04-01',tz='UTC')
    a=P106.build_targets(d,s)
    m={k:v.copy() for k,v in s.items()}
    for k in m: m[k].loc[m[k].index>cut]+=1e9
    b=P106.build_targets(d,m)
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_phase106_dollar_neutral_gross_and_daily_clock():
    d,s=synthetic();t=P106.build_targets(d,s)
    active=t.abs().sum(axis=1)>1e-9
    if active.any():
        assert float(t.loc[active].sum(axis=1).abs().max())<1e-12
        assert float(t.loc[active].abs().sum(axis=1).max())<=P106.GROSS+1e-12
    changed=t.diff().abs().sum(axis=1)>1e-12
    if changed.any(): assert set(t.index[changed].hour)=={0}

def test_phase106_strict_lag_and_no_opened_holdout_access():
    text=(PROJECT/'scripts'/'v98_independent_phase106_txcount_rotation.py').read_text()
    assert '.shift(1)' in text and 'LOOKBACK_DAYS=28' in text
    forbidden=('final_holdout_start','final_holdout_end','2026-08','phase083_final_holdout')
    assert not any(token in text for token in forbidden)
