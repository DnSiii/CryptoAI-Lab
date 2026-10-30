#!/usr/bin/env python3
"""GZ authenticated source-only weekly native cash-option recovery gate, before PnL."""
import json
import numpy as np
from gz_sources import bundle,static_check
from phase1260_aj_authenticated_source_digest import load_official,HOURS
NAMES=("GrowthCore","Opportunity","RelativeValue")
def run():
    assert static_check()
    frames,_=load_official()
    signals,updates,regimes,budgets=bundle(
        frames[0],frames[1],frames[2],frames[3],frames[5],frames[6],frames[4])
    years={};passed=True
    for yr,start,end in (("2023",744,9504),("2024",9504,HOURS)):
        idx=np.flatnonzero(updates[start:end,0])+start
        overlay=[int(t) for t in idx if np.any(signals[t,3])]
        y={"epochs":len(idx),"cash_option_epochs":len(overlay),
           "minimum":4,"overlay_pass":len(overlay)>=4}
        passed &=y["overlay_pass"]
        for i,name in enumerate(NAMES):
            count=sum(np.any(signals[t,i]) for t in idx)
            y[name]={"active_epochs":int(count),"minimum":4,"pass":bool(count>=4)}
            passed &=y[name]["pass"]
        years[yr]=y
    out={"architecture":"GZ","decision":"PASS_GZ_SOURCE_ONLY" if passed else
         "REJECT_GZ_SOURCE_INACTIVE","historical_training_only":True,
         "validation_2025_read":False,"external_benchmarks_used":False,
         "trading_authorized":False,"years":years}
    with open("gz_source_viability.json","w") as f:json.dump(out,f,indent=2,sort_keys=True)
    print("GZ_SOURCE_VIABILITY",json.dumps(out,sort_keys=True))
    raise SystemExit(0 if passed else 2)
if __name__=="__main__":run()
