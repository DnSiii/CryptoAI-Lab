#!/usr/bin/env python3
"""PS independent scalar decision/allocator oracle; no import of PS strategy functions."""
import math
import numpy as np

def independent_decisions(d,primary,targets):
    c=np.asarray(d["c"],float);v=np.asarray(d["q"],float)
    modes={};raws={};previous=[];prev_side=None
    for t in range(1008,27048,24):
        r1=np.log(c[t]/c[t-24]);r3=np.log(c[t]/c[t-72])
        r7=np.log(c[t]/c[t-168]);r14=np.log(c[t]/c[t-336])
        r42=np.log(c[t]/c[t-1008])
        hourly=np.log(c[t-335:t+1]/c[t-336:t])
        sigma=np.maximum(np.sqrt(np.mean((hourly-hourly.mean(axis=0))**2,axis=0))*math.sqrt(336),.05)
        breadth=int(sum(r14>0))
        direction=1 if breadth>=2 else -1
        metric=(r42+.5*r14)/sigma
        if direction==1:
            candidates=sorted([j for j in range(4) if r42[j]>0 and r14[j]>0],key=lambda j:(-metric[j],j))
        else:
            candidates=sorted([j for j in range(4) if r42[j]<0 and r14[j]<0],key=lambda j:(metric[j],j))
        chosen=[]
        for rank in range(2):
            available=[j for j in candidates if j not in chosen]
            if not available:break
            leader=available[0]
            incumbent=previous[rank] if prev_side==direction and rank<len(previous) else None
            if incumbent in available and leader!=incumbent:
                advantage=direction*(metric[leader]-metric[incumbent])
                barrier=max(.02,.25*abs(metric[incumbent]))
                pick=incumbent if advantage<barrier else leader
            else:pick=leader
            chosen.append(pick)
        previous=chosen;prev_side=direction
        raw=np.zeros((4,4))
        for rank,j in enumerate(chosen):
            raw[0,j]=((.36,.18) if direction==1 else (-.32,-.18))[rank]
        ratio=np.sum(v[t-71:t+1],axis=0)/np.maximum(np.sum(v[t-143:t-71],axis=0),1.)
        upper=np.max(c[t-407:t-71],axis=0)
        lower=np.min(c[t-407:t-71],axis=0)
        breakout=[]
        for j in range(4):
            up=c[t,j]>upper[j] and r3[j]>.05
            down=c[t,j]<lower[j] and r3[j]<-.05
            if ratio[j]>=1.2 and (up or down):breakout.append(j)
        if breakout:
            best=min(breakout,key=lambda j:(-abs(r3[j])/sigma[j],j))
            raw[1,best]=.16 if r3[best]>0 else -.16
        best=min(range(4),key=lambda j:(-r7[j],j))
        worst=min(range(4),key=lambda j:(r7[j],j))
        if best!=worst and r7[best]-r7[worst]>=.22 and r1[best]*r1[worst]<0:
            raw[2,worst]=.10;raw[2,best]=-.10
        if breadth<=1 and sum(r1<-.045)>=3:
            worst=min(range(4),key=lambda j:(r3[j],j));raw[3,worst]=-.14
        elif breadth>=3 and sum(r1>.045)>=3 and float(np.median(r3))<-.04:
            best=min(range(4),key=lambda j:(-r1[j],j));raw[3,best]=.14
        mode="risk_off" if breadth<=1 else ("risk_on" if breadth>=3 else "mixed")
        modes[t]=mode;raws[t]=raw
    if len(modes)!=1085 or set(modes)!=set(primary):
        raise ValueError("PS_ORACLE_CLOCK")
    mismatches=0;max_err=0.
    for t in modes:
        expected,mode=primary[t]
        err=float(np.max(np.abs(raws[t]-expected)))
        max_err=max(max_err,err)
        if mode!=modes[t] or err>1e-10:mismatches+=1
    priority={"risk_off":(3,2,1),"risk_on":(1,2,3),"mixed":(2,1,3)}
    books={"PS_full":(0,1,2,3),"PS_core_only":(0,),
           "PS_minus_opportunity":(0,2,3),"PS_minus_RV":(0,1,3),
           "PS_minus_stress":(0,1,2)}
    for name,active in books.items():
        if set(targets[name])!=set(modes):raise ValueError("PS_ORACLE_BOOK_CLOCK")
        for t in modes:
            w=np.zeros((4,4))
            if 0 in active:w[0]=raws[t][0]
            room=min(.28,max(0.,.84-float(np.abs(w).sum())))
            for slot in priority[modes[t]]:
                if slot not in active or room<=1e-12:continue
                gross=float(np.abs(raws[t][slot]).sum())
                if gross<=1e-12:continue
                fraction=min(room,gross)/gross
                w[slot]=raws[t][slot]*fraction
                room-=min(room,gross)
            err=float(np.max(np.abs(w-targets[name][t])))
            max_err=max(max_err,err)
            if err>1e-10:mismatches+=1
    return {"decisions":1085,"books":5,"mismatches":mismatches,
            "max_weight_error":max_err,"independent_implementation":True,
            "source_future_accessed":False}
