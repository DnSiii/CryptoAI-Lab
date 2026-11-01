#!/usr/bin/env python3
"""V98 PD independent loop-based signal/allocator oracle, no PD engine import."""
import math
import numpy as np

def independent_decisions(d,primary,targets):
    c=np.asarray(d["c"],float);fund=np.asarray(d["rate"],float);events=np.asarray(d["event"],bool)
    expected={};modes={}
    for t in range(744,27048,168):
        def lr(k,n):return math.log(float(c[t,k])/float(c[t-n,k]))
        a504=[lr(j,504) for j in range(4)]
        a168=[lr(j,168) for j in range(4)]
        a72=[lr(j,72) for j in range(4)]
        a24=[lr(j,24) for j in range(4)]
        hist=[[math.log(float(c[h,j])/float(c[h-1,j])) for h in range(t-167,t+1)] for j in range(4)]
        past=[math.log(float(c[h,0])/float(c[h-1,0])) for h in range(t-335,t-167)]
        vols=[float(np.std(np.asarray(v)))*math.sqrt(24*365.25) for v in hist]
        stress=float(np.std(hist[0]))>1.25*float(np.std(past))
        mode="stress" if stress else "carry"
        w=np.zeros((4,4),float)
        scores=[(a504[j]+.5*a168[j])/max(vols[j],.25) for j in range(4)]
        if a504[0]>0:
            w[0,0]=.28
            pos=[j for j in (1,2,3) if a504[j]>0]
            if pos:w[0,min(pos,key=lambda j:(-scores[j],j))]=.20
        elif a504[0]<0:
            w[0,0]=-.28
            neg=[j for j in (1,2,3) if a504[j]<0]
            if neg:w[0,min(neg,key=lambda j:(scores[j],j))]=-.20
        means=[]
        for j in range(4):
            recent=[float(fund[h,j]) for h in range(t-168,t) if events[h,j]]
            means.append(sum(recent[-21:])/21 if len(recent)>=21 else 0.)
        pick=min(range(4),key=lambda j:(-abs(means[j]),j))
        if abs(means[pick])>=.000025:
            sign=-1. if means[pick]>0 else 1.
            if sign*a168[pick]>0:w[1,pick]=sign*.18
        x=np.asarray(hist[0],float);xm=float(x.mean())
        var=float(sum((float(v)-xm)**2 for v in x)/len(x))
        residuals=[]
        if var>1e-14:
            for j in (1,2,3):
                y=np.asarray(hist[j],float);ym=float(y.mean())
                cov=sum((float(xx)-xm)*(float(yy)-ym) for xx,yy in zip(x,y))/len(x)
                beta=max(0.,min(1.5,cov/var))
                residual=a72[j]-beta*a72[0]
                if abs(residual)>=.06:residuals.append((abs(residual),j,residual,beta))
        if residuals:
            _,j,res,beta=min(residuals,key=lambda row:(-row[0],row[1]))
            side=-1. if res>0 else 1.
            w[2,j]=side*.15
            w[2,0]=-side*.15*beta
        if a72[0]<-.07 and float(np.std(hist[0]))>float(np.std(past)):
            w[3,0]=-.18
        elif a168[0]<-.10 and a24[0]>.025 and float(np.std(hist[0]))<=float(np.std(past)):
            w[3,0]=.18
        factors=(.5,.5,1.) if stress else (1.,1.,.5)
        for j in (1,2,3):w[j]*=factors[j-1]
        expected[t]=w;modes[t]=mode
    if len(expected)!=157 or set(expected)!=set(primary):raise ValueError("PD_ORACLE_CLOCK")
    mismatches=0;max_error=0.
    for t,w in expected.items():
        actual,mode=primary[t]
        err=float(np.max(np.abs(w-actual)))
        max_error=max(max_error,err)
        if err>1e-10 or mode!=modes[t]:mismatches+=1
    books={"PD_full":(0,1,2,3),"PD_core_only":(0,),
           "PD_minus_opportunity":(0,2,3),"PD_minus_RV":(0,1,3),
           "PD_minus_stress":(0,1,2)}
    if set(books)!=set(targets):raise ValueError("PD_ORACLE_BOOKS")
    for book,active in books.items():
        if set(targets[book])!=set(expected):raise ValueError("PD_ORACLE_BOOK_CLOCK")
        for t,raw in expected.items():
            held=np.zeros((4,4),float)
            if 0 in active:held[0]=raw[0]
            remaining=min(.36,max(0.,.84-float(np.abs(held).sum())))
            priority=(3,1,2) if modes[t]=="stress" else (1,2,3)
            for k in priority:
                if k not in active:continue
                desired=float(np.abs(raw[k]).sum())
                if desired>0 and remaining>0:
                    allocated=min(desired,remaining)
                    held[k]=raw[k]*allocated/desired
                    remaining-=allocated
            err=float(np.max(np.abs(held-targets[book][t])))
            max_error=max(max_error,err)
            if err>1e-10:mismatches+=1
    return {"decisions":157,"books":5,"signal_and_allocation_mismatches":mismatches,
            "max_weight_error":max_error,"independent_implementation":True,
            "future_source_accessed":False}
