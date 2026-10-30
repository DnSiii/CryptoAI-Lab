#!/usr/bin/env python3
"""Mechanical validator for V98 Independent Phase232. No tuning/rescue."""
import argparse,json,hashlib
from pathlib import Path
EXPECTED={f"beta_disp_lb{lb}_k{k}_h{h}" for lb,k,h in ((72,1,4),(72,1,8),(168,1,4),(168,1,8),(336,1,4),(336,1,8),(168,2,4),(336,2,8))}
FOLDS={"2023","2024","2025"}; COSTS=("base","severe","supersevere")
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("path",nargs="?",default="research/v98_independent/phase232_results.json"); a=ap.parse_args(); raw=Path(a.path).read_text(); d=json.loads(raw)
 assert d["phase"]==232 and d["cutoff"]=="<2026-01-01" and set(d["specs"])==EXPECTED
 survivors=[]; failures={}
 for spec,folds in d["specs"].items():
  assert set(folds)==FOLDS; ok=True; why=[]
  for y,x in folds.items():
   assert tuple(x)==COSTS
   b,s,ss=x["base"],x["severe"],x["supersevere"]
   # Economic cost monotonicity: harsher costs cannot improve total return.
   assert b["return"]+1e-12>=s["return"] and s["return"]+1e-12>=ss["return"]
   # Frozen annual gate: positive return, PF>1, positive-day majority, DD bounded at base; stresses remain coherent/non-positive rescue forbidden.
   annual=(b["return"]>0 and b["profit_factor"]>1 and b["positive_days"]>0.5 and b["max_drawdown"]>-0.50)
   stress=(s["profit_factor"]>0.90 and ss["profit_factor"]>0.80)
   if not (annual and stress): ok=False; why.append(y)
  if ok: survivors.append(spec)
  else: failures[spec]=why
 decision="ADVANCE_TO_NEXT_GATE" if survivors else "REJECT_FAMILY_NO_RESCUE"
 canonical=json.dumps(d,sort_keys=True,separators=(",",":")); print(json.dumps({"decision":decision,"survivors":survivors,"failures":failures,"file_sha256":hashlib.sha256(raw.encode()).hexdigest(),"canonical_sha256":hashlib.sha256(canonical.encode()).hexdigest()},indent=2,sort_keys=True))
if __name__=="__main__": main()
