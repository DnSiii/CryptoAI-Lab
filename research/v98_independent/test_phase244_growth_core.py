"""V98 Phase244 Growth Core causality and invariants."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p244",ROOT/"research/v98_independent/phase244_growth_core.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*160):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    x=np.arange(hours,dtype=float)
    close=pd.DataFrame({
      "BTCUSDT":100*np.exp(.0003*x),
      "ETHUSDT":100*np.exp(-.0002*x),
      "BNBUSDT":100*(1+.00002*x+0.01*np.sin(x/50)),
      "SOLUSDT":100*(1+.00001*x+0.015*np.cos(x/70)),
    },index=idx)
    frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.ASSETS)}
    funding=pd.DataFrame(0.,index=idx,columns=P.ASSETS)
    return FuturesData(frames=frames,funding=funding,symbols=P.ASSETS)

def test_target_values_and_gross():
    t=P.targets(synthetic())
    assert set(np.unique(t.to_numpy())).issubset({-.25,0.,.25})
    assert float(t.abs().sum(axis=1).max())<=1+1e-12

def test_future_mutation_cannot_change_past_targets():
    d=synthetic();cut=d.close.index[-24*20];a=P.targets(d)
    frames={k:v.copy() for k,v in d.frames.items()}
    for k in ("open","high","low","close"):
        frames[k].loc[frames[k].index>cut]*=3.
    b=P.targets(FuturesData(frames=frames,funding=d.funding.copy(),symbols=d.symbols))
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_single_spec_and_no_external_engine_paths():
    text=(ROOT/"research/v98_independent/phase244_growth_core.py").read_text().lower()
    assert P.ENTRY==2160 and P.EXIT==720 and P.W==.25 and P.CAP==1.0
    assert "research/v99" not in text and "paper_v99" not in text
