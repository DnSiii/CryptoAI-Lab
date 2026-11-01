#!/usr/bin/env python3
"""V98 PC independent decision and allocator oracle; no import of PC engine/signals."""
import math
import numpy as np

def independent_decisions(d,primary,targets):
    close=np.asarray(d["c"],float);volume=np.asarray(d["q"],float)
    expected={};modes={}
    for t in range(744,27048,168):
        ret14=[math.log(float(close[t,k])/float(close[t-336,k])) for k in range(4)]
        ret7=[math.log(float(close[t,k])/float(close[t-168,k])) for k in range(4)]
        ret1=[math.log(float(close[t,k])/float(close[t-24,k])) for k in range(4)]
        prior=[math.log(float(close[h,0])/float(close[h-1,0])) for h in range(t-335,t-167)]
        recent=[math.log(float(close[h,0])/float(close[h-1,0])) for h in range(t-167,t+1)]
        mode="expansion" if float(np.std(recent))>float(np.std(prior)) else "calm"
        w=np.zeros((4,4),float)
        if ret14[0]>0 and sum(x>0 for x in ret14)>=3:
            j=min((1,2,3),key=lambda k:(-ret14[k],k))
            w[0,0]=.42;w[0,j]=.24
        elif ret14[0]<0 and sum(x<0 for x in ret14)>=3:
            j=min((1,2,3),key=lambda k:(ret14[k],k))
            w[0,0]=-.35;w[0,j]=-.22
        else:w[0,0]=.22 if ret14[0]>0 else (-.20 if ret14[0]<0 else 0.)
        ratios={}
        for j in (1,2,3):
            recent_volume=sum(float(volume[h,j]) for h in range(t-167,t+1))
            prior_volume=sum(float(volume[h,j]) for h in range(t-335,t-167))
            ratios[j]=recent_volume/prior_volume if prior_volume>0 else 0.
        up=[j for j in (1,2,3) if ratios[j]>=1.4 and ret1[j]>0 and ret7[j]>0]
        down=[j for j in (1,2,3) if ratios[j]>=1.4 and ret1[j]<0 and ret7[j]<0]
        if up:w[1,min(up,key=lambda k:(-ratios[k],k))]=.18
        elif down:w[1,min(down,key=lambda k:(-ratios[k],k))]=-.18
        residual=[ret1[j]-ret1[0] for j in range(4)]
        low=min((1,2,3),key=lambda k:(residual[k],k))
        high=min((1,2,3),key=lambda k:(-residual[k],k))
        if low!=high and residual[high]-residual[low]>.08 and ret14[low]*ret14[high]>0:
            w[2,low]=.12;w[2,high]=-.12
        if ret1[0]<-.06 and ret7[0]<0:w[3,0]=-.20
        elif ret7[0]<-.08 and ret1[0]>.03:w[3,0]=.20
        factors={"expansion":(1.,.5,1.),"calm":(.5,1.,.5)}[mode]
        for k in (1,2,3):w[k]*=factors[k-1]
        expected[t]=w;modes[t]=mode
    if len(expected)!=157 or set(expected)!=set(primary):raise ValueError("PC_ORACLE_CLOCK")
    mismatches=0;max_error=0.
    for t in expected:
        raw,mode=primary[t]
        err=float(np.max(np.abs(expected[t]-raw)))
        max_error=max(max_error,err)
        if err>1e-10 or mode!=modes[t]:mismatches+=1
    books={"PC_full":(0,1,2,3),"PC_core_only":(0,),
           "PC_minus_opportunity":(0,2,3),"PC_minus_RV":(0,1,3),
           "PC_minus_stress":(0,1,2)}
    priority={"expansion":(1,3,2),"calm":(2,1,3)}
    if set(books)!=set(targets):raise ValueError("PC_ORACLE_BOOKS")
    for book,active in books.items():
        if set(targets[book])!=set(expected):raise ValueError("PC_ORACLE_BOOK_CLOCK")
        for t,raw in expected.items():
            allocated=np.zeros((4,4),float)
            if 0 in active:allocated[0]=raw[0]
            room=min(.30,max(0.,.84-float(np.abs(allocated).sum())))
            for k in priority[modes[t]]:
                if k not in active:continue
                requested=float(np.abs(raw[k]).sum())
                if requested>0 and room>0:
                    take=min(requested,room)
                    allocated[k]=raw[k]*take/requested
                    room-=take
            err=float(np.max(np.abs(allocated-targets[book][t])))
            max_error=max(max_error,err)
            if err>1e-10:mismatches+=1
    return {"decisions":157,"books":5,"signal_and_allocation_mismatches":mismatches,
            "max_weight_error":max_error,"independent_implementation":True,
            "future_source_accessed":False}
