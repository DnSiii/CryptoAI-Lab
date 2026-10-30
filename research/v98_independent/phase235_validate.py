#!/usr/bin/env python3
"""Mechanical validator for V98 Independent Phase235. No tuning/rescue logic."""
import argparse,json,math
from pathlib import Path
EXPECTED={f"idskew_beta{lb}_skew{sh}_k1_h{h}" for lb in (168,336) for sh in (72,168) for h in (4,8)}
FOLDS={"2023","2024","2025"}; COSTS=("base","severe","supersevere")
REQ=("return","max_drawdown","profit_factor","payoff","win_rate","positive_days","worst_day","best_day","turnover_l1","signal_events","tail_p01","tail_p05","tail_p50","tail_p95","tail_p99","max_asset_concentration","regimes","funding_contribution")
def finite_tree(x):
 if isinstance(x,dict): return all(finite_tree(v) for v in x.values())
 if isinstance(x,(int,float)): return math.isfinite(float(x))
 return True
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("path",nargs="?",default="research/v98_independent/phase235_results.json"); a=ap.parse_args(); d=json.loads(Path(a.path).read_text())
 assert d.get("phase")==235 and d.get("cutoff")=="<2026-01-01"; assert set(d.get("specs",{}))==EXPECTED
 failures=[]; passing=[]
 for spec,folds in sorted(d["specs"].items()):
  assert set(folds)==FOLDS; ok=True
  for fold,x in folds.items():
   assert set(x)==set(COSTS)
   for c in COSTS:
    assert all(k in x[c] for k in REQ); assert finite_tree(x[c])
   b,s,ss=x["base"],x["severe"],x["supersevere"]
   # Increasing explicit transaction cost may not improve the same fixed-position PnL.
   if not (b["return"]+1e-12>=s["return"]>=ss["return"]-1e-12): failures.append(f"{spec}/{fold}: cost monotonicity"); ok=False
   # Frozen conservative annual robustness gate. No pooled-fold rescue.
   annual=(b["return"]>0 and b["profit_factor"]>1 and b["max_drawdown"]>-0.35 and b["positive_days"]>0.50 and s["return"]>0 and ss["return"]>0)
   if not annual: ok=False
  (passing if ok else failures).append(spec if ok else f"{spec}: annual gate")
 decision="PROMOTE_TO_SEPARATE_HOLDOUT_REVIEW" if passing else "REJECT_FAMILY_NO_RESCUE"
 print(json.dumps({"phase":235,"decision":decision,"passing_specs":passing,"failures":failures},indent=2,sort_keys=True))
 if not finite_tree(d): raise SystemExit("non-finite result payload")
if __name__=="__main__": main()
