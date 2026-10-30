"""V98 Phase246 structural beta + crash governor tests."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p246",ROOT/"research/v98_independent/phase246_core_governor.py")
P=importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)

def synthetic(hours=24*140):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    x=np.arange(hours,dtype=float)
    base=np.where(x<24*100,np.exp(.0001*x),np.exp(.0001*24*100)*np.exp(-.001*(x-24*100)))
    close=pd.DataFrame({a:100*base*(1+.001*i) for i,a in enumerate(P.P.ASSETS)},index=idx)
    frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
    funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS)
    return FuturesData(frames=frames,funding=funding,symbols=P.P.ASSETS)

def test_targets_common_sign_and_gross():
    t=P.governed_targets(synthetic())
    assert float(t.abs().sum(axis=1).max())<=1+1e-12
    for _,r in t.loc[t.index>=P.START_DECISION].iterrows():
        assert set(r.to_numpy()).issubset({-.25,.25})
        assert len(set(np.sign(r)))==1

def test_changes_only_at_daily_decision():
    t=P.governed_targets(synthetic())
    changed=t.diff().abs().sum(axis=1)>1e-12
    after=changed & (t.index>P.START_DECISION)
    if after.any():
        assert set(t.index[after].hour)=={23}

def test_future_mutation_invariant():
    d=synthetic();cut=d.close.index[-24*10];a=P.governed_targets(d)
    frames={k:v.copy() for k,v in d.frames.items()}
    for k in ("open","high","low","close"):
        frames[k].loc[frames[k].index>cut]*=2.5
    b=P.governed_targets(FuturesData(frames=frames,funding=d.funding.copy(),symbols=d.symbols))
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_governor_parameters():
    assert P.PEAK_H==2160 and P.CONFIRM_H==168 and P.CRASH_DD==-.20 and P.DECISION_HOUR==23
