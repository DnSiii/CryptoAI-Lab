"""V98 Phase251 Funding Friction Router causality and invariants."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p251",ROOT/"research/v98_independent/phase251_funding_friction_router.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*45,dispersed=True):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    close=pd.DataFrame({a:100*np.exp(np.cumsum(np.full(hours,.0001))) for a in P.P.ASSETS},index=idx)
    frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
    funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS)
    if dispersed:
        funding.loc[idx[::8],"BTCUSDT"]=-.001
        funding.loc[idx[::8],"ETHUSDT"]=-.001
        funding.loc[idx[::8],"BNBUSDT"]=.001
        funding.loc[idx[::8],"SOLUSDT"]=.001
    return FuturesData(frames=frames,funding=funding,symbols=P.P.ASSETS)

def test_candidate_geometry():
    row=pd.Series([-.01,-.005,.005,.01],index=P.P.ASSETS)
    w=P.candidate_weights(row)
    assert sorted(round(float(x),10) for x in w)==[.2,.2,.3,.3]
    assert abs(float(w.sum())-1)<1e-12

def test_router_stays_equal_without_economic_savings():
    t,_=P.targets(synthetic(dispersed=False))
    active=t.loc[t.index>=P.START_DECISION]
    assert (active==.25).all().all()

def test_router_selects_candidate_when_savings_cover_roundtrip():
    t,d=P.targets(synthetic(dispersed=True))
    active=t.loc[t.index>=P.START_DECISION]
    geometries={tuple(sorted(round(float(x),10) for x in row)) for row in active.to_numpy()}
    assert (.2,.2,.3,.3) in geometries
    assert any(x["candidate_selected"] for x in d)

def test_future_funding_mutation_cannot_change_past_targets():
    d=synthetic(dispersed=True);cut=d.funding.index[-24*7]
    a,_=P.targets(d)
    f=d.funding.copy();f.loc[f.index>cut,:]*=-100
    b,_=P.targets(FuturesData(frames={k:v.copy() for k,v in d.frames.items()},funding=f,symbols=d.symbols))
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_parameters_and_external_firewall():
    text=(ROOT/"research/v98_independent/phase251_funding_friction_router.py").read_text().lower()
    assert P.WINDOW_H==168 and P.CHEAP_W==.30 and P.EXPENSIVE_W==.20 and P.CORE_W==.25
    assert P.ROUTER_COST==.0007 and P.DECISION_HOUR==23
    assert "research/v99" not in text and "paper_v99" not in text
