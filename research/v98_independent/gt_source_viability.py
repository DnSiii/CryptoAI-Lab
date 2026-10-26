#!/usr/bin/env python3
"""GT authenticated source-only pre-PnL activation gate: reserve >=4 epochs/year."""
import json
import numpy as np
from gt_sources import bundle,static_check
from phase1260_aj_authenticated_source_digest import load_official,HOURS
NAMES=("GrowthCore","Opportunity","RelativeValue","StressRecovery")
def run():
    assert static_check()
    frames,_=load_official()
    signals,updates,regimes,budgets=bundle(
        frames[0],frames[1],frames[2],frames[3],frames[5],frames[6],frames[4])
    years={};passed=True
    for yr,start,end in (("2023",744,9504),("2024",9504,HOURS)):
        idx=np.flatnonzero(updates[start:end,0])+start
        reserve=[int(t) for t in idx if regimes[t]=="STRESS" and
                 not np.any(signals[t,3])]
        year={"epochs":len(idx),"reserve_epochs":len(reserve),
              "reserve_minimum":4,"reserve_pass":len(reserve)>=4}
        passed &=year["reserve_pass"]
        for i,name in enumerate(NAMES[:3]):
            active=[int(t) for t in idx if np.any(signals[t,i])]
            year[name]={"active_epochs":len(active),"minimum":4,
                        "pass":len(active)>=4}
            passed &=year[name]["pass"]
        years[yr]=year
    out={"architecture":"GT","decision":"PASS_GT_SOURCE_ONLY" if passed else
         "REJECT_GT_SOURCE_INACTIVE","historical_training_only":True,
         "validation_2025_read":False,"external_benchmarks_used":False,
         "trading_authorized":False,"years":years}
    with open("gt_source_viability.json","w") as f:json.dump(out,f,indent=2,sort_keys=True)
    print("GT_SOURCE_VIABILITY",json.dumps(out,sort_keys=True))
    raise SystemExit(0 if passed else 2)
if __name__=="__main__":run()
