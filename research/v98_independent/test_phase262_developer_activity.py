"""V98 Phase262 developer activity DATA_ONLY invariants."""
import datetime as dt,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p262",ROOT/"research/v98_independent/phase262_developer_activity.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def test_repo_mapping_frozen():
    assert P.REPOS=={
      "BTCUSDT":("bitcoin/bitcoin","master"),
      "ETHUSDT":("ethereum/go-ethereum","master"),
      "BNBUSDT":("bnb-chain/bsc","master"),
      "SOLUSDT":("anza-xyz/agave","master"),
    }

def test_month_bounds():
    s,n=P.month_bounds(2024,2)
    assert s==dt.datetime(2024,2,1,tzinfo=dt.timezone.utc)
    assert n==dt.datetime(2024,3,1,tzinfo=dt.timezone.utc)

def test_year_end_month_bounds():
    s,n=P.month_bounds(2025,12)
    assert n==dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)

def test_csv_deterministic():
    rows=[
      {"asset":"ETHUSDT","repo":"ethereum/go-ethereum","branch":"master","month":"2023-02","commit_count":2,"first_commit":"","last_commit":""},
      {"asset":"BTCUSDT","repo":"bitcoin/bitcoin","branch":"master","month":"2023-01","commit_count":1,"first_commit":"","last_commit":""},
    ]
    assert P.csv_bytes(rows)==P.csv_bytes(list(reversed(rows)))

def test_training_bounds_frozen():
    assert P.START==dt.datetime(2023,1,1,tzinfo=dt.timezone.utc)
    assert P.END==dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)

def test_data_only_firewall():
    text=(ROOT/"research/v98_independent/phase262_developer_activity.py").read_text().lower()
    assert "exact_fast" not in text and "cryptoai_v13" not in text and "phase252" not in text
    assert '"pnl_executed":false' in text.replace(" ","")
    assert "research/v99" not in text and "paper_v99" not in text
