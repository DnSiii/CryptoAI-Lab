#!/usr/bin/env python3
"""Mechanical validator for V98 Independent Phase233. No tuning/rescue."""
import argparse,json,hashlib
from pathlib import Path
EXPECTED={f"resrev_beta{lb}_sig{sh}_k{k}_h{h}" for lb,sh,k,h in ((168,6,1,2),(168,6,1,4),(168,12,1,2),(168,12,1,4),(336,6,1,2),(336,6,1,4),(336,12,2,2),(336,12,2,4))}
FOLDS={"2023","2024","2025"}; COSTS=("base","severe","supersevere")
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("path",nargs="?",default="research/v98_independent/phase233_results.json"); a=ap.parse_args(); raw=Path(a.path).read_text(); d=json.loads(raw); assert d["phase"]==233 and d["cutoff"]=="<2026-01-01" and set(d["specs"])==EXPECTED
 survivors=[]; failures={}
 for spec,folds in d["specs"].items():
  assert set(folds)==FOLDS; ok=True; why=[]
  for y,x in folds.items():
   assert tuple(x)==COSTS; b,s,ss=x["base"],x["severe"],x["supersevere"]
   assert b["return"]+1e-12>=s["return"] and s["return"]+1e-12>=ss["return"]
   annual=(b["return"]>0 and b["profit_factor"]>1 and b["positive_days"]>0.5 and b["max_drawdown"]>-0.50); stress=(s["profit_factor"]>0.90 and ss["profit_factor"]>0.80)
   if not (annual and stress): ok=False; why.append(y)
  if ok: survivors.append(spec)
  else: failures[spec]=why
 decision="ADVANCE_TO_NEXT_GATE" if survivors else "REJECT_FAMILY_NO_RESCUE"; canonical=json.dumps(d,sort_keys=True,separators=(",",":")); print(json.dumps({"decision":decision,"survivors":survivors,"failures":failures,"file_sha256":hashlib.sha256(raw.encode()).hexdigest(),"canonical_sha256":hashlib.sha256(canonical.encode()).hexdigest()},indent=2,sort_keys=True))
if __name__=="__main__": main()
