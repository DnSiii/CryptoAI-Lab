"""V98 Phase257 Wikimedia DATA_ONLY invariants."""
import datetime as dt
import importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p257",ROOT/"research/v98_independent/phase257_wikimedia_attention.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def raw(items):
    return json.dumps({"items":items},sort_keys=True).encode()

def test_expected_training_days():
    assert P.EXPECTED==1096
    assert P.START==dt.date(2023,1,1) and P.END==dt.date(2025,12,31)

def test_mapping_is_exact_clean4():
    assert P.ASSET_ARTICLE=={
        "BTCUSDT":"Bitcoin","ETHUSDT":"Ethereum",
        "BNBUSDT":"BNB_Smart_Chain_(blockchain_platform)",
        "SOLUSDT":"Solana_(blockchain_platform)"
    }

def test_endpoint_frozen_components():
    u=P.endpoint("Bitcoin",2024)
    assert "en.wikipedia.org/all-access/user/Bitcoin/daily/2024010100/2024123100" in u

def test_parser_keeps_only_training_dates():
    b=raw([
      {"timestamp":"2022123100","views":1},
      {"timestamp":"2023010100","views":2},
      {"timestamp":"2025123100","views":3},
      {"timestamp":"2026010100","views":4},
    ])
    rows=P.parse_items("BTCUSDT","Bitcoin",b)
    assert [x["date"] for x in rows]==["2023-01-01","2025-12-31"]

def test_parser_requires_integer_convertible_views():
    b=raw([{"timestamp":"2023010100","views":"12"},{"timestamp":"bad","views":5}])
    rows=P.parse_items("BTCUSDT","Bitcoin",b)
    assert rows[0]["views"]==12 and len(rows)==1

def test_asset_stats_gap_and_duplicate_detection():
    rows=[
      {"asset":"BTCUSDT","article":"Bitcoin","date":"2023-01-01","views":1},
      {"asset":"BTCUSDT","article":"Bitcoin","date":"2023-01-01","views":1},
      {"asset":"BTCUSDT","article":"Bitcoin","date":"2023-01-05","views":1},
    ]
    s=P.asset_stats(rows)
    assert s["duplicates"]==1 and s["max_gap_days"]==3

def test_csv_is_deterministic_sorted():
    rows=[
      {"asset":"ETHUSDT","article":"Ethereum","date":"2023-01-02","views":2},
      {"asset":"BTCUSDT","article":"Bitcoin","date":"2023-01-01","views":1},
    ]
    a=P.csv_bytes(rows);b=P.csv_bytes(list(reversed(rows)))
    assert a==b and P.sha256_bytes(a)==P.sha256_bytes(b)

def test_no_trading_engine_import_or_price_join():
    text=(ROOT/"research/v98_independent/phase257_wikimedia_attention.py").read_text().lower()
    assert "exact_fast" not in text and "cryptoai_v13" not in text
    assert "phase252" not in text and "load_data(" not in text
    assert '"pnl_executed":false' in text.replace(" ","")

def test_no_external_engine_paths():
    text=(ROOT/"research/v98_independent/phase257_wikimedia_attention.py").read_text().lower()
    assert "research/v99" not in text and "paper_v99" not in text
