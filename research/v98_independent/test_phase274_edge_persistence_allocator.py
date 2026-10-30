import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
from cryptoai_v13.data import FuturesData

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p274",ROOT/"research/v98_independent/phase274_edge_persistence_allocator.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*80):
    idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC")
    x=np.arange(hours,dtype=float)
    close=pd.DataFrame({a:100*np.exp((.00008+.00001*j)*x) for j,a in enumerate(P.P.ASSETS)},index=idx)
    frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
            "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
            "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
    # Negative funding turns the frozen Phase252 opportunity sleeve on.
    funding=pd.DataFrame(-.00001,index=idx,columns=P.P.ASSETS)
    return FuturesData(frames=frames,funding=funding,symbols=P.P.ASSETS)

def test_allocator_never_reduces_phase252_and_caps_gross():
    data=synthetic()
    _,_,baseline,boost,integrated,edge,_=P.allocated_targets(data)
    assert ((integrated-baseline)>=-1e-12).all().all()
    assert float(integrated.abs().sum(axis=1).max())<=P.SYSTEM_CAP+1e-12
    assert set(np.unique(boost.to_numpy())).issubset({0.,P.EXTRA_PER_ASSET})

def test_future_mutation_cannot_change_past_allocator():
    d=synthetic();cut=d.close.index[-24*10]
    a=P.allocated_targets(d)[4]
    frames={k:v.copy() for k,v in d.frames.items()}
    for k in ("open","high","low","close"):
        frames[k].loc[frames[k].index>cut]*=1.8
    bdata=FuturesData(frames=frames,funding=d.funding.copy(),symbols=d.symbols)
    b=P.allocated_targets(bdata)[4]
    pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_constants_and_firewall():
    assert P.EDGE_H==720 and P.EXTRA_PER_ASSET==.0625 and P.SYSTEM_CAP==1.50
    t=(ROOT/"research/v98_independent/phase274_edge_persistence_allocator.py").read_text().lower()
    assert "research/v99" not in t and "paper_v99" not in t
