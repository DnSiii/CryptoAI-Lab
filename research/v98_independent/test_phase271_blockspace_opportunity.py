import importlib.util
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p271",ROOT/"research/v98_independent/phase271_blockspace_opportunity.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def test_frozen_constants():
    assert P.REF_DAYS==90 and P.QUANTILE==.75 and P.SLEEVE_PER_ASSET==.0625 and P.SYSTEM_CAP==1.50

def test_reference_excludes_latest_day(tmp_path):
    idx=pd.date_range("2023-01-01",periods=100,freq="D",tz="UTC")
    vals=list(range(1,101))
    p=tmp_path/"x.csv"
    pd.DataFrame({"date":[x.date().isoformat() for x in idx],"avg_block_size_mb":vals,"source_points":[1]*100}).to_csv(p,index=False)
    on,latest,ref,s=P.demand_regime(p)
    day=idx[-1]
    assert latest.loc[day]==99
    expected=pd.Series(range(9,99),dtype=float).quantile(.75)
    assert abs(ref.loc[day]-expected)<1e-12

def test_no_external_engine_paths():
    t=(ROOT/"research/v98_independent/phase271_blockspace_opportunity.py").read_text().lower()
    assert "research/v99" not in t and "paper_v99" not in t
