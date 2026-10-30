#!/usr/bin/env python3
import argparse, hashlib, json, math
from pathlib import Path
YEARS=("2023","2024","2025")
STRESSES=("base","severe","supersevere")
def main():
 p=argparse.ArgumentParser(); p.add_argument("result"); a=p.parse_args(); d=json.loads(Path(a.result).read_text())
 assert d["phase"]==227 and d["cutoff"]=="<2026-01-01" and len(d["specs"])==8
 raw=dict(d); claimed=raw.pop("deterministic_payload_sha256"); assert hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()==claimed
 survivors=[]
 for key,folds in d["specs"].items():
  assert set(folds)==set(YEARS); ok=True
  for y in YEARS:
   cells=folds[y]; assert set(cells)==set(STRESSES)
   for s in STRESSES:
    m=cells[s]
    required=("return","max_drawdown","profit_factor","payoff","win_rate","positive_days","trades","tail_p01","tail_p05","tail_p50","tail_p95","tail_p99","worst_trade","best_trade","max_asset_concentration","asset_pnl_contribution","funding_contribution","regimes")
    assert all(k in m for k in required)
    assert all(math.isfinite(float(m[k])) for k in ("return","max_drawdown","profit_factor","payoff","win_rate","positive_days","max_asset_concentration"))
    assert m["worst_trade"]<=m["tail_p01"]<=m["tail_p05"]<=m["tail_p50"]<=m["tail_p95"]<=m["tail_p99"]<=m["best_trade"]
    assert len(m["asset_pnl_contribution"])==5 and set(m["regimes"])=={"bull","bear","sideways"}
   assert cells["base"]["return"]>=cells["severe"]["return"]-1e-12>=cells["supersevere"]["return"]-1e-12
   b=cells["base"]; ok=ok and b["return"]>0 and b["profit_factor"]>1 and b["positive_days"]>.5 and b["trades"]>=30
  if ok: survivors.append(key)
 print(json.dumps({"phase":227,"payload_sha256":claimed,"survivor_count":len(survivors),"survivors":survivors,"decision":"SURVIVORS_REQUIRE_AUDIT" if survivors else "REJECT_FAMILY_NO_RESCUE"},sort_keys=True))
if __name__=="__main__": main()
