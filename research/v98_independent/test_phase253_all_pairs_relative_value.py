"""V98 Phase253 all-pairs Relative-Value Sleeve tests."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p253",ROOT/"research/v98_independent/phase253_all_pairs_relative_value.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*60):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    close=pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)
    close["BTCUSDT"]=100*np.exp(np.linspace(0,.05,hours))
    close["ETHUSDT"]=100*np.exp(np.linspace(0,.02,hours))
    close["BNBUSDT"]=100*np.exp(np.linspace(0,-.01,hours))
    close["SOLUSDT"]=100*np.exp(np.linspace(0,.01,hours))
    close.loc[idx[950]:,"BTCUSDT"]*=1.8
    close.loc[idx[1100]:,"SOLUSDT"]*=.65
    frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
    funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS)
    funding.loc[idx[::8],:]=-.0001
    return FuturesData(frames=frames,funding=funding,symbols=P.P.ASSETS)

def test_rv_overlay_is_net_zero_and_bounded():
    rv,count=P.rv_overlay(synthetic())
    assert float(rv.sum(axis=1).abs().max())<=1e-12
    assert float(rv.abs().sum(axis=1).max())<=P.RV_GROSS+1e-12
    assert int(count.max())<=len(P.PAIRS)
    assert (rv.abs().sum(axis=1)>0).any()

def test_integrated_gross_preserves_phase252_baseline():
    d=synthetic()
    base,rv,combo,_=P.integrated_targets(d)
    active=combo.index>=P.START_DECISION
    pd.testing.assert_series_equal(
        combo.loc[active].abs().sum(axis=1),
        base.loc[active].abs().sum(axis=1),
        check_names=False,
        atol=1e-10,rtol=0
    )
    assert float(combo.loc[active].min().min())>=-1e-12
    assert float(combo.loc[active].abs().sum(axis=1).max())<=P.SYSTEM_CAP+1e-12

def test_future_price_mutation_cannot_change_past_targets():
    d=synthetic();cut=d.close.index[-24*10]
    _,_,a,_=P.integrated_targets(d)
    frames={k:v.copy() for k,v in d.frames.items()}
    for k in ("open","high","low","close"):
        frames[k].loc[frames[k].index>cut,"ETHUSDT"]*=2.2
    bdata=FuturesData(frames=frames,funding=d.funding.copy(),symbols=d.symbols)
    _,_,b,_=P.integrated_targets(bdata)
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_all_pairs_and_external_firewall():
    assert len(P.PAIRS)==6 and len(set(P.PAIRS))==6
    assert P.WINDOW==720 and P.ENTRY_Z==2.0 and P.EXIT_Z==.5
    assert P.RV_GROSS==.50 and P.SYSTEM_CAP==1.25 and P.DECISION_HOUR==23
    text=(ROOT/"research/v98_independent/phase253_all_pairs_relative_value.py").read_text().lower()
    assert "research/v99" not in text and "paper_v99" not in text
