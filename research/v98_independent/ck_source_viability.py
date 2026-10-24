#!/usr/bin/env python3
"""CK source-only, preregistered activity viability gate. Never computes PnL."""
from __future__ import annotations
import json,numpy as np
from ck_sources import bundle,BUDGETS
from phase1260_aj_authenticated_source_digest import load_official,HOURS
YEARS={"2023":(744,9504),"2024":(9504,HOURS)}
MODULES=("GrowthCore","Opportunity","RelativeValue","StressRecovery")
MIN={"GrowthCore":4,"Opportunity":4,"RelativeValue":10,"StressRecovery":4}
def main():
    frames,manifest=load_official()
    sig,upd,reg=bundle(frames[3],frames[5],frames[6])
    rows={};passed=True
    for year,(start,end) in YEARS.items():
        rows[year]={}
        for i,name in enumerate(MODULES):
            indices=np.flatnonzero(upd[start:end,i])+start
            nonzero=[int(t) for t in indices if np.any(sig[t,i])]
            effective=[t for t in nonzero if BUDGETS[str(reg[t])][i]>0]
            ok=len(effective)>=MIN[name]
            passed=passed and ok
            rows[year][name]={"scheduled_epochs":int(len(indices)),
              "nonzero_signal_epochs":len(nonzero),
              "effective_epochs":len(effective),"minimum":MIN[name],"pass":ok,
              "long_asset_counts":[int(sum(sig[t,i,j]>0 for t in effective)) for j in range(4)],
              "short_asset_counts":[int(sum(sig[t,i,j]<0 for t in effective)) for j in range(4)]}
    result={"architecture":"CK","decision":"PASS_CK_SOURCE_VIABILITY_ONLY" if passed else "REJECT_CK_SOURCE_INACTIVITY",
      "historical_training_only":True,"validation_2025_read":False,
      "external_benchmarks_used":False,"trading_authorized":False,"years":rows}
    with open("ck_source_viability.json","w") as f:json.dump(result,f,indent=2,sort_keys=True)
    print("CK_SOURCE_VIABILITY",json.dumps(result,sort_keys=True))
    raise SystemExit(0 if passed else 2)
if __name__=="__main__":main()
