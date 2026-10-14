"""V98 Phase247 synchronized-breakout Opportunity Sleeve tests."""
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
from cryptoai_v13.data import FuturesData
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p247",ROOT/"research/v98_independent/phase247_opportunity.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*50):
 idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC");x=np.arange(hours,dtype=float)
 close=pd.DataFrame({a:100*np.exp((.0001+.00001*i)*x) for i,a in enumerate(P.P.ASSETS)},index=idx)
 frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
 "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),"quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
 return FuturesData(frames=frames,funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS),symbols=P.P.ASSETS)

def test_core_sleeve_combined_geometry():
 core,sleeve,combo=P.targets(synthetic())
 assert float(core.abs().sum(axis=1).max())<=1+1e-12
 assert float(sleeve.abs().sum(axis=1).max())<=.25+1e-12
 assert float(combo.abs().sum(axis=1).max())<=1.25+1e-12
 assert set(np.unique(sleeve.to_numpy())).issubset({0.,.0625})

def test_sleeve_changes_only_at_daily_decision():
 _,s,_=P.targets(synthetic());changed=s.diff().abs().sum(axis=1)>1e-12
 after=changed & (s.index>P.START_DECISION)
 if after.any():assert set(s.index[after].hour)=={23}

def test_future_mutation_invariant():
 d=synthetic();cut=d.close.index[-24*5];a=P.targets(d)[2]
 frames={k:v.copy() for k,v in d.frames.items()}
 for k in ("open","high","low","close"):frames[k].loc[frames[k].index>cut]*=.5
 b=P.targets(FuturesData(frames=frames,funding=d.funding.copy(),symbols=d.symbols))[2]
 pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_opportunity_parameters():
 assert P.LOOKBACK==720 and P.BREADTH==3 and P.SLEEVE_PER_ASSET==.0625 and P.SYSTEM_CAP==1.25
