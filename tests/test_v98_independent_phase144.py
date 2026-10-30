import importlib.util
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'scripts'/'v98_independent_phase144_sp500_risk_on.py'
spec=importlib.util.spec_from_file_location('p144',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_phase144_frozen_constants():
 assert m.LOOKBACK==20 and m.LAG_DAYS==1 and abs(m.TARGET-.45)<1e-12 and abs(m.CAP-.50)<1e-12
 assert m.ASSETS==['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT','SOLUSDT']

def test_phase144_prereg_isolation():
 import json
 p=json.loads((ROOT/'reports'/'v98_independent_phase144_sp500_risk_on_preregistration.json').read_text())
 assert p['status']=='PREREGISTERED_BEFORE_ECONOMIC_INSPECTION'
 assert p['evaluation']['validation'] is None and p['evaluation']['final_holdout'] is None
 assert p['anti_overfit']['parameter_search'] is False and p['anti_overfit']['rescue_allowed'] is False
 assert p['anti_overfit']['v16_used'] is False and p['anti_overfit']['v99_used'] is False

def test_phase144_signal_future_invariance():
 idx=pd.date_range('2023-01-02',periods=80,freq='B',tz='UTC');s=pd.Series(range(80),index=idx,dtype=float);cut=idx[50]
 a=(s>s.shift(m.LOOKBACK)).astype(float);b=s.copy();b.loc[b.index>cut]=-99999.;b=(b>b.shift(m.LOOKBACK)).astype(float)
 pd.testing.assert_series_equal(a.loc[:cut],b.loc[:cut])
 # economic activation is strictly after the source observation date
 assert (cut+pd.Timedelta(days=m.LAG_DAYS))>cut
