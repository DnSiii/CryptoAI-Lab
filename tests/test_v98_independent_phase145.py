from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/"scripts"/"v98_independent_phase145_vix_data_only.py"
s=spec_from_file_location("p145",P); m=module_from_spec(s); s.loader.exec_module(m)
def raw(rows):return ("observation_date,VIXCLS\n"+"\n".join(rows)+"\n").encode()
def test_hash_is_value_sensitive():
 a=m.audit(raw(["2023-01-02,20.0","2023-01-03,21.0"])); b=m.audit(raw(["2023-01-02,20.0","2023-01-03,22.0"]))
 assert a["normalized_observations_sha256"]!=b["normalized_observations_sha256"]
def test_duplicate_and_order_fail_closed():
 a=m.audit(raw(["2023-01-03,20","2023-01-02,21","2023-01-02,22"]))
 assert not a["gates"]["unique_dates"] and not a["gates"]["strictly_increasing"]
def test_malformed_fails_closed():
 a=m.audit(raw(["2023-01-02,abc"])); assert not a["gates"]["no_malformed"]
def test_schema_identity_required():
 with pytest.raises(RuntimeError):m.audit(b"date,VIXCLS\n2023-01-02,20\n")
def test_data_only_contract_has_no_economic_keys():
 a=m.audit(raw(["2023-01-02,20"])); text=str(a).lower()
 for token in ("return","correlation","pnl","profit","drawdown","sharpe","payoff","win_rate","position","signal"):
  assert token not in text
