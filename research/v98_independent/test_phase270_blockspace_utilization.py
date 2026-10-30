import datetime as dt,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p270",ROOT/"research/v98_independent/phase270_blockspace_utilization.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

def test_contract():
    assert P.EXPECTED==1096 and "avg-block-size" in P.URL

def test_parse_filter_and_average():
    def ts(y,m,d,h=0):return int(dt.datetime(y,m,d,h,tzinfo=dt.timezone.utc).timestamp())
    raw=json.dumps({"values":[
      {"x":ts(2022,12,31),"y":1},
      {"x":ts(2023,1,1),"y":1.2},
      {"x":ts(2023,1,1,12),"y":1.4},
      {"x":ts(2026,1,1),"y":1.6}
    ]}).encode()
    rows,invalid=P.parse(raw)
    assert invalid==0 and len(rows)==1 and abs(rows[0]["avg_block_size_mb"]-1.3)<1e-12

def test_data_only_no_trading_imports():
    t=(ROOT/"research/v98_independent/phase270_blockspace_utilization.py").read_text().lower()
    assert "exact_fast" not in t and "cryptoai_v13" not in t and "phase252" not in t
