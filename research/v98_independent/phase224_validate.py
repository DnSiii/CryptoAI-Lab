#!/usr/bin/env python3
"""Independent mechanical validator for V98 Phase224 result payloads."""
import argparse, hashlib, json, math
from pathlib import Path
FOLDS=("2023","2024","2025"); STRESSES=("base","severe","supersevere")
REQ=("return","max_drawdown","profit_factor","payoff","win_rate","positive_days","trades","tail_p01","tail_p05","tail_p50","tail_p95","tail_p99","worst_trade","best_trade","max_asset_concentration")

def main():
 p=argparse.ArgumentParser(); p.add_argument("result",type=Path); p.add_argument("--repeat",type=Path); a=p.parse_args(); raw=a.result.read_bytes(); d=json.loads(raw)
 if d.get("phase")!=224 or d.get("cutoff")!="<2026-01-01" or len(d.get("specs",{}))!=8: raise SystemExit("FAIL payload identity/spec count")
 core={k:v for k,v in d.items() if k!="deterministic_payload_sha256"}; expected=hashlib.sha256(json.dumps(core,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 if d.get("deterministic_payload_sha256")!=expected: raise SystemExit("FAIL internal SHA")
 if a.repeat and raw!=a.repeat.read_bytes(): raise SystemExit("FAIL byte reproducibility")
 coherent=[]
 for spec,folds in d["specs"].items():
  foldpass=True; agg={s:0. for s in STRESSES}
  for y in FOLDS:
   if set(folds.get(y,{}))!=set(STRESSES): raise SystemExit(f"FAIL stresses {spec}/{y}")
   for s in STRESSES:
    m=folds[y][s]
    for k in REQ:
     if k not in m or not math.isfinite(float(m[k])): raise SystemExit(f"FAIL metric {spec}/{y}/{s}/{k}")
    if not (m["tail_p01"]<=m["tail_p05"]<=m["tail_p50"]<=m["tail_p95"]<=m["tail_p99"]): raise SystemExit("FAIL tail ordering")
    if set(m.get("asset_pnl_contribution",{}))!={"ETHUSDT","BNBUSDT","XRPUSDT","SOLUSDT"}: raise SystemExit("FAIL attribution")
    if set(m.get("regimes",{}))!={"bull","bear","sideways"}: raise SystemExit("FAIL regimes")
    agg[s]+=float(m["return"])
   b=folds[y]["base"]; foldpass &= b["return"]>0 and b["profit_factor"]>1
  if not (agg["base"]>=agg["severe"]>=agg["supersevere"]): raise SystemExit(f"FAIL cost monotonicity {spec}")
  if foldpass: coherent.append(spec)
 print(json.dumps({"status":"PASS_VALIDATION","coherent_specs":coherent,"n_coherent":len(coherent),"decision":"TRAINING_SURVIVOR_REQUIRES_FULL_AUDIT" if coherent else "REJECT_FAMILY_NO_RESCUE","sha256":hashlib.sha256(raw).hexdigest()},sort_keys=True))
if __name__=="__main__": main()
