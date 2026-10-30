#!/usr/bin/env python3
"""GQ preregistered source-only distinct ewent activity gate, no system PnL."""
import json
import numpy as np
from gq_sources import bundle,static_check
from phase1260_aj_authenticated_source_digest import load_official,HOURS
NAMES=("GrowthCore","Opportunity","RelativeValue","StressRecovery")
MIN=(4,4,4,4)
def run():
    assert static_check()
    frames,manifest=load_official()
    signals,updates,regimes,budgets=bundle(
        frames[0],frames[1],frames[2],frames[3],frames[5],frames[6],frames[4])
    years={};passed=True
    for yr,start,end in (("2023",744,9504),("2024",9504,HOURS)):
        years[yr]={}
        for i,name in enumerate(NAMES):
            idx=np.flatnonzero(updates[start:end,i])+start
            active=[int(t) for t in idx if np.any(signals[t,i]) and budgets[t,i]>0]
            ok=len(active)>=MIN[i];passed &=ok
            years[yr][name]={"observation_epochs":len(idx),
                "active_epochs":len(active),"minimum":MIN[i],"pass":bool(ok),
                "long_asset_counts":[int(sum(signals[t,i,j]>0 for t in active)) for j in range(4)],
                "short_asset_counts":[int(sum(signals[t,i,j]<0 for t in active)) for j in range(4)]}
    out={"architecture":"GQ","decision":"PASS_GQ_SOURCE_ONLY" if passed else "REJECT_GQ_SOURCE_INACTIVE",
         "historical_training_only":True,"validation_2025_read":False,
         "external_benchmarks_used":False,"trading_authorized":False,"years":years}
    with open("gq_source_viability.json","w") as f:json.dump(out,f,indent=2,sort_keys=True)
    print("GQ_SOURCE_VIABILITY",json.dumps(out,sort_keys=True))
    raise SystemExit(0 if passed else 2)
if __name__=="__main__":run()
