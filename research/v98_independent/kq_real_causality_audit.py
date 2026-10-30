#!/usr/bin/env python3
"""KQ independent authenticated historical future-mutation firewall, source only; no PnL."""
from __future__ import annotations
import hashlib,json
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from kq_dual_trend_native_relative_sources import bundle,WARMUP

def run():
    frames,manifest=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    baseline=bundle(o,h,l,c,r,e,q)
    cut=14000
    oo,hh,ll,cc,qq,rr=[x.copy() for x in (o,h,l,c,q,r)]
    for x in (oo,hh,ll,cc):x[cut:]*=1.27
    qq[cut:]*=3.5;rr[cut:]*=-1
    altered=bundle(oo,hh,ll,cc,rr,e,qq)
    errors=[]
    for i,name in enumerate(("intents","updates","entries","valid","regimes")):
        if not np.array_equal(baseline[i][:cut],altered[i][:cut]):
            errors.append("FUTURE_LEAK_"+name)
    if np.any(baseline[1][:WARMUP]):errors.append("WARMUP_UPDATE")
    if not np.any(baseline[1][WARMUP:cut]):errors.append("NO_REAL_HISTORICAL_UPDATES")
    out={"architecture":"KQ","source_only":True,"system_pnl_computed":False,
         "historical_training_only":True,"validation_2025_read":False,
         "future_holdout_read":False,"external_benchmarks_read":False,
         "hours":HOURS,"future_mutation_cut":cut,
         "manifest_sha256":hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),
         "verified_prefix_hours":cut,"errors":errors,
         "decision":"PASS_KQ_AUTHENTICATED_FUTURE_MUTATION" if not errors else "BLOCK_KQ_CAUSAL_SOURCE"}
    print("KQ_REAL_HISTORY_CAUSAL",json.dumps(out,sort_keys=True))
    return out
if __name__=="__main__":
    report=run()
    from pathlib import Path
    Path("kq_real_causality_audit.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    raise SystemExit(0 if not report["errors"] else 2)
