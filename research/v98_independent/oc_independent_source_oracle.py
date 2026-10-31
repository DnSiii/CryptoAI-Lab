#!/usr/bin/env python3
"""OC independent 105-decision raw source reconstruction, not an allocator or PnL."""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from oc_sources import bundle
def check(d):
    raw,updates,_=bundle(*(d[k] for k in ("o","h","l","c","q","rate","event")))
    p=np.log(d["c"]);hourly=np.diff(p,axis=0,prepend=p[:1])
    held=np.zeros((4,4));count=core_count=0
    for t in range(WARMUP,HOURS,168):
        def ret(k):return p[t]-p[t-k]
        a,b,v,w,x=ret(672),ret(336),ret(168),ret(72),ret(24)
        if (t-WARMUP)%672==0:
            held[0]=0.
            sigma=np.std(hourly[t-167:t+1],axis=0)*math.sqrt(8760)
            elig=[j for j in range(4) if a[j]>0 and v[j]>0]
            elig.sort(key=lambda j:(-a[j]/(1+4*sigma[j]),j))
            if elig:
                held[0,elig[0]]=.52
                if len(elig)>1:held[0,elig[1]]=.12
            elif v[0]<0 and sum(z<0 for z in v)>=3:
                held[0,0]=-.38
            core_count+=1
        held[1:]=0.
        exp=[]
        for j in range(4):
            recent=np.median(np.abs(hourly[t-23:t+1,j]))
            past=np.median(np.abs(hourly[t-167:t-23,j]))
            exp.append(float(recent/max(past,1e-12)))
        vol=[float(np.sum(d["q"][t-167:t+1,j])/max(np.sum(d["q"][t-335:t-167,j]),1e-12)) for j in range(4)]
        choices=[j for j in range(4) if exp[j]>1.6 and abs(x[j])>.025 and vol[j]>1.]
        if choices:
            j=min(choices,key=lambda k:(-abs(x[k])*exp[k],k))
            held[1,j]=.12 if x[j]>0 else -.12
        btc=hourly[t-335:t+1,0];variance=float(np.var(btc))
        if variance>1e-12:
            beta={}
            for j in (1,2,3):
                alt=hourly[t-335:t+1,j]
                beta[j]=float(np.clip(np.mean((alt-alt.mean())*(btc-btc.mean()))/variance,.2,2.))
            residual={j:float(v[j]-beta[j]*v[0]) for j in beta}
            j=min((1,2,3),key=lambda k:(-abs(residual[k]),k))
            if abs(residual[j])>.06:
                sign=1 if residual[j]>0 else -1
                held[2,j]=-.075*sign;held[2,0]=.075*sign*min(beta[j],1.)
        if w[0]<-.07 and sum(z<0 for z in w)>=3:
            held[3,0]=-.14
        elif v[0]<-.10 and x[0]>.025 and sum(z>0 for z in x[1:])>=2:
            held[3,0]=.14
        if b[0]>0 and sum(z>0 for z in v)>=3:
            held[1:]*=np.array([1.,.75,.5])[:,None]
        else:held[1:]*=np.array([.75,1.,1.])[:,None]
        error=float(np.max(np.abs(raw[t]-held)))
        if error>1e-8 or not updates[t,1:].all() or bool(updates[t,0])!=((t-WARMUP)%672==0):
            raise ValueError("OC_SOURCE_INDEPENDENT_MISMATCH_"+str(t)+"_"+str(error))
        count+=1
    if count!=105 or core_count!=27 or int(d["event"].sum())!=9144:
        raise ValueError("OC_SOURCE_ORACLE_COUNT")
    return {"decision":"PASS_OC_INDEPENDENT_SOURCE_ONLY_NOT_PNL",
            "optional_decisions":count,"core_decisions":core_count,
            "raw_target_mismatches":0,"funding_events":9144,
            "training_only":True,"holdout_accessed":False,"live_authorized":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();out=check(load(a.root))
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
