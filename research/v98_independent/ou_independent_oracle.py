#!/usr/bin/env python3
"""OU independent signal/allocation oracle; does NOT import OU strategy functions.
Historical Clean-4 TRAINING only; no PnL, benchmark, future or holdout access.
"""
import math
import numpy as np

def independent_decisions(d,primary,targets):
    close=np.asarray(d["c"],float);high=np.asarray(d["h"],float)
    low=np.asarray(d["l"],float);quote=np.asarray(d["q"],float)
    rates=np.asarray(d["rate"],float);events=np.asarray(d["event"],bool)
    independent={}
    books={"OU_full":(0,1,2,3),"OU_core_only":(0,),
           "OU_minus_opportunity":(0,2,3),"OU_minus_RV":(0,1,3),
           "OU_minus_stress":(0,1,2)}
    factors={"shock":(.5,1.,1.),"trend":(1.,.75,.5),"range":(.75,1.,.75)}
    priority={"shock":(3,2,1),"trend":(1,2,3),"range":(2,1,3)}
    for t in range(744,27048,168):
        r14=np.log(close[t]/close[t-336])
        r3=np.log(close[t]/close[t-72])
        r1=np.log(close[t]/close[t-24])
        rhalf=np.log(close[t]/close[t-12])
        h14=np.log(close[t-335:t+1]/close[t-336:t])
        h3=np.log(close[t-71:t+1]/close[t-72:t])
        s14=np.sqrt(np.mean((h14-h14.mean(axis=0))**2,axis=0))
        s3=np.sqrt(np.mean((h3-h3.mean(axis=0))**2,axis=0))
        volratio=float(np.median(s3)/max(float(np.median(s14)),1e-9))
        median=float(np.median(r14))
        aligned=sum(r14>0) if median>0 else (sum(r14<0) if median<0 else 0)
        state="shock" if volratio>=1.25 else ("trend" if aligned>=3 else "range")
        w=np.zeros((4,4))
        candidates=[k for k in range(4) if (r14[k]>0 and r3[k]>0) or (r14[k]<0 and r3[k]<0)]
        if candidates:
            quality=np.abs(r14)/np.maximum(s14*math.sqrt(336),.03)
            k=sorted(candidates,key=lambda z:(-quality[z],z))[0]
            w[0,k]=math.copysign(.62,r14[k])
        burst=quote[t-23:t+1].sum(axis=0)>1.4*quote[t-168:t].sum(axis=0)/7.
        top=close[t]>high[t-72:t].max(axis=0)
        bottom=close[t]<low[t-72:t].min(axis=0)
        candidates=[k for k in range(4) if burst[k] and (top[k] or bottom[k])]
        if candidates:
            k=sorted(candidates,key=lambda z:(-abs(r1[z]),z))[0]
            w[1,k]=.16 if top[k] else -.16
        indices=list(range(t-160,t+1,8))
        if len(indices)!=21 or not np.all(events[indices]):
            raise ValueError("OU_INDEPENDENT_FUNDING_CLOCK")
        avg=np.array([sum(rates[u,k] for u in indices)/21. for k in range(4)])
        payer=sorted(range(4),key=lambda k:(-avg[k],k))[0]
        receiver=sorted(range(4),key=lambda k:(avg[k],k))[0]
        if avg[payer]-avg[receiver]>.00005:
            w[2,payer]=-.12;w[2,receiver]=+.12
        if sum(r1<-.05)>=3 and sum(rhalf>0)>=3:
            k=sorted(range(4),key=lambda z:(r3[z],z))[0]
            w[3,k]=+.16
        elif sum(r1<-.07)>=3 and sum(rhalf<0)>=3:
            k=sorted(range(4),key=lambda z:(r3[z],z))[0]
            w[3,k]=-.16
        for k in (1,2,3):w[k]*=factors[state][k-1]
        independent[t]=(w,state)
    if len(independent)!=157 or set(primary)!=set(independent):
        raise ValueError("OU_INDEPENDENT_DECISION_CALENDAR")
    mismatches=0;max_error=0.
    for t,(w,state) in independent.items():
        actual,actual_state=primary[t]
        err=float(np.max(np.abs(actual-w)))
        max_error=max(max_error,err)
        if actual_state!=state or err>1e-10:mismatches+=1
        for name,active in books.items():
            expected=np.zeros((4,4))
            if 0 in active:expected[0]=w[0]
            room=min(.22,max(0.,.84-float(np.abs(expected).sum())))
            for sleeve in priority[state]:
                if sleeve not in active:continue
                gross=float(np.abs(w[sleeve]).sum())
                if gross>0 and room>0:
                    allocation=min(room,gross)
                    expected[sleeve]=w[sleeve]*(allocation/gross)
                    room-=allocation
            if t not in targets[name]:raise ValueError("OU_INDEPENDENT_TARGET_CLOCK")
            err=float(np.max(np.abs(expected-targets[name][t])))
            max_error=max(max_error,err)
            if err>1e-10:mismatches+=1
    return {"decisions":157,"books":5,
            "signal_and_allocation_mismatches":mismatches,
            "max_weight_error":max_error,
            "independent_implementation":True,
            "source_future_accessed":False}
