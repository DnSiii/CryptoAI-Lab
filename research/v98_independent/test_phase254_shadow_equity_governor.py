"""V98 Phase254 shadow-equity governor invariants."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p254",ROOT/"research/v98_independent/phase254_shadow_equity_governor.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def test_governor_blocks_only_after_frozen_drawdown():
    idx=pd.date_range("2023-01-01",periods=2300,freq="h",tz="UTC")
    eq=pd.Series(1.0,index=idx)
    eq.iloc[:2160]=np.linspace(1.0,2.0,2160)
    eq.iloc[2160:]=1.5
    m=P.governor_mask(eq)
    assert m.index.equals(idx)
    # only decision hours can change the state
    changes=m.astype(int).diff().fillna(0)!=0
    assert set(idx[changes].hour).issubset({P.DECISION_HOUR})

def test_governed_targets_never_touch_core():
    idx=pd.date_range("2023-01-01",periods=2300,freq="h",tz="UTC")
    cols=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
    core=pd.DataFrame(.25,index=idx,columns=cols)
    sleeve=pd.DataFrame(.0625,index=idx,columns=cols)
    eq=pd.Series(1.0,index=idx)
    eq.iloc[:2160]=np.linspace(1.0,2.0,2160)
    eq.iloc[2160:]=1.5
    g,b=P.governed_targets(core,sleeve,eq)
    assert (g>=core-1e-12).all().all()
    assert float(g.abs().sum(axis=1).min())>=1.0-1e-12
    assert float(g.abs().sum(axis=1).max())<=1.25+1e-12
    assert b.dtype==bool

def test_frozen_params_and_external_firewall():
    text=(ROOT/"research/v98_independent/phase254_shadow_equity_governor.py").read_text().lower()
    assert P.PEAK_H==2160 and P.BLOCK_DD==-0.20 and P.DECISION_HOUR==23
    assert "research/v99" not in text and "paper_v99" not in text
