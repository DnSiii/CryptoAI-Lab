#!/usr/bin/env python3
"""V98 OW independent weekly signal/allocator oracle. No OW strategy imports.
Independently rebuilds the 157 decisions and five books from pinned input only.
"""
import math
import numpy as np

def independent_decisions(d,primary,targets):
    close=np.asarray(d["c"],float)
    modes={};raws={}
    for t in range(744,27048,168):
        returns={k:np.log(close[t]/close[t-k]) for k in (12,24,72,168,504)}
        r12,r24,r72,r168,r504=(returns[k] for k in (12,24,72,168,504))
        hr=np.log(close[t-503:t+1]/close[t-504:t])
        path=np.abs(hr).sum(axis=0)
        efficiency=np.abs(r504)/np.maximum(path,1e-12)
        pos=sum(v>0 for v in r504);neg=sum(v<0 for v in r504)
        mode="positive" if pos>=3 else "negative" if neg>=3 else "mixed"
        w=np.zeros((4,4),dtype=float)
        if mode=="positive":
            ranks=sorted([i for i in range(4) if r504[i]>0 and r168[i]>0],
                         key=lambda i:(-efficiency[i],i))
            for i,value in zip(ranks[:2],(.42,.22)):w[0,i]=value
        elif mode=="negative":
            ranks=sorted([i for i in range(4) if r504[i]<0 and r168[i]<0],
                         key=lambda i:(-efficiency[i],i))
            for i,value in zip(ranks[:2],(-.38,-.20)):w[0,i]=value
        else:
            if r504[0]>0 and r168[0]>0:w[0,0]=.28
            elif r504[0]<0 and r168[0]<0:w[0,0]=-.28
        rebound=[i for i in range(4) if r24[i]<-.065 and r12[i]>.022]
        exhausted=[i for i in range(4) if r24[i]>.065 and r12[i]<-.022]
        if rebound:w[1,min(rebound,key=lambda i:(-r12[i],i))]=.16
        elif exhausted:w[1,min(exhausted,key=lambda i:(r12[i],i))]=-.16
        market=hr[:,0]
        market_mean=float(np.mean(market))
        market_center=market-market_mean
        denom=max(float(np.sum(market_center**2)),1e-15)
        adjusted=[]
        for i in (1,2,3):
            centered=hr[:,i]-np.mean(hr[:,i])
            b=min(2.5,max(.2,float(np.sum(centered*market_center))/denom))
            adjusted.append(float(r168[i]-b*r168[0]))
        high=min(range(3),key=lambda i:(-adjusted[i],i))
        low=min(range(3),key=lambda i:(adjusted[i],i))
        if adjusted[high]-adjusted[low]>.10:
            w[2,high+1]=.11;w[2,low+1]=-.11
        if sum(r72<-.09)>=3 and sum(r24<-.035)>=3:w[3,0]=-.16
        elif sum(r72<-.09)>=3 and sum(r24>.020)>=3:w[3,0]=.16
        factor={"positive":(1.,.75,.5),"negative":(.5,1.,1.),
                "mixed":(.75,1.,.75)}[mode]
        for i in (1,2,3):w[i]*=factor[i-1]
        modes[t]=mode;raws[t]=w
    if len(modes)!=157 or set(modes)!=set(primary):
        raise ValueError("OW_ORACLE_CLOCK")
    mismatch=0;maxerr=0.
    for t in modes:
        p,m=primary[t]
        e=float(np.max(np.abs(p-raws[t])))
        maxerr=max(maxerr,e)
        if e>1e-10 or m!=modes[t]:mismatch+=1
    active={"OW_full":(0,1,2,3),"OW_core_only":(0,),
            "OW_minus_opportunity":(0,2,3),"OW_minus_RV":(0,1,3),
            "OW_minus_stress":(0,1,2)}
    priorities={"positive":(1,2,3),"negative":(3,2,1),"mixed":(2,1,3)}
    if set(targets)!=set(active):raise ValueError("OW_ORACLE_BOOKS")
    for name,slots in active.items():
        if set(targets[name])!=set(modes):raise ValueError("OW_ORACLE_BOOK_CLOCK")
        for t in modes:
            raw=raws[t];book=np.zeros((4,4))
            book[0]=raw[0]
            capacity=min(.26,max(0.,.84-float(np.abs(book).sum())))
            for i in priorities[modes[t]]:
                if i not in slots:continue
                wanted=float(np.abs(raw[i]).sum())
                if wanted>0 and capacity>0:
                    granted=min(wanted,capacity)
                    book[i]=raw[i]*(granted/wanted)
                    capacity-=granted
            e=float(np.max(np.abs(book-targets[name][t])))
            maxerr=max(maxerr,e)
            if e>1e-10:mismatch+=1
    return {"decisions":157,"books":5,"signal_and_allocation_mismatches":mismatch,
            "max_weight_error":maxerr,"source_future_accessed":False,
            "independent_implementation":True}
