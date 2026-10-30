#!/usr/bin/env python3
"""Independent mechanical validator for preregistered V98 Phase228."""
import argparse,hashlib,json
from pathlib import Path
EXPECTED={f"cw{cw}_bw{bw}_h{h}" for cw in (24,72) for bw in (24,72) for h in (4,8)}
YEARS=("2023","2024","2025"); COSTS=("base","severe","supersevere")
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("result"); a=ap.parse_args(); p=Path(a.result); raw=p.read_bytes(); d=json.loads(raw)
 assert d["phase"]==228 and d["family"]=="volatility_compression_breakout_continuation" and d["cutoff"]=="<2026-01-01"
 assert set(d["specs"])==EXPECTED and len(d["specs"])==8
 survivors=[]
 for spec,folds in sorted(d["specs"].items()):
  assert set(folds)==set(YEARS)
  ok=True
  for y in YEARS:
   assert set(folds[y])==set(COSTS); b=folds[y]["base"]
   for c in COSTS:
    m=folds[y][c]
    for k in ("return","max_drawdown","profit_factor","payoff","win_rate","positive_days","trades","worst_trade","best_trade","tail_p01","tail_p05","tail_p50","tail_p95","tail_p99","max_asset_concentration","funding_contribution","regimes"): assert k in m
   # Cost stress must not improve total return relative to a cheaper cost level.
   assert folds[y]["severe"]["return"] <= b["return"]+1e-12
   assert folds[y]["supersevere"]["return"] <= folds[y]["severe"]["return"]+1e-12
   ok &= b["return"]>0 and b["profit_factor"]>1 and b["positive_days"]>.50 and b["trades"]>=30
  if ok: survivors.append(spec)
 payload=dict(d); sha=payload.pop("deterministic_payload_sha256"); calc=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest(); assert sha==calc
 decision="REJECT_FAMILY_NO_RESCUE" if not survivors else "SURVIVORS_REQUIRE_ROBUSTNESS_AUDIT"
 print(json.dumps({"phase":228,"decision":decision,"survivors":survivors,"file_sha256":hashlib.sha256(raw).hexdigest(),"payload_sha256":sha},sort_keys=True))
if __name__=="__main__": main()
