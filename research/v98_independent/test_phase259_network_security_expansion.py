"""V98 Phase259 network-security sleeve causality/invariants."""
import importlib.util,tempfile
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p259",ROOT/"research/v98_independent/phase259_network_security_expansion.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def write_csv(path,values):
    idx=pd.date_range("2023-01-01",periods=len(values),freq="D",tz="UTC")
    pd.DataFrame({"date":idx.strftime("%Y-%m-%d"),"hashrate":values,"source_points":1}).to_csv(path,index=False)

def test_frozen_constants():
    assert P.RECENT_DAYS==30 and P.PRIOR_DAYS==30 and P.SLEEVE_PER_ASSET==.0625
    assert P.SYSTEM_CAP==1.50 and P.DECISION_HOUR==23

def test_expanding_hashrate_turns_signal_on_after_warmup():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"x.csv";write_csv(p,range(1,121))
        expansion,_,_,_=P.daily_expansion(p)
        assert bool(expansion.loc[pd.Timestamp("2023-04-30",tz="UTC")]) is True
        assert expansion.loc[:"2023-02-28"].sum()==0

def test_declining_hashrate_turns_signal_off():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"x.csv";write_csv(p,list(range(200,80,-1)))
        expansion,_,_,_=P.daily_expansion(p)
        assert bool(expansion.loc[pd.Timestamp("2023-04-30",tz="UTC")]) is False

def test_three_day_gap_is_forward_filled_but_not_interpolated():
    with tempfile.TemporaryDirectory() as td:
        idx=pd.date_range("2023-01-01",periods=70,freq="D",tz="UTC")
        d=pd.DataFrame({"date":idx.strftime("%Y-%m-%d"),"hashrate":range(1,71),"source_points":1})
        d=d.drop(index=[20,21,22]);p=Path(td)/"x.csv";d.to_csv(p,index=False)
        _,_,_,s=P.daily_expansion(p)
        assert s.iloc[20]==s.iloc[19] and s.iloc[22]==s.iloc[19]

def test_future_hashrate_mutation_does_not_change_past_signal():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"a.csv";q=Path(td)/"b.csv";vals=list(range(1,121));write_csv(p,vals)
        vals2=vals[:90]+[x*100 for x in vals[90:]];write_csv(q,vals2)
        a=P.daily_expansion(p)[0];b=P.daily_expansion(q)[0]
        pd.testing.assert_series_equal(a.loc[:"2023-03-31"],b.loc[:"2023-03-31"])

def test_external_engine_firewall():
    text=(ROOT/"research/v98_independent/phase259_network_security_expansion.py").read_text().lower()
    assert "research/v99" not in text and "paper_v99" not in text
