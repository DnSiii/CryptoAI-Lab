"""V98 Phase249 Dynamic Allocator causality and invariants."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p249",ROOT/"research/v98_independent/phase249_inverse_vol_allocator.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*160):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    rng=np.random.default_rng(249)
    vols=[.002,.003,.004,.005]
    close={}
    for a,v in zip(P.P.ASSETS,vols):
        close[a]=100*np.exp(np.cumsum(rng.normal(0,v,hours)))
    close=pd.DataFrame(close,index=idx)
    frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
    funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS)
    return FuturesData(frames=frames,funding=funding,symbols=P.P.ASSETS)

def test_capped_weights_sum_and_bounds():
    v=pd.Series([1.,2.,3.,4.],index=P.P.ASSETS)
    w=P.capped_inverse_vol(v)
    assert abs(float(w.sum())-1)<1e-12
    assert float(w.max())<=P.MAX_W+1e-12
    assert float(w.min())>=0

def test_target_gross_and_asset_cap():
    t=P.targets(synthetic())
    active=t.abs().sum(axis=1)>0
    if active.any():
        assert float((t.loc[active].sum(axis=1)-1).abs().max())<1e-10
        assert float(t.loc[active].max().max())<=P.MAX_W+1e-12
        assert float(t.loc[active].min().min())>=0

def test_future_mutation_cannot_change_past_targets():
    d=synthetic();cut=d.close.index[-24*20]
    a=P.targets(d)
    frames={k:v.copy() for k,v in d.frames.items()}
    for k in ("open","high","low","close"):
        frames[k].loc[frames[k].index>cut]*=3.
    b=P.targets(FuturesData(frames=frames,funding=d.funding.copy(),symbols=d.symbols))
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_parameters_and_external_firewall():
    text=(ROOT/"research/v98_independent/phase249_inverse_vol_allocator.py").read_text().lower()
    assert P.VOL_H==720 and P.MAX_W==.40 and P.DECISION_HOUR==23
    assert "research/v99" not in text and "paper_v99" not in text
