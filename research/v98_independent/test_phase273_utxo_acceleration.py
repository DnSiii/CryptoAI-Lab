import importlib.util
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p273",ROOT/"research/v98_independent/phase273_utxo_acceleration.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def test_exact_date_growth_no_imputation(tmp_path):
    idx=pd.date_range("2023-01-01",periods=100,freq="D",tz="UTC")
    vals=[100+i for i in range(100)]
    p=tmp_path/"u.csv"
    pd.DataFrame({"date":[x.date().isoformat() for x in idx],"utxo_count":vals,"source_points":[1]*100}).to_csv(p,index=False)
    on,recent,prior,s=P.acceleration_signal(p)
    d=idx[-1]
    assert abs(recent.loc[d]-(198/168-1))<1e-12
    assert abs(prior.loc[d]-(168/138-1))<1e-12
    # Remove an exact required date: signal must become unavailable/OFF.
    x=pd.read_csv(p);x=x[x["date"]!="2023-03-10"];x.to_csv(p,index=False)
    on2,_,_,_=P.acceleration_signal(p)
    assert not bool(on2.loc[d])

def test_frozen_constants():
    assert P.SLEEVE_PER_ASSET==.0625 and P.SYSTEM_CAP==1.50 and P.DECISION_HOUR==23

def test_external_firewall():
    t=(ROOT/"research/v98_independent/phase273_utxo_acceleration.py").read_text().lower()
    assert "research/v99" not in t and "paper_v99" not in t
