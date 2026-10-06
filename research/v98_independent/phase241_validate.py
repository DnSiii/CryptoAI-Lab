#!/usr/bin/env python3
"""Independent mechanical validator for V98 Phase241. Training folds only; no rescue."""
import json,sys
from pathlib import Path
EXPECTED=4; FOLDS=("2023","2024","2025"); COSTS=("base","severe","supersevere")
REQUIRED=("return","max_drawdown","profit_factor","payoff","win_rate","positive_days","turnover_l1","tail_p01","tail_p05","tail_p50","tail_p95","tail_p99","max_asset_concentration","asset_pnl_contribution","funding_contribution","regimes")
def main():
 d=json.loads(Path(sys.argv[1]).read_text()); assert d["phase"]==241 and d["cutoff"]=="<2026-01-01" and len(d["specs"])==EXPECTED
 audit={"phase":241,"specs":{},"decision":"REJECT_FAMILY_NO_RESCUE"}; passed=[]
 for name,s in sorted(d["specs"].items()):
  assert set(s)==set(FOLDS); reasons=[]
  for y in FOLDS:
   assert set(s[y])==set(COSTS)
   for c in COSTS:
    m=s[y][c]
    for k in REQUIRED: assert k in m,(name,y,c,k)
    assert m.get("tail_frequency")=="daily"; assert set(m["regimes"])=={"bull","bear","sideways"}
    assert m["max_drawdown"]<=1e-12 and 0<=m["win_rate"]<=1 and 0<=m["positive_days"]<=1 and m["turnover_l1"]>=0
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
