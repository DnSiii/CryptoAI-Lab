"""V98 Phase250 Funding-Efficiency Allocator invariants."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p250",ROOT/"research/v98_independent/phase250_funding_efficiency_allocator.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*40):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    close=pd.DataFrame({a:100*np.exp(np.cumsum(np.full(hours,.0001*(i+1)))) for i,a in enumerate(P.P.ASSETS)},index=idx)
    frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
    funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS)
    funding.loc[idx[::8],"BTCUSDT"]=.0001
    funding.loc[idx[::8],"ETHUSDT"]=.0002
    funding.loc[idx[::8],"BNBUSDT"]=-.0001
    funding.loc[idx[::8],"SOLUSDT"]=.0003
    return FuturesData(frames=frames,funding=funding,symbols=P.P.ASSETS)

def test_weights_and_gross():
    t=P.targets(synthetic())
    active=t.abs().sum(axis=1)>0
    if active.any():
        assert float((t.loc[active].sum(axis=1)-1).abs().max())<1e-12
        vals=set(round(float(x),10) for x in t.loc[active].to_numpy().ravel())
        assert vals.issubset({.2,.3})
        row=t.loc[active].iloc[-1]
        assert row["BNBUSDT"]==.3
        assert row["BTCUSDT"]==.3
        assert row["SOLUSDT"]==.2

def test_future_funding_mutation_cannot_change_past_targets():
    d=synthetic();cut=d.funding.index[-24*5]
    a=P.targets(d)
    f=d.funding.copy()
    f.loc[f.index>cut,:]*=-100
    b=P.targets(FuturesData(frames={k:v.copy() for k,v in d.frames.items()},funding=f,symbols=d.symbols))
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_training_mask_alignment_regression():
    t=P.targets(synthetic())
    mask=(t.index>=P.P.START)&(t.index<P.P.CUT)
    weights=t.loc[mask,P.P.ASSETS]
    active=weights.abs().sum(axis=1)>0
    selected=weights.loc[active]
    assert len(selected)<=len(weights)
    assert selected.index.equals(active.index[active.to_numpy()])

def test_frozen_parameters_and_firewall():
    text=(ROOT/"research/v98_independent/phase250_funding_efficiency_allocator.py").read_text().lower()
    assert P.WINDOW_H==168 and P.CHEAP_W==.30 and P.EXPENSIVE_W==.20
    assert P.DECISION_HOUR==23
    assert "research/v99" not in text and "paper_v99" not in text
