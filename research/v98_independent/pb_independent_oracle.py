#!/usr/bin/env python3
"""V98 PB independent loop oracle: does not import PB engine or its constants."""
import math
import numpy as np

def independent_decisions(d,primary,targets):
    close=np.asarray(d["c"],float)
    rate=np.asarray(d["rate"],float)
    expected={};modes={}
    for t in range(744,27048,168):
        ret28=[math.log(float(close[t,j])/float(close[t-672,j])) for j in range(4)]
        ret7=[math.log(float(close[t,j])/float(close[t-168,j])) for j in range(4)]
        ret1=[math.log(float(close[t,j])/float(close[t-24,j])) for j in range(4)]
        # Explicit event loop; no rates at t or after t.
        funding=[sum(float(rate[k,j]) for k in range(t-168,t,8))/21. for j in range(4)]
        score=[ret28[j]+.65*ret7[j]-120.*funding[j] for j in range(4)]
        positives=sum(x>0 for x in ret7)
        negatives=sum(x<0 for x in ret7)
        mode=("risk_on" if positives>=3 and ret7[0]>0 else
              "risk_off" if negatives>=3 and ret7[0]<0 else "mixed")
        w=np.zeros((4,4),float)
        if mode=="risk_on":
            order=sorted((j for j in range(4) if score[j]>0),key=lambda j:(-score[j],j))
            for j,size in zip(order[:2],(.50,.18)):w[0,j]=size
        elif mode=="risk_off":
            order=sorted((j for j in range(4) if score[j]<0),key=lambda j:(score[j],j))
            for j,size in zip(order[:2],(-.42,-.20)):w[0,j]=size
        else:
            top=min(range(4),key=lambda j:(-score[j],j))
            bottom=min(range(4),key=lambda j:(score[j],j))
            if score[top]>0 and ret7[top]>0:w[0,top]=.35
            elif score[bottom]<0 and ret7[bottom]<0:w[0,bottom]=-.30
        long_candidates=[j for j in (1,2,3) if funding[j]<-.00005 and ret1[j]>.04 and ret7[j]>0]
        short_candidates=[j for j in (1,2,3) if funding[j]>.00015 and ret1[j]<-.05 and ret7[j]<0]
        if long_candidates:w[1,min(long_candidates,key=lambda j:(-ret1[j],j))]=.20
        elif short_candidates:w[1,min(short_candidates,key=lambda j:(ret1[j],j))]=-.20
        cheap=min((1,2,3),key=lambda j:(funding[j],j))
        expensive=min((1,2,3),key=lambda j:(-funding[j],j))
        if (cheap!=expensive and funding[expensive]-funding[cheap]>.00015
            and ret7[cheap]-ret7[expensive]>.04 and ret7[cheap]>0):
            w[2,cheap]=.12;w[2,expensive]=-.12
        if ret7[0]<-.10 and negatives>=3:w[3,0]=-.18
        elif ret7[0]<-.10 and ret1[0]>.035 and sum(x>0 for x in ret1)>=3:w[3,0]=.18
        multiplier={"risk_on":(1.,1.,.5),"risk_off":(.5,.75,1.),
                    "mixed":(.75,1.,.75)}[mode]
        for k in (1,2,3):w[k]*=multiplier[k-1]
        expected[t]=w;modes[t]=mode
    if len(expected)!=157 or set(expected)!=set(primary):
        raise ValueError("PB_ORACLE_CLOCK")
    mismatches=0;max_error=0.
    for t,expected_raw in expected.items():
        actual_raw,actual_mode=primary[t]
        error=float(np.max(np.abs(actual_raw-expected_raw)))
        max_error=max(max_error,error)
        if error>1e-10 or actual_mode!=modes[t]:mismatches+=1
    books={"PB_full":(0,1,2,3),"PB_core_only":(0,),
           "PB_minus_opportunity":(0,2,3),"PB_minus_RV":(0,1,3),
           "PB_minus_stress":(0,1,2)}
    priority={"risk_on":(1,2,3),"risk_off":(3,2,1),"mixed":(2,1,3)}
    if set(books)!=set(targets):raise ValueError("PB_ORACLE_BOOKS")
    for book,active in books.items():
        if set(targets[book])!=set(expected):raise ValueError("PB_ORACLE_BOOK_CLOCK")
        for t,raw in expected.items():
            allocated=np.zeros((4,4),float)
            if 0 in active:allocated[0]=raw[0]
            budget=min(.30,max(0.,.88-float(np.abs(allocated).sum())))
            for k in priority[modes[t]]:
                if k not in active:continue
                requested=float(np.abs(raw[k]).sum())
                if requested>0 and budget>0:
                    used=min(requested,budget)
                    allocated[k]=raw[k]*used/requested
                    budget-=used
            error=float(np.max(np.abs(allocated-targets[book][t])))
            max_error=max(max_error,error)
            if error>1e-10:mismatches+=1
    return {"decisions":157,"books":5,"signal_and_allocation_mismatches":mismatches,
            "max_weight_error":max_error,"independent_implementation":True,
            "previous_settled_funding_only":True,"future_source_accessed":False}
