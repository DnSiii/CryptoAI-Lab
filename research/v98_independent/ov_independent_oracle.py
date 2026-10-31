#!/usr/bin/env python3
"""V98 OV independent BTC-led signal and allocation reconstruction.
Does not import the OV primary strategy or use its signal/allocator functions.
"""
import numpy as np

def independent_decisions(d,primary,targets):
    price=np.asarray(d["c"],float)
    states={}
    books={"OV_full":(0,1,2,3),"OV_core_only":(0,),
           "OV_minus_opportunity":(0,2,3),"OV_minus_RV":(0,1,3),
           "OV_minus_stress":(0,1,2)}
    order={"panic":(3,1,2),"propagation":(1,2,3),"transition":(2,3,1)}
    factors={"panic":(.5,.5,1.),"propagation":(1.,.75,.5),"transition":(.75,1.,.75)}
    mismatches=0;maxerr=0.
    for t in range(744,27048,168):
        def returns(n):return np.log(price[t]/price[t-n])
        r21=returns(504);r14=returns(336);r7=returns(168)
        r3=returns(72);r1=returns(24);rhalf=returns(12)
        up=bool(r21[0]>0 and r7[0]>0)
        down=bool(r21[0]<0 and r7[0]<0)
        mode="panic" if r3[0]<-.10 else ("propagation" if up or down else "transition")
        raw=np.zeros((4,4))
        if up:
            choices=sorted((j for j in range(4) if r7[j]>0),key=lambda j:(-r21[j],j))
            for j,v in zip(choices[:2],(.40,.22)):raw[0,j]=v
        elif down:
            choices=sorted((j for j in range(4) if r7[j]<0),key=lambda j:(r21[j],j))
            for j,v in zip(choices[:2],(-.35,-.20)):raw[0,j]=v
        if r1[0]>.025 and r3[0]>.045:
            choices=sorted((j for j in range(1,4) if r3[0]-r3[j]>=.04 and r1[j]>0),
                           key=lambda j:(r3[j],j))
            if choices:raw[1,choices[0]]=.16
        elif r1[0]<-.025 and r3[0]<-.045:
            choices=sorted((j for j in range(1,4) if r3[j]-r3[0]>=.04 and r1[j]<0),
                           key=lambda j:(-r3[j],j))
            if choices:raw[1,choices[0]]=-.16
        strongest=sorted((1,2,3),key=lambda j:(-r14[j],j))[0]
        weakest=sorted((1,2,3),key=lambda j:(r14[j],j))[0]
        if r14[strongest]-r14[weakest]>.14:
            if r14[0]>0:
                raw[2,strongest]=.10;raw[2,weakest]=-.10
            elif r14[0]<0:
                raw[2,strongest]=-.10;raw[2,weakest]=.10
        if r3[0]<-.10 and rhalf[0]>.025 and np.count_nonzero(rhalf[1:]>0)>=2:
            raw[3,0]=.16
        elif r3[0]<-.10 and rhalf[0]<-.025 and np.count_nonzero(rhalf[1:]<0)>=2:
            raw[3,0]=-.16
        for k,v in enumerate(factors[mode],start=1):raw[k]*=v
        if t not in primary:
            mismatches+=1
        else:
            x,s=primary[t]
            err=float(np.max(np.abs(x-raw)))
            maxerr=max(maxerr,err)
            if s!=mode or err>1e-10:mismatches+=1
        for book,active in books.items():
            weights=np.zeros((4,4))
            if 0 in active:weights[0]=raw[0]
            available=min(.24,max(0.,.84-float(np.abs(weights).sum())))
            for slot in order[mode]:
                if slot not in active:continue
                exposure=float(np.abs(raw[slot]).sum())
                if exposure and available:
                    scale=min(1.,available/exposure)
                    weights[slot]=raw[slot]*scale
                    available-=exposure*scale
            if book not in targets or t not in targets[book]:
                mismatches+=1
            else:
                err=float(np.max(np.abs(weights-targets[book][t])))
                maxerr=max(maxerr,err)
                if err>1e-10:mismatches+=1
            if np.abs(weights).sum()>.84+1e-10 or np.abs(weights[1:]).sum()>.24+1e-10:
                mismatches+=1
        states[mode]=states.get(mode,0)+1
    return {"independent_weekly_decisions":157,"books":5,
            "signal_and_allocation_mismatches":mismatches,
            "max_absolute_weight_error":maxerr,
            "regime_counts":states,"no_future_data_accessed":True,
            "independent_of_primary_signal_code":True}
