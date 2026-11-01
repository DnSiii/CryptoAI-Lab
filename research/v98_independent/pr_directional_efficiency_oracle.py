#!/usr/bin/env python3
"""PR independent scalar path-efficiency and allocator oracle; never imports primary PR."""
import math
import numpy as np
CLOCK=tuple(range(744,27048,168))
BOOKS={"PR_full":(0,1,2,3),"PR_core_only":(0,),"PR_minus_opportunity":(0,2,3),
       "PR_minus_RV":(0,1,3),"PR_minus_stress":(0,1,2)}
PRIORITY={"stress":(3,1,2),"release":(1,2,3),"normal":(2,1,3)}
def independent_decisions(d,primary,books):
    c=np.asarray(d["c"],float);q=np.asarray(d["q"],float)
    mismatches=0;max_error=0.;activations={1:0,2:0,3:0}
    for t in CLOCK:
        r24=[];r72=[];r168=[];r336=[];er336=[];er72=[];sigma=[];compression=[];volume=[]
        for j in range(4):
            close=lambda k:float(c[k,j])
            r24.append(math.log(close(t)/close(t-24)))
            r72.append(math.log(close(t)/close(t-72)))
            r168.append(math.log(close(t)/close(t-168)))
            r336.append(math.log(close(t)/close(t-336)))
            changes336=[math.log(close(k)/close(k-1)) for k in range(t-335,t+1)]
            changes72=changes336[-72:]
            er336.append(abs(r336[-1])/max(sum(abs(v) for v in changes336),1e-8))
            er72.append(abs(r72[-1])/max(sum(abs(v) for v in changes72),1e-8))
            changes168=changes336[-168:]
            changes504=[math.log(close(k)/close(k-1)) for k in range(t-503,t+1)]
            mean168=sum(changes168)/168.;mean504=sum(changes504)/504.
            std168=math.sqrt(sum((v-mean168)**2 for v in changes168)/168.)
            std504=math.sqrt(sum((v-mean504)**2 for v in changes504)/504.)
            sigma.append(max(std168*math.sqrt(168),.04))
            compression.append(min(4.,std168/max(std504,1e-8)))
            recent=sum(float(q[k,j]) for k in range(t-71,t+1))
            earlier=sum(float(q[k,j]) for k in range(t-143,t-71))
            volume.append(min(4.,recent/max(earlier,1.)))
        breadth=sum(v>0 for v in r168)
        raw=np.zeros((4,4),float)
        if breadth>=2:
            eligible=[j for j in range(4) if r336[j]>0 and er336[j]>=.12]
            eligible.sort(key=lambda j:(-r336[j]*er336[j]/sigma[j],j))
            for j,w in zip(eligible[:2],(.36,.18)):raw[0,j]=w
        else:
            eligible=[j for j in range(4) if r336[j]<0 and er336[j]>=.12]
            eligible.sort(key=lambda j:(r336[j]*er336[j]/sigma[j],j))
            for j,w in zip(eligible[:2],(-.34,-.16)):raw[0,j]=w
        eligible=[j for j in range(4) if er72[j]>=.18 and volume[j]>=1.15 and abs(r72[j])>=.035 and r72[j]*r336[j]>0]
        eligible.sort(key=lambda j:(-abs(r72[j])*er72[j]*volume[j],j))
        if eligible:raw[1,eligible[0]]=.17 if r72[eligible[0]]>0 else -.17
        high=min((1,2,3),key=lambda j:(-er72[j],j))
        low=min((1,2,3),key=lambda j:(er72[j],j))
        if high!=low and er72[high]-er72[low]>=.10 and abs(r168[high]-r168[low])<=.14:
            raw[2,low]=.11;raw[2,high]=-.11
        if breadth<=1 and float(np.median(r24))<-.035:
            recovery=[j for j in range(4) if r24[j]>0 and er72[j]>=.12]
            recovery.sort(key=lambda j:(-r24[j],j))
            if recovery:raw[3,recovery[0]]=.15
            elif r24[0]<-.05:raw[3,0]=-.13
        elif breadth>=3 and float(np.median(compression))<.65 and float(np.median(r24))>.025:
            j=min(range(4),key=lambda j:(-r24[j],j));raw[3,j]=.15
        mode=("stress" if breadth<=1 and float(np.median(r24))<-.035 else
              "release" if float(np.median(compression))<.75 and breadth>=2 else "normal")
        expected,primary_mode=primary[t]
        error=float(np.max(np.abs(expected-raw)));max_error=max(max_error,error)
        if error>1e-10 or mode!=primary_mode:mismatches+=1
        for slot in (1,2,3):
            if np.any(raw[slot]):activations[slot]+=1
        for name,active in BOOKS.items():
            weights=np.zeros((4,4),float)
            if 0 in active:weights[0]=raw[0]
            remaining=min(.30,max(0.,.84-float(np.abs(weights).sum())))
            for slot in PRIORITY[mode]:
                if slot not in active or remaining<=1e-12:continue
                gross=sum(abs(float(x)) for x in raw[slot])
                if gross>1e-12:
                    take=min(remaining,gross)
                    weights[slot]=raw[slot]*(take/gross)
                    remaining-=take
            error=float(np.max(np.abs(weights-books[name][t])));max_error=max(max_error,error)
            if error>1e-10:mismatches+=1
    return {"decisions":157,"books":5,"mismatches":mismatches,
            "max_weight_error":max_error,"raw_optional_activations":activations,
            "independent_implementation":True,"future_2026_accessed":False}
