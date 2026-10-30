#!/usr/bin/env python3
"""Independent mechanical validator for V98 Phase241. Training folds only; no rescue."""
import hashlib,json,math,sys
from pathlib import Path
EXPECTED=4; FOLDS=("2023","2024","2025"); COSTS=("base","severe","supersevere")
ASSETS={"BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT"}
REQUIRED=("return","max_drawdown","profit_factor","payoff","win_rate","positive_days","turnover_l1","tail_p01","tail_p05","tail_p50","tail_p95","tail_p99","worst_day","best_day","max_asset_concentration","asset_pnl_contribution","funding_contribution","regimes")
def finite_tree(x,path="root"):
 if isinstance(x,dict):
  for k,v in x.items(): finite_tree(v,f"{path}.{k}")
 elif isinstance(x,list):
  for i,v in enumerate(x): finite_tree(v,f"{path}[{i}]")
 elif isinstance(x,(int,float)) and not isinstance(x,bool):
  assert math.isfinite(x),f"nonfinite {path}"
def verify_payload_hash(d):
 claimed=d.get("deterministic_payload_sha256"); assert isinstance(claimed,str) and len(claimed)==64
 payload=dict(d); payload.pop("deterministic_payload_sha256",None)
 raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
 assert hashlib.sha256(raw.encode()).hexdigest()==claimed,"deterministic payload hash mismatch"
def main():
 d=json.loads(Path(sys.argv[1]).read_text()); verify_payload_hash(d); finite_tree(d)
 assert d["phase"]==241 and d["cutoff"]=="<2026-01-01" and len(d["specs"])==EXPECTED
 audit={"phase":241,"payload_hash_verified":True,"specs":{},"decision":"REJECT_FAMILY_NO_RESCUE"}; passed=[]
 for name,s in sorted(d["specs"].items()):
  assert set(s)==set(FOLDS); reasons=[]
  for y in FOLDS:
   assert set(s[y])==set(COSTS)
   for c in COSTS:
    m=s[y][c]
    for k in REQUIRED: assert k in m,(name,y,c,k)
    assert m.get("tail_frequency")=="daily"; assert set(m["regimes"])=={"bull","bear","sideways"}
    assert set(m["asset_pnl_contribution"])==ASSETS and set(m["funding_contribution"])==ASSETS
    assert m["max_drawdown"]<=1e-12 and 0<=m["win_rate"]<=1 and 0<=m["positive_days"]<=1 and m["turnover_l1"]>=0
    assert 0<=m["max_asset_concentration"]<=1+1e-12
    assert m["worst_day"]<=m["tail_p01"]<=m["tail_p05"]<=m["tail_p50"]<=m["tail_p95"]<=m["tail_p99"]<=m["best_day"]
  for y in FOLDS:
   b=s[y]["base"]; sev=s[y]["severe"]
   if b["return"]<=0: reasons.append(f"{y}:base_return<=0")
   if b["profit_factor"]<=1: reasons.append(f"{y}:base_PF<=1")
   if b["max_drawdown"]<-0.35: reasons.append(f"{y}:base_DD<-35%")
   if b["positive_days"]<=.50: reasons.append(f"{y}:base_positive_days<=50%")
   if sev["return"]<=0: reasons.append(f"{y}:severe_return<=0")
   if sev["profit_factor"]<=1: reasons.append(f"{y}:severe_PF<=1")
  ok=not reasons; audit["specs"][name]={"pass":ok,"reasons":reasons}
  if ok: passed.append(name)
 if passed: audit["decision"]="PROMOTE_TRAINING_SURVIVORS"; audit["passed_specs"]=passed
 print(json.dumps(audit,indent=2,sort_keys=True))
if __name__=="__main__": main()
