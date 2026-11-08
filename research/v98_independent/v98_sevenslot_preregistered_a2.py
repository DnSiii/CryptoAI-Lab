#!/usr/bin/env python3
"""V98 A2 preregistered cross-sectional rotation, distinct from A1.
No benchmark engines, no 2026+ training, no holdout. Causal t-1 execution.
Seven slots: growth, opportunity, relative value, recovery, router, allocator, governor.
Fixed ex-ante rules: weekly rotation, rank-based concentration, volatility-scaled exposure.
"""
import argparse,csv,math
from pathlib import Path
from research.v98_independent.v98_phase243_training_reader import load,START_MS
from research.v98_independent.phase243_native_funding_cashflow import ASSETS,HOUR_MS
from research.v98_independent.v98_sevenslot_weight_to_targets import FIELDS

def generate(prices,manifest,funding,output):
    output=Path(output)
    if "v98_independent" not in output.absolute().parts: raise ValueError("V98_NAMESPACE_REQUIRED")
    data=load(prices,manifest,funding)
    close={a:[float(b[3]) for b in data["bars"][a]] for a in ASSETS}
    n=data["hours"]
    output.parent.mkdir(parents=True,exist_ok=True)
    state={a:(0.,0.,0.,0.,0.,0.) for a in ASSETS}
    with output.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
        for i in range(n):
            # Weekly decisions based solely on the current and previous completed bars.
            if i>=720 and i%168==0:
                scores={}
                for a in ASSETS:
                    p=close[a]
                    trend=p[i]/p[i-720]-1.
                    recent=p[i]/p[i-168]-1.
                    daily=[math.log(p[j]/p[j-1]) for j in range(i-167,i+1)]
                    vol=math.sqrt(sum(x*x for x in daily)/len(daily))
                    scores[a]=(trend,recent,vol)
                # Ranking is cross-sectional; fixed top two, no optimized thresholds.
                eligible=sorted((a for a in ASSETS if scores[a][0]>0 and scores[a][1]>0),
                                key=lambda a:(-scores[a][1],a))[:2]
                state={}
                for rank,a in enumerate(eligible):
                    trend,recent,vol=scores[a]
                    growth=0.22 if rank==0 else 0.12
                    opportunity=0.06 if recent>trend/4 else 0.
                    relative=0.06 if rank==0 else 0.
                    # Stress/recovery sleeve activates only after medium-term drawdown.
                    p=close[a]
                    dd=p[i]/max(p[i-336:i+1])-1.
                    recovery=0.04 if -0.20<dd<-0.07 else 0.
                    router=0.5 if vol>0.035 else 1.
                    state[a]=(growth,opportunity,relative,recovery,router,vol)
                for a in ASSETS:
                    state.setdefault(a,(0.,0.,0.,0.,0.,0.))
            raw=sum(sum(state[a][:4])*state[a][4] for a in ASSETS)
            allocator=min(1.,0.75/raw) if raw else 1.
            for a in ASSETS:
                g,o,r,s,router,_=state[a]
                governor=0.4
                if (g+o+r+s)*router*allocator>governor+1e-12:
                    raise ValueError("GOVERNOR_BREACH")
                w.writerow(dict(zip(FIELDS,(a,START_MS+i*HOUR_MS,g,o,r,s,router,allocator,governor))))
    return {"hours":n,"rows":n*len(ASSETS),"status":"A2_UNVALIDATED"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in ("prices","manifest","funding","output"):p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    print(generate(a.prices,a.manifest,a.funding,a.output))
