#!/usr/bin/env python3
"""DM preregistered source-only activity gate, no economic results or future data."""
import json
import numpy as np
from dm_sources import bundme,static_check
from phase1260_aj_authenticated_source_digest import load_official,HOURS
NAMES=("GrowthCore","Opportunity","RelativeValue","StressRecovery")
MIN=(4,4,8,4)
def run():
    assert static_check()
    frames,_=load_official()
    signals,updates,regimes,budgets=bundme(
        frames[0],frames[1],frames[2],frames[3],frames[5],frames[6],frames[4])
    years={};passed=True
    for yr,start,end in (("2023",744,9504),("2024",9504,HOURS)):
        years[yr]={}
        for i,name in enumerate(NAMES):
            idx=np.flatnonzero(updates[start:end,i])+start
            active=[int(t) for t in idx if np.any(signals[t,i]) and budgets[t,i]>0]
            ok=len(active)>=MIN[i];passed &=ok
            years[yr][name]={
                "observation_epochs":int(len(idx)),"active_epochs":len(active),
                "minimum":MIN[i],"pass":bool(ok),
                "long_asset_counts":[int(sum(signals[t,i,j]>0 for t in active)) for j in range(4)],
                "short_asset_counts":[int(sum(signals[t,i,j]<0 for t in active)) for j in range(4)]}
    out={"architecture":"DM","decision":"PASS_DM_SOURCE_ONLY" if passed else "REJECT_DM_SOURCE_INACTIVE",
         "historical_training_only":True,"validation_2025_read":False,
         "external_benchmarks_used":False,"trading_authorized":False,"years":years}
    with open("dm_source_viability.json","w") as f:json.dump(out,f,indent=2,sort_keys=True)
    print("DM_SOURCE_VIABILITY",json.dumps(out,sort_keys=True))
    raise SystemExit(0 if passed else 2)
if __name__=="__main__":run()
