#!/usr/bin/env python3
"""V98 PE independent scalar-loop signal and allocation oracle.
Does not import the PE engine or reuse its pressure/allocator implementation.
"""
import math
import numpy as np

def independent_decisions(d,primary,targets):
    c=np.asarray(d["c"],float);h=np.asarray(d["h"],float)
    l=np.asarray(d["l"],float);q=np.asarray(d["q"],float)
    expected={};modes={}
    def flow(j,a,b):
        numerator=0.;denominator=0.
        for i in range(a,b):
            weight=float(q[i,j])
            width=float(h[i,j]-l[i,j])
            clv=max(-1.,min(1.,(2*float(c[i,j])-float(h[i,j])-float(l[i,j]))/width)) if width>0 else 0.
            numerator+=weight*clv
            denominator+=weight
        return numerator/denominator if denominator>0 else 0.
    for t in range(744,27048,168):
        p168=[flow(j,t-167,t+1) for j in range(4)]
        p24=[flow(j,t-23,t+1) for j in range(4)]
        p72=[flow(j,t-71,t+1) for j in range(4)]
        def avg_range(a,b):
            total=0.
            for i in range(a,b):
                for j in range(4):
                    total+=(float(h[i,j])-float(l[i,j]))/float(c[i,j])
            return total/(4*(b-a))
        stressed=avg_range(t-23,t+1)>1.5*avg_range(t-167,t-23)
        mode="stress" if stressed else "normal"
        raw=np.zeros((4,4),float)
        top=sorted(range(4),key=lambda j:(-p168[j],j))
        bottom=sorted(range(4),key=lambda j:(p168[j],j))
        if p168[top[1]]>.08:
            raw[0,top[0]]=.32;raw[0,top[1]]=.20
        elif p168[bottom[1]]<-.08:
            raw[0,bottom[0]]=-.32;raw[0,bottom[1]]=-.20
        scores=[]
        for j in range(4):
            recent=sum(float(q[i,j]) for i in range(t-23,t+1))/24.
            prior=sum(float(q[i,j]) for i in range(t-167,t-23))/144.
            ratio=min(3.,max(0.,recent/prior)) if prior>0 else 0.
            scores.append((p24[j]-p168[j])*ratio)
        pick=min(range(4),key=lambda j:(-abs(scores[j]),j))
        if abs(scores[pick])>.20 and abs(math.log(float(c[t,pick])/float(c[t-24,pick])))<.06:
            raw[1,pick]=math.copysign(.16,scores[pick])
        hi=max((1,2,3),key=lambda j:(p72[j],-j))
        lo=min((1,2,3),key=lambda j:(p72[j],j))
        if hi!=lo and p72[hi]-p72[lo]>.32:
            raw[2,hi]=.12;raw[2,lo]=-.12
        pos=[j for j in range(4) if p24[j]>.12]
        neg=[j for j in range(4) if p24[j]<-.12]
        if stressed and (len(pos)>=3 or len(neg)>=3):
            direction=1. if len(pos)>=3 else -1.
            candidates=pos if direction>0 else neg
            winner=min(candidates,key=lambda j:(-abs(p24[j]),j))
            raw[3,winner]=direction*.16
        multipliers=(.5,.5,1.) if stressed else (1.,1.,.5)
        for k in (1,2,3):raw[k]*=multipliers[k-1]
        expected[t]=raw;modes[t]=mode
    if len(expected)!=157 or set(expected)!=set(primary):raise ValueError("PE_ORACLE_CLOCK")
    mismatches=0;max_error=0.
    for t,raw in expected.items():
        actual,mode=primary[t]
        err=float(np.max(np.abs(raw-actual)))
        max_error=max(max_error,err)
        if err>1e-10 or mode!=modes[t]:mismatches+=1
    books={"PE_full":(0,1,2,3),"PE_core_only":(0,),
           "PE_minus_opportunity":(0,2,3),"PE_minus_RV":(0,1,3),
           "PE_minus_stress":(0,1,2)}
    if set(books)!=set(targets):raise ValueError("PE_ORACLE_BOOKS")
    for book,active in books.items():
        if set(targets[book])!=set(expected):raise ValueError("PE_ORACLE_BOOK_CLOCK")
        for t,raw in expected.items():
            held=np.zeros((4,4),float)
            if 0 in active:held[0]=raw[0]
            remaining=min(.30,max(0.,.84-float(np.abs(held).sum())))
            priority=(3,1,2) if modes[t]=="stress" else (1,2,3)
            for k in priority:
                if k not in active:continue
                desired=float(np.abs(raw[k]).sum())
                if desired>0 and remaining>0:
                    amount=min(desired,remaining)
                    held[k]=raw[k]*amount/desired
                    remaining-=amount
            err=float(np.max(np.abs(held-targets[book][t])))
            max_error=max(max_error,err)
            if err>1e-10:mismatches+=1
    return {"decisions":157,"books":5,"signal_and_allocation_mismatches":mismatches,
            "max_weight_error":max_error,"independent_implementation":True,
            "future_source_accessed":False}
