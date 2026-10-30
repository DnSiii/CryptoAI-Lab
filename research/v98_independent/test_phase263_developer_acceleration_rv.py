"""V98 Phase263 developer-acceleration RV causality/invariants."""
import importlib.util,tempfile
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p263",ROOT/"research/v98_independent/phase263_developer_acceleration_rv.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def panel(path,months=12):
    idx=pd.period_range("2023-01",periods=months,freq="M")
    rows=[]
    for k,a in enumerate(P.P.ASSETS):
        for i,m in enumerate(idx):
            rows.append({"asset":a,"repo":f"x/{a}","branch":"master","month":str(m),
              "commit_count":10+i*(k+1),"first_commit":"","last_commit":""})
    pd.DataFrame(rows,columns=["asset","repo","branch","month","commit_count","first_commit","last_commit"]).to_csv(path,index=False)

def test_frozen_constants():
    assert P.RECENT_MONTHS==3 and P.PRIOR_MONTHS==3
    assert P.LONG_BUDGET==.125 and P.SHORT_BUDGET==.125
    assert P.OVERLAY_GROSS_CAP==.25 and P.SYSTEM_CAP==1.25 and P.DECISION_HOUR==23

def test_scores_use_six_completed_months():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"x.csv";panel(p,12);c=P.load_monthly(p);s=P.monthly_scores(c)
        assert s.index[0]=="2023-07"
        # First July decision can only use Jan-Jun, never July.
        c2=c.copy();c2.loc["2023-07"]*=1000
        s2=P.monthly_scores(c2)
        pd.testing.assert_series_equal(s.loc["2023-07"],s2.loc["2023-07"])

def test_overlay_net_zero_gross_capped_and_monthly_persistent():
    scores=pd.DataFrame([[3.,2.,1.,0.]],index=["2023-07"],columns=P.P.ASSETS)
    idx=pd.date_range("2023-07-01",periods=72,freq="h",tz="UTC")
    o,n=P.overlay_from_scores(scores,idx)
    assert n==1
    assert float(o.sum(axis=1).abs().max())<=1e-12
    assert float(o.abs().sum(axis=1).max())<=.25+1e-12
    assert o.loc["2023-07-02 00:00:00+00:00"].equals(o.loc["2023-07-01 23:00:00+00:00"])

def test_exact_tie_splits_budget():
    scores=pd.DataFrame([[2.,2.,0.,0.]],index=["2023-07"],columns=P.P.ASSETS)
    idx=pd.date_range("2023-07-01 23:00",periods=2,freq="h",tz="UTC")
    o,n=P.overlay_from_scores(scores,idx)
    row=o.iloc[0]
    assert np.isclose(row.iloc[0],.0625) and np.isclose(row.iloc[1],.0625)
    assert np.isclose(row.iloc[2],-.0625) and np.isclose(row.iloc[3],-.0625)

def test_future_month_mutation_cannot_change_past_scores():
    with tempfile.TemporaryDirectory() as td:
        a=Path(td)/"a.csv";b=Path(td)/"b.csv";panel(a,18)
        d=pd.read_csv(a);d.loc[d["month"]>="2024-01","commit_count"]*=100;d.to_csv(b,index=False)
        s1=P.monthly_scores(P.load_monthly(a));s2=P.monthly_scores(P.load_monthly(b))
        pd.testing.assert_frame_equal(s1.loc[:"2024-01"],s2.loc[:"2024-01"])

def test_external_engine_firewall():
    text=(ROOT/"research/v98_independent/phase263_developer_acceleration_rv.py").read_text().lower()
    assert "research/v99" not in text and "paper_v99" not in text
