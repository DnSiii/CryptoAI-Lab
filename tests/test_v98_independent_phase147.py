import importlib.util
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"v98_independent_phase147_broad_dollar_data_only.py"
spec=importlib.util.spec_from_file_location("p147",P); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def raw(rows):
 return ("observation_date,DTWEXBGS\n"+"\n".join(rows)+"\n").encode()
def test_hash_is_value_sensitive():
 a=m.audit(raw(["2023-01-02,100","2023-01-03,101"])); b=m.audit(raw(["2023-01-02,100","2023-01-03,102"]))
 assert a["normalized_observations_sha256"] != b["normalized_observations_sha256"]
def test_duplicate_and_order_fail_closed():
 a=m.audit(raw(["2023-01-03,100","2023-01-02,101","2023-01-02,102"]))
 assert not a["gates"]["unique_dates"] and not a["gates"]["strictly_increasing"] and a["decision"]=="REJECT_DATA_QUALITY_NO_RESCUE"
def test_outside_window_fails_closed():
 a=m.audit(raw(["2022-12-30,100","2023-01-02,101"]))
 assert a["counts"]["outside_window"]==1 and not a["gates"]["all_inside_frozen_window"]
def test_malformed_fails_closed():
 a=m.audit(raw(["2023-01-02,not-a-number"]))
 assert a["counts"]["malformed"]==1 and not a["gates"]["no_malformed"]
def test_output_has_no_economic_fields():
 a=m.audit(raw(["2023-01-02,100","2023-01-03,101"]))
 forbidden=("return","correlation","pnl","profit_factor","win_rate","drawdown","signal")
 def walk(x):
  if isinstance(x,dict):
   for k,v in x.items():
    key=str(k).lower()
    assert not any(t in key for t in forbidden)
    walk(v)
  elif isinstance(x,list):
   for v in x: walk(v)
 walk(a)
