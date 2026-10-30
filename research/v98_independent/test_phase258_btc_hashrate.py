"""V98 Phase258 BTC hashrate DATA_ONLY invariants."""
import datetime as dt,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p258",ROOT/"research/v98_independent/phase258_btc_hashrate.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def test_expected_days_and_bounds():
    assert P.EXPECTED==1096 and P.START==dt.date(2023,1,1) and P.END==dt.date(2025,12,31)

def test_frozen_endpoint():
    assert P.URL=="https://api.blockchain.info/charts/hash-rate?start=2023-01-01&timespan=3years&format=json&sampled=false"

def test_parse_x_y_schema_and_training_filter():
    def ts(d):return int(dt.datetime(*d,tzinfo=dt.timezone.utc).timestamp())
    raw=json.dumps({"values":[{"x":ts((2022,12,31)),"y":10},{"x":ts((2023,1,1)),"y":20},{"x":ts((2025,12,31)),"y":30},{"x":ts((2026,1,1)),"y":40}]}).encode()
    rows,invalid=P.parse(raw)
    assert [r["date"] for r in rows]==["2023-01-01","2025-12-31"] and invalid==0

def test_same_day_points_are_deterministically_averaged():
    t=int(dt.datetime(2023,1,1,tzinfo=dt.timezone.utc).timestamp())
    rows,_=P.parse(json.dumps({"values":[{"x":t,"y":10},{"x":t+3600,"y":20}]}).encode())
    assert len(rows)==1 and rows[0]["hashrate"]==15 and rows[0]["source_points"]==2

def test_invalid_points_counted():
    raw=json.dumps({"values":[{"x":"bad","y":1},{"x":1,"y":"nan"}]}).encode()
    rows,invalid=P.parse(raw)
    assert rows==[] and invalid==2

def test_csv_deterministic():
    rows=[{"date":"2023-01-01","hashrate":12.3456789012345,"source_points":1}]
    assert P.csv_bytes(rows)==P.csv_bytes(rows)

def test_data_only_no_trading_engine_import():
    text=(ROOT/"research/v98_independent/phase258_btc_hashrate.py").read_text().lower()
    assert "exact_fast" not in text and "cryptoai_v13" not in text and "phase252" not in text
    assert '"pnl_executed":false' in text.replace(" ","")

def test_external_engine_firewall():
    text=(ROOT/"research/v98_independent/phase258_btc_hashrate.py").read_text().lower()
    assert "research/v99" not in text and "paper_v99" not in text
