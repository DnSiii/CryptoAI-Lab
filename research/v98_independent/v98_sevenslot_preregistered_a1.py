#!/usr/bin/env python3
"""V98 A1 preregistered distinct hypothesis: long-only slow-breakout portfolio.
Frozen before examining A1 economics. A0 rejection is not used for parameter search.
No external engines, future prices, holdout, or 2026+ data. Research only.
Hypothesis: persistent upside capture with slower entry and no systematic short drag.
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
    closes={a:[float(b[3]) for b in data["bars"][a]] for a in ASSETS}
    n=data["hours"]
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        for i in range(n):
            proposals={}
            for a in ASSETS:
                p=closes[a]
                if i<720:
                    proposals[a]=(0.,0.,0.,0.,0.,0.)
                    continue
                ma=sum(p[i-719:i+1])/720
                slow=p[i]/p[i-720]-1
                breakout=p[i]>=max(p[i-168:i])
                ret168=p[i]/p[i-168]-1
                vol=math.sqrt(sum(math.log(p[j]/p[j-1])**2 for j in range(i-167,i+1))/168)
                # Four sleeves: independent roles; all long-only by preregistration.
                growth=0.15 if p[i]>ma and slow>0 else 0.
                opportunity=0.075 if breakout and slow>0 else 0.
                relative=0.05 if ret168>0 else 0.
                # Recovery only after a drawdown with regained slow trend.
                dd=p[i]/max(p[i-719:i+1])-1
                recovery=0.025 if -0.25<dd<-0.08 and p[i]>ma else 0.
                # Regime router suppresses extreme realized turbulence.
                router=0.5 if vol>0.035 else 1.
                proposals[a]=(growth,opportunity,relative,recovery,router,vol)
            raw=sum(sum(proposals[a][:4])*proposals[a][4] for a in ASSETS)
            allocator=min(1.,0.8/raw) if raw else 1.
            for a in ASSETS:
                g,o,r,s,router,vol=proposals[a]
                governor=0.3
                if (g+o+r+s)*router*allocator>governor+1e-12: raise ValueError("GOVERNOR_BREACH")
                writer.writerow(dict(zip(FIELDS,(a,START_MS+i*HOUR_MS,g,o,r,s,router,allocator,governor))))
    return {"rows":n*len(ASSETS),"hours":n,"status":"A1_UNVALIDATED"}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in ("prices","manifest","funding","output"):p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    print(generate(a.prices,a.manifest,a.funding,a.output))
