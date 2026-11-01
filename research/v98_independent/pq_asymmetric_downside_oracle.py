#!/usr/bin/env python3
"""Independent scalar PQ signal/allocator oracle; does not import PQ primary engine."""
import math
import numpy as np

CLOCK=tuple(range(744,27048,168))
BOOKS={"PQ_full":(0,1,2,3),"PQ_core_only":(0,),
       "PQ_minus_opportunity":(0,2,3),"PQ_minus_RV":(0,1,3),
       "PQ_minus_stress":(0,1,2)}
PRIORITY={"panic":(3,2,1),"expansion":(1,2,3),"normal":(2,1,3)}

def independent_decisions(d,primary,books):
    c=np.asarray(d["c"],float);q=np.asarray(d["q"],float)
    mismatches=0;max_error=0.;activations={1:0,2:0,3:0}
    for t in CLOCK:
        r24=[];r72=[];r168=[];r504=[];asym=[];vol=[];expansion=[]
        for j in range(4):
            changes=[math.log(c[k,j]/c[k-1,j]) for k in range(t-503,t+1)]
            downside=math.sqrt(sum(min(x,0.)**2 for x in changes)/504.)
            upside=math.sqrt(sum(max(x,0.)**2 for x in changes)/504.)
            asym.append((downside+.0001)/(upside+.0001))
            mu=sum(changes)/504.
            variance=sum((x-mu)**2 for x in changes)/504.
            vol.append(max(math.sqrt(variance*504.),.04))
            r24.append(math.log(c[t,j]/c[t-24,j]))
            r72.append(math.log(c[t,j]/c[t-72,j]))
            r168.append(math.log(c[t,j]/c[t-168,j]))
            r504.append(math.log(c[t,j]/c[t-504,j]))
            recent=sum(float(q[k,j]) for k in range(t-71,t+1))
            earlier=sum(float(q[k,j]) for k in range(t-143,t-71))
            expansion.append(min(4.,recent/max(earlier,1.)))
        raw=np.zeros((4,4),float)
        if float(np.median(r168))>=0:
            eligible=[j for j in range(4) if r504[j]>0 and asym[j]<1.25]
            eligible.sort(key=lambda j:(-r504[j]/vol[j],j))
            for j,w in zip(eligible[:2],(.42,.24)):raw[0,j]=w
        else:
            eligible=[j for j in range(4) if r504[j]<0 and asym[j]>1.15]
            eligible.sort(key=lambda j:(r504[j]/vol[j],j))
            for j,w in zip(eligible[:2],(-.38,-.22)):raw[0,j]=w
        long=[j for j in range(4) if r72[j]>.06 and expansion[j]>1.5 and asym[j]<.95]
        short=[j for j in range(4) if r72[j]<-.08 and expansion[j]>1.5 and asym[j]>1.30]
        long.sort(key=lambda j:(-expansion[j],j))
        short.sort(key=lambda j:(-expansion[j],j))
        if long:raw[1,long[0]]=.18
        elif short:raw[1,short[0]]=-.16
        hi=sorted((1,2,3),key=lambda j:(-asym[j],j))[0]
        lo=sorted((1,2,3),key=lambda j:(asym[j],j))[0]
        if hi!=lo and asym[hi]-asym[lo]>.40 and abs(r168[hi]-r168[lo])<.10:
            raw[2,hi]=-.12;raw[2,lo]=.12
        if r72[0]<-.12 and np.median(asym)>1.25:
            recover=[j for j in range(4) if r24[j]>0 and expansion[j]>1.2]
            recover.sort(key=lambda j:(-r24[j],j))
            if recover:raw[3,recover[0]]=.16
            elif r24[0]<-.05:raw[3,0]=-.16
        mode="panic" if np.median(asym)>1.35 else "expansion" if np.median(expansion)>1.20 else "normal"
        expected,primary_mode=primary[t]
        error=float(np.max(np.abs(expected-raw)))
        max_error=max(max_error,error)
        if error>1e-10 or mode!=primary_mode:mismatches+=1
        for slot in (1,2,3):
            if np.any(raw[slot]):activations[slot]+=1
        for name,active in BOOKS.items():
            weights=np.zeros((4,4),float)
            if 0 in active:weights[0]=raw[0]
            remaining=min(.24,max(0.,.82-float(np.abs(weights).sum())))
            for slot in PRIORITY[mode]:
                if slot not in active or remaining<=1e-12:continue
                gross=sum(abs(float(x)) for x in raw[slot])
                if gross>1e-12:
                    take=min(remaining,gross)
                    weights[slot]=raw[slot]*(take/gross)
                    remaining-=take
            error=float(np.max(np.abs(weights-books[name][t])))
            max_error=max(max_error,error)
            if error>1e-10:mismatches+=1
    return {"decisions":157,"books":5,"mismatches":mismatches,
            "max_weight_error":max_error,"raw_optional_activations":activations,
            "independent_implementation":True,"future_2026_accessed":False}
