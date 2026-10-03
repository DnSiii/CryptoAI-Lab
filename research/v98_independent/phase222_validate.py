#!/usr/bin/env python3
"""Decision-grade validator for namespaced Phase222 result payloads."""
import argparse, hashlib, json
from pathlib import Path
REQ=("return","max_drawdown","profit_factor","payoff","win_rate","positive_days","trades","tail_p01","tail_p05","tail_p50","tail_p95","tail_p99","worst_trade","best_trade","max_asset_concentration","funding_contribution","regimes")
ap=argparse.ArgumentParser(); ap.add_argument("result"); ap.add_argument("--compare"); a=ap.parse_args(); raw=Path(a.result).read_bytes(); p=json.loads(raw)
assert p["phase"]==222 and p["cutoff"]=="<2026-01-01" and len(p["specs"])==8
# Verify the evaluator's deterministic payload digest, not merely the serialized file bytes.
claimed=p.get("deterministic_payload_sha256"); assert isinstance(claimed,str) and len(claimed)==64
core=dict(p); core.pop("deterministic_payload_sha256",None)
canonical=json.dumps(core,sort_keys=True,separators=(",",":"))
assert hashlib.sha256(canonical.encode()).hexdigest()==claimed, "internal deterministic payload SHA mismatch"
passing=[]
for k,v in p["specs"].items():
 assert set(v)=={"2023","2024","2025"}
 for y,z in v.items():
  assert set(z)=={"base","severe","supersevere"}
  assert z["supersevere"]["return"]<=z["severe"]["return"]+1e-12<=z["base"]["return"]+1e-12
  for stress,m in z.items():
   assert all(x in m for x in REQ); assert set(m["regimes"])=={"bull","bear","sideways"}; assert 0<=m["max_asset_concentration"]<=1+1e-12
   assert m["max_drawdown"]<=1e-12 and m["profit_factor"]>=0 and m["payoff"]>=0 and 0<=m["win_rate"]<=1 and 0<=m["positive_days"]<=1 and m["trades"]>=0
   for rm in m["regimes"].values():
    assert all(x in rm for x in ("return","max_drawdown","profit_factor","payoff","win_rate","positive_days"))
    assert rm["max_drawdown"]<=1e-12 and rm["profit_factor"]>=0 and rm["payoff"]>=0 and 0<=rm["win_rate"]<=1 and 0<=rm["positive_days"]<=1
 if all(v[y]["base"]["return"]>0 and v[y]["base"]["profit_factor"]>1 for y in ("2023","2024","2025")): passing.append(k)
if a.compare:
 other=Path(a.compare).read_bytes(); assert raw==other, "reproducibility failure: outputs differ"
print(json.dumps({"file_sha256":hashlib.sha256(raw).hexdigest(),"payload_sha256":claimed,"coherent_specs":passing,"decision":"REJECT_FAMILY_NO_RESCUE" if not passing else "ROBUSTNESS_GATE_REQUIRED"},sort_keys=True))
