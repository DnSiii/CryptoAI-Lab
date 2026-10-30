"""V98 Phase261 BTC NVT DATA_ONLY invariants."""
import datetime as dt,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p261",ROOT/"research/v98_independent/phase261_btc_nvt.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def test_bounds_and_endpoint():
    assert P.EXPECTED==1096 and P.START==dt.date(2023,1,1) and P.END==dt.date(2025,12,31)
    assert P.URL=="https://api.blockchain.info/charts/nvt?start=2023-01-01&timespan=3years&format=json&sampled=false"

def test_parse_filters_training():
    def ts(y,m,d):return int(dt.datetime(y,m,d,tzinfo=dt.timezone.utc).timestamp())
    raw=json.dumps({"values":[{"x":ts(2022,12,31),"y":1},{"x":ts(2023,1,1),"y":10},{"x":ts(2025,12,31),"y":20},{"x":ts(2026,1,1),"y":30}]}).encode()
    rows,invalid=P.parse(raw)
    assert [r["date"] for r in rows]==["2023-01-01","2025-12-31"] and invalid==0

def test_same_day_mean():
    t=int(dt.datetime(2023,1,1,tzinfo=dt.timezone.utc).timestamp())
    rows,_=P.parse(json.dumps({"values":[{"x":t,"y":10},{"x":t+3600,"y":30}]}).encode())
    assert rows[0]["nvt"]==20 and rows[0]["source_points"]==2

def test_invalid_counted():
    rows,invalid=P.parse(json.dumps({"values":[{"x":"bad","y":1},{"x":1,"y":"nan"}]}).encode())
    assert rows==[] and invalid==2

def test_data_only_firewall():
    text=(ROOT/"research/v98_independent/phase261_btc_nvt.py").read_text().lower()
    assert "exact_fast" not in text and "cryptoai_v13" not in text and "phase252" not in text
    assert '"pnl_executed":false' in text.replace(" ","")
    assert "research/v99" not in text and "paper_v99" not in text
