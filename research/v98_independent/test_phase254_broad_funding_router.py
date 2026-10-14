"""V98 Phase254 Broad-Funding Router causality and invariants."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p254",ROOT/"research/v98_independent/phase254_broad_funding_router.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*45,mode="broad"):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    close=pd.DataFrame(100*np.exp(np.linspace(0,.02,hours))[:,None],
                       index=idx,columns=["x"])*pd.DataFrame(np.ones((hours,4)),index=idx,columns=P.P.ASSETS)
    frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
    funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS)
    if mode=="broad":
        funding.loc[idx[::8],"BTCUSDT"]=-.0002
        funding.loc[idx[::8],"ETHUSDT"]=-.0002
        funding.loc[idx[::8],"BNBUSDT"]=-.0001
        funding.loc[idx[::8],"SOLUSDT"]= .0001
    elif mode=="concentrated":
        funding.loc[idx[::8],"BTCUSDT"]=-.0010
        funding.loc[idx[::8],"ETHUSDT"]= .0002
        funding.loc[idx[::8],"BNBUSDT"]= .0002
        funding.loc[idx[::8],"SOLUSDT"]= .0002
    else:
        funding.loc[idx[::8],:]=.0001
    return FuturesData(frames=frames,funding=funding,symbols=P.P.ASSETS)

def test_broad_negative_funding_allows_opportunity():
    _,s,c=P.routed_targets(synthetic(mode="broad"))
    active=c.index>=P.START_DECISION
    assert float(c.loc[active].max().max())==.3125
    assert (s.loc[active].abs().sum(axis=1)>0).any()

def test_concentrated_negative_mean_is_filtered():
    _,s,c=P.routed_targets(synthetic(mode="concentrated"))
    active=c.index>=P.START_DECISION
    tail=c.loc[active].iloc[-48:]
    assert (tail==.25).all().all()
    assert (s.loc[active].iloc[-48:]==0).all().all()

def test_positive_funding_keeps_core():
    _,s,c=P.routed_targets(synthetic(mode="positive"))
    active=c.index>=P.START_DECISION
    assert (c.loc[active].iloc[-48:]==.25).all().all()
    assert (s.loc[active].iloc[-48:]==0).all().all()

def test_future_funding_mutation_cannot_change_past_targets():
    d=synthetic(mode="broad");cut=d.funding.index[-24*7]
    _,_,a=P.routed_targets(d)
    f=d.funding.copy();f.loc[f.index>cut,:]*=-100
    bdata=FuturesData(frames={k:v.copy() for k,v in d.frames.items()},funding=f,symbols=d.symbols)
    _,_,b=P.routed_targets(bdata)
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_parameters_and_external_firewall():
    text=(ROOT/"research/v98_independent/phase254_broad_funding_router.py").read_text().lower()
    assert P.WINDOW_H==168 and P.BREADTH_REQUIRED==3
    assert P.SLEEVE_PER_ASSET==.0625 and P.CORE_PER_ASSET==.25
    assert P.SYSTEM_CAP==1.25 and P.DECISION_HOUR==23
    assert "research/v99" not in text and "paper_v99" not in text
