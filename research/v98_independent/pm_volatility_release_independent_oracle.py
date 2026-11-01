#!/usr/bin/env python3
"""Independent scalar PM decision/allocator oracle. Never imports PM implementation."""
import math
import numpy as np

CLOCK=tuple(range(744,27048,168))
BOOKS={"PM_full":(0,1,2,3),"PM_core_only":(0,),
       "PM_minus_opportunity":(0,2,3),"PM_minus_RV":(0,1,3),
       "PM_minus_stress":(0,1,2)}
PRIORITY={"expansion":(1,2,3),"defense":(3,2,1),"transition":(2,1,3)}

def independent_decisions(d,premium,primary,targets):
    c=d["c"];rate=d["rate"];event=d["event"]
    mismatches=0;max_error=0.
    active={1:0,2:0,3:0}
    for t in CLOCK:
        f=[];pr=[];r24=[];r72=[];r168=[];r504=[];v72=[];v336=[];h336=[]
        for j in range(4):
            assert all(bool(event[k,j]) for k in range(t-168,t,8))
            f.append(sum(float(rate[k,j]) for k in range(t-168,t,8))/21.)
            pr.append(float(premium[t-1,j]))
            r24.append(math.log(float(c[t,j])/float(c[t-24,j])))
            r72.append(math.log(float(c[t,j])/float(c[t-72,j])))
            r168.append(math.log(float(c[t,j])/float(c[t-168,j])))
            r504.append(math.log(float(c[t,j])/float(c[t-504,j])))
            a=[math.log(float(c[k,j])/float(c[k-1,j])) for k in range(t-71,t+1)]
            b=[math.log(float(c[k,j])/float(c[k-1,j])) for k in range(t-335,t+1)]
            h336.append(b)
            ma=sum(a)/72.;mb=sum(b)/336.
            v72.append(math.sqrt(sum((v-ma)**2 for v in a)/72.))
            v336.append(math.sqrt(sum((v-mb)**2 for v in b)/336.))
        raw=np.zeros((4,4),float)
        quality=[r504[j]/max(v336[j]*math.sqrt(504),.06) for j in range(4)]
        core=sorted((j for j in range(4) if r504[j]>0 and r168[j]>0 and
                     f[j]<.00015 and pr[j]<.004),
                    key=lambda j:(-quality[j],j))
        for j,w in zip(core[:2],(.46,.24)):raw[0,j]=w
        opp=sorted((j for j in range(4) if
                    v72[j]/max(v336[j],1e-6)<.80 and
                    float(c[t,j])>max(float(c[k,j]) for k in range(t-168,t)) and
                    r24[j]>.018 and f[j]<.00018),
                   key=lambda j:(-r24[j]/max(v72[j],.0001),j))
        if opp:raw[1,opp[0]]=.20
        btc=h336[0];mean_btc=sum(btc)/336.
        btc_var=max(sum((v-mean_btc)**2 for v in btc)/336.,1e-8)
        residual=[0.]*4
        for j in (1,2,3):
            vals=h336[j];mean_x=sum(vals)/336.
            covariance=sum((vals[k]-mean_x)*(btc[k]-mean_btc) for k in range(336))/336.
            residual[j]=r168[j]-(covariance/btc_var)*r168[0]
        high=min((1,2,3),key=lambda j:(-residual[j],j))
        low=min((1,2,3),key=lambda j:(residual[j],j))
        if high!=low and residual[high]-residual[low]>.12 and f[high]-f[low]<.00010:
            raw[2,high]=.10;raw[2,low]=-.10
        if r72[0]<-.065 and sum(v>0 for v in r72)<=1 and v72[0]>1.30*v336[0]:
            raw[3,0]=-.16
        elif r72[0]>.04 and sum(v>0 for v in r24)>=3 and v72[0]>1.20*v336[0]:
            raw[3,0]=.16
        breadth=sum(v>0 for v in r168)
        mode="expansion" if breadth>=3 else "defense" if breadth<=1 else "transition"
        got=primary[t]
        error=max(float(np.max(np.abs(raw-got[0]))),
                  float(np.max(np.abs(np.array(f)-got[2][0]))),
                  float(np.max(np.abs(np.array(pr)-got[2][1]))),
                  float(np.max(np.abs(np.array(residual)-got[2][2]))))
        max_error=max(max_error,error)
        if error>1e-9 or mode!=got[1]:mismatches+=1
        for slot in (1,2,3):
            if np.any(raw[slot]):active[slot]+=1
        for name,allowed in BOOKS.items():
            held=np.zeros((4,4),float)
            if 0 in allowed:held[0]=raw[0]
            room=min(.30,max(0.,.84-float(np.abs(held[0]).sum())))
            for slot in PRIORITY[mode]:
                if slot not in allowed or room<=1e-12:continue
                gross=sum(abs(float(x)) for x in raw[slot])
                if gross<=1e-12:continue
                take=min(room,gross)
                held[slot]=raw[slot]*(take/gross)
                room-=take
            err=float(np.max(np.abs(held-targets[name][t])))
            max_error=max(max_error,err)
            if err>1e-9:mismatches+=1
    return {"decisions":len(CLOCK),"books":len(BOOKS),"mismatches":mismatches,
            "max_weight_or_feature_error":max_error,
            "raw_optional_active_decisions":active,
            "independent_scalar_implementation":True,
            "premium_t_bar_read":False,"funding_t_event_read":False,
            "2025_exposed_training_only":True,"future_accessed":False}
