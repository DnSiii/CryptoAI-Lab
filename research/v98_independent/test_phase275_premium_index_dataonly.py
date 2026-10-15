import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("p275",ROOT/"research/v98_independent/phase275_premium_index_dataonly.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
def test_contract():
    assert P.ASSETS==("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
    assert P.EXPECTED_ARCHIVES==144 and P.EXPECTED_PER_ASSET==26304 and P.EXPECTED_TOTAL==105216
    assert P.INTERVAL=="1h" and "premiumIndexKlines" in P.BASE
def test_month_hours_leap_year():
    assert len(P.month_hours(2023,2))==28*24
    assert len(P.month_hours(2024,2))==29*24
def test_frozen_url_shape():
    name,url,check=P.urls("BTCUSDT",2023,1)
    assert name=="BTCUSDT-1h-2023-01.zip"
    assert url.endswith("/premiumIndexKlines/BTCUSDT/1h/BTCUSDT-1h-2023-01.zip")
    assert check==url+".CHECKSUM"
def test_no_trading_imports():
    t=(ROOT/"research/v98_independent/phase275_premium_index_dataonly.py").read_text().lower()
    assert "exact_fast" not in t and "phase252" not in t and "cryptoai_v13" not in t
