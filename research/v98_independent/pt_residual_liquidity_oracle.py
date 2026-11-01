#!/usr/bin/env python3
"""Independent PT scalar residual/allocator oracle; no import of PT strategy code."""
import numpy as np

def independent_decisions(d,primary,targets):
    c=np.asarray(d["c"],float);v=np.asarray(d["q"],float)
    modes={};raws={}
    for t in range(744,27048,168):
        hourly=np.log(c[t-671:t+1]/c[t-672:t])
        means=[float(hourly[:,j].mean()) for j in range(4)]
        centered=[[float(x-means[j]) for x in hourly[:,j]] for j in range(4)]
        denom=max(sum(x*x for x in centered[0]),672e-10)
        beta=[1.]
        for j in (1,2,3):
            cov=sum(x*y for x,y in zip(centered[0],centered[j]))
            beta.append(max(0.,min(2.,cov/denom)))
        ret={}
        residual={}
        for h in (24,72,168,672):
            rr=[float(np.log(c[t,j]/c[t-h,j])) for j in range(4)]
            ret[h]=rr
            residual[h]=[rr[j]-beta[j]*rr[0] for j in range(4)]
        liquidity=[float(v[t-71:t+1,j].sum()/max(v[t-143:t-71,j].sum(),1.)) for j in range(4)]
        raw=np.zeros((4,4),float)
        if ret[672][0]>0:
            raw[0,0]=.30
            best=sorted((1,2,3),key=lambda j:(-residual[168][j],j))[0]
            if residual[168][best]>0:raw[0,best]=.26
        elif ret[672][0]<0:
            raw[0,0]=-.26
            worst=sorted((1,2,3),key=lambda j:(residual[168][j],j))[0]
            if residual[168][worst]<0:raw[0,worst]=-.24
        options=[j for j in (1,2,3) if liquidity[j]>=1.35 and abs(residual[72][j])>=.05]
        if options:
            k=sorted(options,key=lambda j:(-abs(residual[72][j])*liquidity[j],j))[0]
            raw[1,k]=.16 if residual[72][k]>0 else -.16
        high=sorted((1,2,3),key=lambda j:(-residual[168][j],j))[0]
        low=sorted((1,2,3),key=lambda j:(residual[168][j],j))[0]
        if high!=low and residual[168][high]-residual[168][low]>=.14 and residual[24][high]<residual[24][low]:
            raw[2,low]=.11;raw[2,high]=-.11
        med=float(np.median(liquidity))
        if ret[24][0]<-.06 and sum(x<0 for x in ret[24])>=3 and med>=1.15:
            raw[3,0]=-.15
        elif ret[168][0]<-.10 and ret[24][0]>.035 and med>=1.15:
            raw[3,0]=.15
        regime=("contraction" if ret[672][0]<0 else
                "expansion" if ret[672][0]>0 and med>=1. else "dispersion")
        raws[t]=raw;modes[t]=regime
    if len(modes)!=157 or set(modes)!=set(primary):
        raise ValueError("PT_ORACLE_CLOCK")
    max_err=0.;mismatches=0
    for t in modes:
        a,b=primary[t];err=float(np.max(np.abs(raws[t]-a)))
        max_err=max(max_err,err)
        if err>1e-10 or b!=modes[t]:mismatches+=1
    priority={"contraction":(3,2,1),"expansion":(1,2,3),"dispersion":(2,1,3)}
    books={"PT_full":(0,1,2,3),"PT_core_only":(0,),
           "PT_minus_opportunity":(0,2,3),"PT_minus_RV":(0,1,3),
           "PT_minus_stress":(0,1,2)}
    for name,active in books.items():
        if set(targets[name])!=set(modes):raise ValueError("PT_ORACLE_BOOK_CLOCK")
        for t in modes:
            w=np.zeros((4,4))
            if 0 in active:w[0]=raws[t][0]
            remaining=min(.28,max(0.,.84-float(np.abs(w).sum())))
            for slot in priority[modes[t]]:
                if slot not in active or remaining<=1e-12:continue
                gross=float(np.abs(raws[t][slot]).sum())
                if gross<=1e-12:continue
                take=min(gross,remaining)
                w[slot]=raws[t][slot]*take/gross
                remaining-=take
            err=float(np.max(np.abs(w-targets[name][t])))
            max_err=max(max_err,err)
            if err>1e-10:mismatches+=1
    return {"decisions":157,"books":5,"mismatches":mismatches,
            "max_weight_error":max_err,"independent_implementation":True,
            "source_future_accessed":False}
