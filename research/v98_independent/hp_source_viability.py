#!/usr/bin/env python3
"""HP authenticated source-only counterfactual financing/causality gate; no historical system PnL."""
import json
import numpy as np
from hp_sources import bundle,static_check
from phase1260_aj_authenticated_source_digest import load_official,HPURS
NAMES=("GrowthCore","Opportunity","RelativeValue","StressRecovery")
def run():
    assert static_check()
    frames,_=load_official()
    signals,updates,regimes,budgets=bundle(
        frames[0],frames[1],frames[2],frames[3],frames[5],frames[6],frames[4])
    years={};passed=True
    for yr,start,end in (("2023",744,9504),("2024",9504,HPURS)):
        idx=np.flatnonzero(updates[start:end,0])+start
        y={"epochs":len(idx),"minimum_active_epochs":8}
        for i,name in enumerate(NAMES):
            count=sum(bool(np.any(signals[t,i]) and (i==0 or budgets[t,i]>0)) for t in idx)
            y[name]={"financed_epochs":int(count),"minimum":8,"pass":bool(count>=8)}
            passed &=y[name]["pass"]
        years[yr]=y
    out={"architecture":"HP","decision":"PASS_HP_SOURCE_ONLY" if passed else
         "REJECT_HP_SOURCE_INACTIVE","historical_training_only":True,
         "validation_2025_read":False,"external_benchmarks_used":False,
         "trading_authorized":False,"years":years}
    with open("hp_source_viability.json","w") as f:json.dump(out,f,indent=2,sort_keys=True)
    print("HP_SOURCE_VIABILITY",json.dumps(out,sort_keys=True))
    raise SystemExit(0 if passed else 2)
if __name__=="__main__":run()
