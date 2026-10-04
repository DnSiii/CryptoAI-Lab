#!/usr/bin/env python3
"""Decision-grade validator for frozen V98 Independent Phase229."""
import argparse,json,hashlib
from pathlib import Path
EXPECTED={f"{b}_lb{lb}_h{h}" for b in ("hour_of_day","hour_of_week") for lb in (12,24) for h in (1,4)}
FOLDS=("2023","2024","2025"); COSTS=("base","severe","supersevere")
def main():
 p=argparse.ArgumentParser(); p.add_argument("result"); a=p.parse_args(); raw=Path(a.result).read_text(); x=json.loads(raw)
 assert x["phase"]==229 and x["cutoff"]=="<2026-01-01" and set(x["specs"])==EXPECTED
 survivors=[]
 for spec,folds in x["specs"].items():
  assert set(folds)==set(FOLDS)
  ok=True
  for y in FOLDS:
   assert set(folds[y])==set(COSTS); b=folds[y]["base"]; s=folds[y]["severe"]; ss=folds[y]["supersevere"]
   for m in (b,s,ss):
    for k in ("return","max_drawdown","profit_factor","payoff","win_rate","positive_days","trades","tail_p01","tail_p05","tail_p50","tail_p95","tail_p99","worst_trade","best_trade","max_asset_concentration","asset_pnl_contribution","funding_contribution","regimes"): assert k in m
   # Higher costs must not improve aggregate return under identical positions/accounting.
   assert b["return"]+1e-12>=s["return"] and s["return"]+1e-12>=ss["return"]
   ok &= b["return"]>0 and b["profit_factor"]>1 and b["positive_days"]>.5 and b["trades"]>=30
  if ok: survivors.append(spec)
 payload=dict(x); sha=payload.pop("deterministic_payload_sha256"); calc=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest(); assert sha==calc
 decision="SURVIVORS_REQUIRE_NEXT_GATES" if survivors else "REJECT_FAMILY_NO_RESCUE"
 print(json.dumps({"decision":decision,"survivors":survivors,"payload_sha256":sha},sort_keys=True))
if __name__=="__main__": main()
