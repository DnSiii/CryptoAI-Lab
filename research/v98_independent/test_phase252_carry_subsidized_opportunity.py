"""V98 Phase252 Carry-Subsidized Opportunity Sleeve tests."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p252",ROOT/"research/v98_independent/phase252_carry_subsidized_opportunity.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*45,negative=True):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    close=pd.DataFrame({a:100*np.exp(np.cumsum(np.full(hours,.0001))) for a in P.P.ASSETS},index=idx)
    frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
    funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS)
    val=-.0001 if negative else .0001
    funding.loc[idx[::8],:]=val
    return FuturesData(frames=frames,funding=funding,symbols=P.P.ASSETS)

def test_negative_funding_activates_sleeve():
    core,sleeve,combo,_=P.targets(synthetic(negative=True))
    active=combo.index>=P.START_DECISION
    assert float(combo.loc[active].max().max())==.3125
    assert (sleeve.loc[active].max(axis=1)>=0).all()
    assert float(combo.loc[active].abs().sum(axis=1).max())<=1.25+1e-12

def test_positive_funding_keeps_core_only():
    core,sleeve,combo,_=P.targets(synthetic(negative=False))
    active=combo.index>=P.START_DECISION
    tail=combo.loc[active].iloc[-24:]
    assert (tail==.25).all().all()
    assert (sleeve.loc[active].iloc[-24:]==0).all().all()

def test_future_funding_mutation_cannot_change_past_targets():
    d=synthetic(negative=True);cut=d.funding.index[-24*7]
    _,_,a,_=P.targets(d)
    f=d.funding.copy();f.loc[f.index>cut,:]*=-10
    bdata=FuturesData(frames={k:v.copy() for k,v in d.frames.items()},funding=f,symbols=d.symbols)
    _,_,b,_=P.targets(bdata)
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_parameters_and_external_firewall():
    text=(ROOT/"research/v98_independent/phase252_carry_subsidized_opportunity.py").read_text().lower()
    assert P.WINDOW_H==168 and P.SLEEVE_PER_ASSET==.0625 and P.CORE_PER_ASSET==.25
    assert P.SYSTEM_CAP==1.25 and P.DECISION_HOUR==23
    assert "research/v99" not in text and "paper_v99" not in text
