import importlib.util
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"v98_independent_phase149_wti_data_only.py"
spec=importlib.util.spec_from_file_location("p149",P); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def raw(rows): return ("observation_date,DCOILWTICO\n"+"\n".join(rows)+"\n").encode()
def test_hash_is_value_sensitive():
 a=m.audit(raw(["2023-01-02,70","2023-01-03,71"])); b=m.audit(raw(["2023-01-02,70","2023-01-03,72"]))
 assert a["normalized_observations_sha256"] != b["normalized_observations_sha256"]
def test_duplicate_and_order_fail_closed():
 a=m.audit(raw(["2023-01-03,70","2023-01-02,71","2023-01-02,72"]))
 assert not a["gates"]["unique_dates"] and not a["gates"]["strictly_increasing"] and a["decision"]=="REJECT_DATA_QUALITY_NO_RESCUE"
def test_outside_and_malformed_fail_closed():
 a=m.audit(raw(["2022-12-30,70","2023-01-02,bad"]))
 assert a["counts"]["outside_window"]==1 and a["counts"]["malformed"]==1
 assert not a["gates"]["all_inside_frozen_window"] and not a["gates"]["no_malformed"]
def test_nonpositive_value_fails_closed():
 a=m.audit(raw(["2023-01-02,0","2023-01-03,-1"]))
 assert a["counts"]["malformed"]==2 and a["decision"]=="REJECT_DATA_QUALITY_NO_RESCUE"
def test_output_has_no_economic_fields():
 a=m.audit(raw(["2023-01-02,70","2023-01-03,71"]))
 forbidden=("return","correlation","pnl","profit_factor","win_rate","drawdown","signal")
 def walk(x):
  if isinstance(x,dict):
   for k,v in x.items(): assert not any(t in str(k).lower() for t in forbidden); walk(v)
  elif isinstance(x,list):
   for v in x: walk(v)
 walk(a)
