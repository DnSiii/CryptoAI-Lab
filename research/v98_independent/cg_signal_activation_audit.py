#!/usr/bin/env python3
"""CG frozen original source activation diagnostic only; no tuning or reruns."""
from __future__ import annotations
import json,numpy as np
from cg_sources import bundle,BUDGETS,WARMUP
from phase1260_aj_authenticated_source_digest import load_official,HOURS
YEARS={"2023":(744,9504),"2024":(9504,HOURS)}
MODULES=("GrowthCore","Opportunity","RelativeValue","StressRecovery")
def main():
    frames,manifest=load_official()
    sig,upd,reg=bundle(frames[3],frames[5],frames[6])
    rows={}
    for year,(start,end) in YEARS.items():
        rows[year]={}
        for i,name in enumerate(MODULES):
            indices=np.flatnonzero(upd[start:end,i])+start
            nonzero=[int(t) for t in indices if np.any(sig[t,i])]
            budgets=[float(BUDGETS[str(reg[t])][i]) for t in nonzero]
            nonzero_effective=[t for t,b in zip(nonzero,budgets) if b>0]
            long=[int(np.sum(sig[nonzero_effective,i,j]>0)) for j in range(4)] if nonzero_effective else [0]*4
            short=[int(np.sum(sig[nonzero_effective,i,j]<0)) for j in range(4)] if nonzero_effective else [0]*4
            rows[year][name]={"scheduled_epochs":int(len(indices)),
              "nonzero_signal_epochs":len(nonzero),
              "positive_budget_epochs":len(nonzero_effective),
              "positive_by_asset":long,"negative_by_asset":short}
    result={"architecture":"CG","decision":"SOURCE_ACTIVATION_DIAGNOSTIC_ONLY_NO_ENGINE_APPROVAL",
      "historical_training_only":True,"validation_2025_read":False,
      "external_benchmarks_used":False,"trading_authorized":False,"years":rows}
    with open("cg_activation_audit.json","w") as f:json.dump(result,f,indent=2,sort_keys=True)
    print("CG_ACTIVATION_AUDIT",json.dumps(rows,sort_keys=True))
if __name__=="__main__":main()
