#!/usr/bin/env python3
"""V98 physical capacity geometry, historical source-only; no alpha, PnL, holdout or orders."""
from __future__ import annotations
import argparse,json,hashlib
import numpy as np
from phase1260_aj_authenticated_source_digest import load_official,HOURS
from gl_order_invariant_governor import GLOrderInvariantBufferedGovernor
from cg_buffered_governor import buffered_safe
from v98_staged_exit_viability_governor_v2 import FEES,ORDERS,prior_min_exit_window_quote

WARMUP=744
CLOCK=168
CASH=10000.
REQUEST=.74
WEIGHTS={
 "btc_only":np.array([1.,0.,0.,0.]),
 "btc_eth":np.array([.5,.5,0.,0.]),
 "equal4":np.full(4,.25),
 "tapered4":np.array([.5,.25,.15,.1]),
}
def percentile(a):
    return {"p10":float(np.quantile(a,.1)),"median":float(np.median(a)),
            "p90":float(np.quantile(a,.9)),"min":float(np.min(a)),
            "max":float(np.max(a))}
def run():
    frames,manifest=load_official()
    o,h,l,c,q,r,e,ml,mh=frames
    samples=list(range(WARMUP,HOURS,CLOCK))
    rows={name:{fee:[] for fee in FEES} for name in WEIGHTS}
    source_sha=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    checked=0
    for t in samples:
        down=np.maximum(.40,np.max(1.-l[t-336:t]/o[t-336:t],axis=0))
        up=np.maximum(.65,np.max(h[t-336:t]/o[t-336:t]-1.,axis=0))
        f=np.maximum(.0005,3.*np.max(np.abs(r[t-672:t]*e[t-672:t]),axis=0))
        exitq=prior_min_exit_window_quote(q,t)
        for name,weights in WEIGHTS.items():
            for fee in FEES:
                order_results=[]
                for order in ORDERS:
                    g=GLOrderInvariantBufferedGovernor()
                    g.signal_components(REQUEST*CASH*weights/o[t])
                    n=g.trade(CASH,np.zeros(4),c[t-1],o[t],down,up,f,q[t-1],exitq,
                              fee_mode=fee,funding_order=order)
                    if (not np.isfinite(n).all() or np.any(n<-1e-9) or
                        not buffered_safe(CASH,np.zeros(4),c[t-1],o[t],n,down,up,f,
                                          exitq,fee,"carried_before_fill")):
                        raise ValueError("GEOMETRY_UNSAFE_AUTHORIZATION")
                    order_results.append(n)
                    checked+=1
                if not np.allclose(order_results[0],order_results[1],rtol=0,atol=1e-10):
                    raise ValueError("GEOMETRY_FUNDING_ORDER_CHANGED_AUTHORIZATION")
                n=order_results[0]
                gross=float(n@o[t])
                rows[name][fee].append({"ratio":gross/(REQUEST*CASH),
                                         "gross":gross,
                                         "requested":REQUEST*CASH,
                                         "concentration":float(np.max(n*o[t])/gross) if gross>0 else 0.})
    summary={}
    for name,by_fee in rows.items():
        summary[name]={}
        for fee,points in by_fee.items():
            summary[name][fee]={"authorization_ratio":percentile([x["ratio"] for x in points]),
                "authorized_gross_usd":percentile([x["gross"] for x in points]),
                "single_asset_concentration":percentile([x["concentration"] for x in points]),
                "samples":len(points)}
    out={"audit":"V98_NO_PNL_PHYSICAL_AUTHORIZATION_GEOMETRY",
         "historical_training_only":True,"validation_2025_read":False,
         "external_benchmarks_used":False,"trading_authorized":False,
         "source_manifest_sha256":source_sha,
         "sample_count":len(samples),"authorization_checks":checked,
         "requested_gross_to_nav":REQUEST,"results":summary,
         "decision":"PASS_GEOMETRY_AUDIT_ONLY_NO_PNL"}
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True);a=p.parse_args()
    out=run()
    with open(a.output,"w") as f:json.dump(out,f,indent=2,sort_keys=True,allow_nan=False)
    print("V98_GEOMETRY",out["decision"],"checks",out["authorization_checks"])
    for name,rows in out["results"].items():
        print(name,[(fee,round(v["authorization_ratio"]["median"],5),
                          round(v["authorization_ratio"]["p10"],5)) for fee,v in rows.items()])
