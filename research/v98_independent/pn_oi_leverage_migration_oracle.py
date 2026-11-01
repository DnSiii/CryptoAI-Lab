#!/usr/bin/env python3
"""Independent PN scalar/vector decision reconstruction from preregistered specification.
Does not import PN primary signal/allocator or any rejected strategy alpha.
"""
import math
import numpy as np

CLOCK=tuple(range(744,27048,168))
BOOKS={"PN_full":(0,1,2,3),"PN_core_only":(0,),
       "PN_minus_opportunity":(0,2,3),"PN_minus_RV":(0,1,3),
       "PN_minus_stress":(0,1,2)}

def independent_decisions(d,bridge,primary,books):
    c=np.asarray(d["c"],float)
    oi=np.asarray(bridge["oi"],float)
    observed=np.asarray(bridge["observed"],bool)
    independent={}
    for t in CLOCK:
        returns168=np.log(c[t]/c[t-168])
        returns336=np.log(c[t]/c[t-336])
        returns72=np.log(c[t]/c[t-72])
        h=np.log(c[t-167:t+1]/c[t-168:t])
        sigma=np.sqrt(np.mean((h-h.mean(axis=0))**2,axis=0))*math.sqrt(168)
        breadth=sum(x>0 for x in returns168)
        raw=np.zeros((4,4),float)
        if breadth>=2:
            candidates=[k for k in range(4) if returns336[k]>0 and returns168[k]>0]
            candidates.sort(key=lambda k:(-returns336[k]/max(float(sigma[k]),.06),k))
            for k,w in zip(candidates[:2],(.40,.22)):raw[0,k]=w
        valid=bool(observed[t-167:t+1].all())
        if valid:
            change=np.log(oi[t]/oi[t-167])
            expanding=sum(x>0 for x in change)
            eligible=[k for k in range(4) if change[k]>.035 and
                      returns72[k]>0 and returns168[k]>0]
            if eligible:
                best=min(eligible,key=lambda k:(-(returns72[k]+.5*change[k]),k))
                raw[1,best]=.16
            divergence=change-returns168
            highest=min(range(4),key=lambda k:(-divergence[k],k))
            lowest=min(range(4),key=lambda k:(divergence[k],k))
            if (highest!=lowest and divergence[highest]-divergence[lowest]>.09 and
                returns72[highest]>0 and returns72[lowest]<0):
                raw[2,highest]=.09;raw[2,lowest]=-.09
            if expanding<=1 and breadth<=1 and returns168[0]<-.08:
                raw[3,0]=-.14
            elif expanding<=1 and breadth>=3 and returns72[0]>.025:
                raw[3,0]=.14
            regime=("expansion" if breadth>=3 and expanding>=2 else
                    "defense" if breadth<=1 or expanding<=1 else "transition")
        else:
            regime=("expansion" if breadth>=3 else
                    "defense" if breadth<=1 else "transition")
        independent[t]=(raw,regime,valid)
    if len(independent)!=157 or sum(x[2] for x in independent.values())!=143:
        raise ValueError("PN_ORACLE_SOURCE_CLOCK")
    mismatch=0;maximum=0.
    if set(primary)!=set(independent):raise ValueError("PN_ORACLE_PRIMARY_CLOCK")
    for t in CLOCK:
        expected=independent[t]
        got=primary[t]
        err=float(np.max(np.abs(expected[0]-got[0])))
        maximum=max(maximum,err)
        if err>1e-10 or expected[1:]!=got[1:]:mismatch+=1
        if not expected[2] and np.any(got[0][1:]!=0):mismatch+=1
    priority={"expansion":(1,2,3),"defense":(3,2,1),"transition":(2,1,3)}
    for book,slots in BOOKS.items():
        if set(books[book])!=set(CLOCK):raise ValueError("PN_ORACLE_BOOK_CLOCK")
        for t in CLOCK:
            raw,mode,_=independent[t]
            expected=np.zeros((4,4))
            expected[0]=raw[0]
            left=min(.24,max(0.,.84-float(np.abs(expected).sum())))
            for slot in priority[mode]:
                if slot not in slots or left<=0:continue
                exposure=float(np.abs(raw[slot]).sum())
                if exposure>0:
                    amount=min(exposure,left)
                    expected[slot]=raw[slot]*amount/exposure
                    left-=amount
            err=float(np.max(np.abs(expected-books[book][t])))
            maximum=max(maximum,err)
            if err>1e-10:mismatch+=1
    return {"decisions":157,"books":5,"oi_eligible":143,"oi_blocked":14,
            "mismatches":mismatch,"max_weight_error":maximum,
            "independent_implementation":True,"future_2026_accessed":False}
