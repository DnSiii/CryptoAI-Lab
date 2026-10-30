from __future__ import annotations
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,PROJECT/path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

P142=load_module('v98_phase142','scripts/v98_independent_phase142_treasury_curve_steepening_strict_pit.py')

def synthetic():
    idx=pd.date_range('2023-01-01',periods=24*90,freq='h',tz='UTC')
    close=pd.DataFrame(100.,index=idx,columns=P142.ASSETS)
    days=pd.date_range('2023-01-01',periods=70,freq='D',tz='UTC')
    macro=pd.Series(np.arange(len(days),dtype=float),index=days)
    return SimpleNamespace(close=close),macro

def test_phase142_future_macro_invariant():
    d,m=synthetic();cut=pd.Timestamp('2023-02-20',tz='UTC')
    a,_=P142.build_targets(d,m)
    mm=m.copy();mm.loc[mm.index>cut]+=10000
    b,_=P142.build_targets(d,mm)
    # Future macro changes cannot alter targets before their d+2 admissible time.
    pd.testing.assert_frame_equal(a.loc[:cut+pd.Timedelta(days=2)],b.loc[:cut+pd.Timedelta(days=2)])

def test_phase142_target_gross_long_only_equal_weight():
    d,m=synthetic();t,_=P142.build_targets(d,m)
    assert float(t.min().min())>=-1e-15
    assert float(t.abs().sum(axis=1).max())<=P142.TARGET_GROSS+1e-12
    active=t.abs().sum(axis=1)>1e-10
    if active.any():
        row=t.loc[active].iloc[0][P142.ASSETS]
        assert float(row.max()-row.min())<1e-12
        assert abs(float(row.sum())-P142.TARGET_GROSS)<1e-12

def test_phase142_strict_pit_causal_contract_and_isolation():
    text=(PROJECT/'scripts'/'v98_independent_phase142_treasury_curve_steepening_strict_pit.py').read_text()
    assert 'PIT_USE_DAYS=2' in text
    assert 'LOOKBACK=20' in text
    assert "TARGET_GROSS=.45" in text
    assert "HARD_GROSS=.50" in text
    assert "PASS_PIT_DATA_ONLY" in text
    assert 'phase141_result_used' in text
    forbidden=('validation_start','validation_end','final_holdout_start','final_holdout_end','2026-08-01','2026-09-15')
    assert not any(x in text for x in forbidden)
