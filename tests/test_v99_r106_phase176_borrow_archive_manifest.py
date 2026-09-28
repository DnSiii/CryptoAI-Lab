import importlib.util, pathlib, tempfile, csv
from datetime import datetime, timezone
P=pathlib.Path(__file__).parents[1]/"scripts"/"v99_r106_phase176_borrow_archive_manifest.py"
s=importlib.util.spec_from_file_location("p176",P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

def write(rows):
    f=tempfile.NamedTemporaryFile(suffix=".csv",delete=False,mode="w",newline="")
    w=csv.writer(f); w.writerow(["timestamp","ccy","rate"]); w.writerows(rows); f.close(); return pathlib.Path(f.name)

def test_holdout_row_is_detected_fail_closed():
    p=write([["2021-12-01T00:00:00Z","BTC","0.1"],["2024-01-18T00:00:00Z","BTC","0.2"]])
    r=m.inspect(p)["members"][0]
    assert r["outside_frozen_train_rows"]==1

def test_duplicate_and_nonmonotonic_are_detected():
    p=write([["2022-01-02T00:00:00Z","BTC","0.1"],["2022-01-01T00:00:00Z","BTC","0.1"],["2022-01-01T00:00:00Z","BTC","0.1"]])
    r=m.inspect(p)["members"][0]
    assert r["duplicate_timestamps"]==1 and r["monotonic"] is False

def test_epoch_ms_parsing_is_utc():
    d=m.parse_ts("1640995200000")
    assert d==datetime(2022,1,1,tzinfo=timezone.utc)
