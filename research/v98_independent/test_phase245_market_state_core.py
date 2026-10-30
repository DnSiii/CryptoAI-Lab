"""V98 Phase245 market-state Growth Core causality/invariants."""
import importlib.util
from pathlib import Path
import numpy as np,pandas as pd
from cryptoai_v13.data import FuturesData
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p245",ROOT/"research/v98_independent/phase245_market_state_core.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def synthetic(hours=24*150):
 idx=pd.date_range("2022-12-01",periods=hours,freq="h",tz="UTC");x=np.arange(hours,dtype=float)
 close=pd.DataFrame({
 "BTCUSDT":100*np.exp(.00015*x),
 "ETHUSDT":100*np.exp(.00014*x),
 "BNBUSDT":100*np.exp(.00013*x),
 "SOLUSDT":100*np.exp(.00012*x)},index=idx)
 frames={"open":close.copy(),"high":close*1.001,"low":close*.999,"close":close.copy(),
 "volume":pd.DataFrame(1.,index=idx,columns=P.P.ASSETS),
 "quote_volume":pd.DataFrame(100.,index=idx,columns=P.P.ASSETS)}
 return FuturesData(frames=frames,funding=pd.DataFrame(0.,index=idx,columns=P.P.ASSETS),symbols=P.P.ASSETS)

def test_market_targets_are_common_beta_and_capped():
 t=P.market_targets(synthetic())
 assert float(t.abs().sum(axis=1).max())<=1+1e-12
 for _,row in t.iterrows():
  nz=row[row!=0]
  if len(nz): assert len(set(np.sign(nz)))==1 and len(nz)==4

def test_target_changes_only_after_23utc_decisions():
 t=P.market_targets(synthetic())
 changed=t.diff().abs().sum(axis=1)>1e-12
 if changed.any(): assert set(t.index[changed].hour)=={23}

def test_future_mutation_does_not_change_past():
 d=synthetic();cut=d.close.index[-24*10];a=P.market_targets(d)
 frames={k:v.copy() for k,v in d.frames.items()}
 for k in ("open","high","low","close"):frames[k].loc[frames[k].index>cut]*=.4
 b=P.market_targets(FuturesData(frames=frames,funding=d.funding.copy(),symbols=d.symbols))
 pd.testing.assert_frame_equal(a.loc[:cut],b.loc[:cut])

def test_frozen_parameters():
 assert P.FAST==720 and P.SLOW==2880 and P.BREADTH==3 and P.DECISION_HOUR==23
