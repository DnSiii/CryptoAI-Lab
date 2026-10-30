"""V98 Phase248 Stress/Recovery Sleeve causality and invariants."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p248",ROOT/"research/v98_independent/phase248_stress_recovery.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*160):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    rng=np.random.default_rng(248)
    base=np.cumsum(rng.normal(0,.002,hours))
    close=pd.DataFrame({
      "BTCUSDT":100*np.exp(base),
      "ETHUSDT":100*np.exp(base+rng.normal(0,.02,hours)),
      "BNBUSDT":100*np.exp(base+rng.normal(0,.025,hours)),
      "SOLUSDT":100*np.exp(base+rng.normal(0,.03,hours)),
    },index=idx)
    frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
    funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS)
    return FuturesData(frames=frames,funding=funding,symbols=P.P.ASSETS)

def test_combined_never_short_and_gross_bound():
    _,s,c=P.targets(synthetic())
    assert float(c.min().min())>=-1e-12
    assert float(c.abs().sum(axis=1).max())<=1+1e-12
    vals=set(np.unique(c.to_numpy()))
    assert vals.issubset({0.,.125,.25})
    assert set(np.unique(s.to_numpy())).issubset({-.125,0.})

def test_future_mutation_cannot_change_past_targets():
    d=synthetic();cut=d.close.index[-24*20]
    _,_,a=P.targets(d)
    frames={k:v.copy() for k,v in d.frames.items()}
    for k in ("open","high","low","close"):
        frames[k].loc[frames[k].index>cut]*=2.5
    bdata=FuturesData(frames=frames,funding=d.funding.copy(),symbols=d.symbols)
    _,_,b=P.targets(bdata)
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_parameters_and_external_firewall():
    text=(ROOT/"research/v98_independent/phase248_stress_recovery.py").read_text().lower()
    assert P.RET_H==168 and P.RV_H==24 and P.REF_H==720
    assert P.Q==.80 and P.BREADTH==3 and P.SLEEVE_PER_ASSET==-.125
    assert P.SYSTEM_CAP==1.0 and P.DECISION_HOUR==23
    assert "research/v99" not in text and "paper_v99" not in text
