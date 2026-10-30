"""V98 Phase256 volatility-normalization recovery sleeve invariants."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p256",ROOT/"research/v98_independent/phase256_vol_normalization_recovery.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*80):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    rng=np.random.default_rng(256)
    base=np.r_[rng.normal(.0001,.002,hours-120),rng.normal(-.003,.02,48),rng.normal(.002,.003,72)]
    lr=np.tile(base[:,None],(1,4))
    close=100*np.exp(np.cumsum(lr,axis=0))
    c=pd.DataFrame(close,index=idx,columns=P.P.ASSETS)
    frames={"open":c.copy(),"high":c*1.001,"low":c*.999,"close":c.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
    funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS)
    return FuturesData(frames=frames,funding=funding,symbols=P.P.ASSETS)

def test_signal_is_causal_under_future_mutation():
    d=synthetic();cut=d.close.index[-48]
    a=P.recovery_state(d)[0]
    frames={k:v.copy() for k,v in d.frames.items()}
    for k in ("open","high","low","close"):
        frames[k].loc[frames[k].index>cut]*=1.7
    bdata=FuturesData(frames=frames,funding=d.funding.copy(),symbols=d.symbols)
    b=P.recovery_state(bdata)[0]
    pd.testing.assert_series_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_constants():
    assert P.RV_H==24 and P.REF_H==720 and P.STRESS_MULT==2.0 and P.MEMORY_H==72
    assert P.SLEEVE_PER_ASSET==.0625 and P.SYSTEM_CAP==1.50 and P.DECISION_HOUR==23

def test_external_engine_firewall():
    text=(ROOT/"research/v98_independent/phase256_vol_normalization_recovery.py").read_text().lower()
    assert "research/v99" not in text and "paper_v99" not in text
