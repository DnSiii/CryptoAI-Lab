#!/usr/bin/env python3
"""Independent V98 OZ decision + allocator oracle. Does not import OZ engine."""
import math
import numpy as np

def independent_decisions(d,primary,targets):
    c=np.asarray(d["c"],float)
    expected={};modes={}
    for t in range(744,27048,168):
        raw=np.zeros((4,4),float)
        if t<1344:
            expected[t]=raw;modes[t]="transition";continue
        r56=[math.log(c[t,j]/c[t-1344,j]) for j in range(4)]
        r28=[math.log(c[t,j]/c[t-672,j]) for j in range(4)]
        r7=[math.log(c[t,j]/c[t-168,j]) for j in range(4)]
        r1=[math.log(c[t,j]/c[t-24,j]) for j in range(4)]
        vol=[];scores=[]
        for j in range(4):
            changes=[math.log(c[h,j]/c[h-1,j]) for h in range(t-671,t+1)]
            mu=sum(changes)/len(changes)
            variance=sum((x-mu)**2 for x in changes)/len(changes)
            vol.append(math.sqrt(variance)*math.sqrt(24*365.25))
            scores.append(.6*r56[j]+.4*r28[j])
        mode=("trend" if r28[0]>0 and sum(s>0 for s in scores)>=2 else
              "stress" if r28[0]<0 and sum(v<0 for v in r28)>=3 else "transition")
        if mode=="trend":
            ranked=sorted((j for j in range(4) if scores[j]>0),
                          key=lambda j:(-scores[j]/max(vol[j],.04),j))
            for j,w in zip(ranked[:2],(.42,.25)):raw[0,j]=w
        elif mode=="stress":
            raw[0,0]=-.35
            raw[0,min((1,2,3),key=lambda j:(r28[j],j))]=-.18
        elif r7[0]>0 and r28[0]>0:
            raw[0,0]=.20
        breakout=[]
        for j in (1,2,3):
            prior=max(math.log(float(c[h,j])) for h in range(t-168,t))
            sample=[math.log(float(c[h,j])) for h in range(t-167,t+1)]
            if max(sample)-min(sample)<.20 and math.log(float(c[t,j]))>prior and scores[j]>0 and r1[j]>0:
                breakout.append(j)
        if breakout:
            raw[1,min(breakout,key=lambda j:(-scores[j],j))]=.16
        hi=min((1,2,3),key=lambda j:(-r28[j],j))
        lo=min((1,2,3),key=lambda j:(r28[j],j))
        if hi!=lo and r28[hi]-r28[lo]>.30 and r7[hi]>0 and r7[lo]<0 and r28[0]>0:
            raw[2,hi]=.10;raw[2,lo]=-.10
        btc_peak=max(float(c[h,0]) for h in range(t-672,t+1))
        if math.log(float(c[t,0])/btc_peak)<math.log(.80) and sum(v<0 for v in r7)>=3:
            raw[3,0]=-.16
        elif r7[0]<-.12 and r1[0]>0 and sum(v>0 for v in r1)>=3:
            raw[3,0]=.16
        multipliers={"trend":(1.,1.,.5),"stress":(.5,.5,1.),"transition":(.5,.75,.75)}[mode]
        for k in (1,2,3):raw[k]*=multipliers[k-1]
        expected[t]=raw;modes[t]=mode
    if len(expected)!=157 or set(expected)!=set(primary):
        raise ValueError("OZ_ORACLE_CLOCK")
    mismatches=0;max_error=0.
    for t in expected:
        observed,mode=primary[t]
        err=float(np.max(np.abs(observed-expected[t])))
        max_error=max(max_error,err)
        if err>1e-10 or mode!=modes[t]:mismatches+=1
    books={"OZ_full":(0,1,2,3),"OZ_core_only":(0,),
           "OZ_minus_opportunity":(0,2,3),"OZ_minus_RV":(0,1,3),
           "OZ_minus_stress":(0,1,2)}
    priorities={"trend":(1,2,3),"stress":(3,2,1),"transition":(3,1,2)}
    if set(targets)!=set(books):raise ValueError("OZ_ORACLE_BOOKS")
    for name,active in books.items():
        if set(targets[name])!=set(expected):raise ValueError("OZ_ORACLE_BOOK_CLOCK")
        for t,raw in expected.items():
            w=np.zeros((4,4),float)
            w[0]=raw[0]
            room=min(.28,max(0.,.84-float(np.abs(w).sum())))
            for k in priorities[modes[t]]:
                if k not in active:continue
                gross=float(np.abs(raw[k]).sum())
                if gross>0 and room>0:
                    portion=min(room,gross)
                    w[k]=raw[k]*portion/gross
                    room-=portion
            err=float(np.max(np.abs(w-targets[name][t])))
            max_error=max(max_error,err)
            if err>1e-10:mismatches+=1
    return {"decisions":157,"books":5,"signal_and_allocation_mismatches":mismatches,
            "max_weight_error":max_error,"source_future_accessed":False,
            "independent_implementation":True,"cold_start_cash_decisions":4}
