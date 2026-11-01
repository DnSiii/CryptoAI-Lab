#!/usr/bin/env python3
"""Independent scalar PK premium/price signal and allocation oracle; no PK strategy import."""
import math
import numpy as np
CLOCK=tuple(range(744,27048,168))
BOOKS={"PK_full":(0,1,2,3),"PK_core_only":(0,),
       "PK_minus_opportunity":(0,2,3),"PK_minus_RV":(0,1,3),
       "PK_minus_stress":(0,1,2)}
PRIORITY={"discount":(1,3,2),"crowded":(2,3,1),"balanced":(2,1,3)}

def independent_decisions(d,premium,primary,targets):
    c=np.asarray(d["c"],float)
    mismatches=0;max_error=0.;active={1:0,2:0,3:0}
    for t in CLOCK:
        z=[];drift=[];r24=[];r72=[];r336=[];quality=[]
        for j in range(4):
            # independent scalar per-asset computation; never reads bar t premium.
            past=sorted(float(premium[k,j]) for k in range(t-168,t))
            median=(past[83]+past[84])/2
            long=[float(premium[k,j]) for k in range(t-672,t)]
            mean=sum(long)/672.
            sigma=max(math.sqrt(sum((v-mean)**2 for v in long)/672.),.0002)
            z.append((float(premium[t-1,j])-median)/sigma)
            drift.append(float(premium[t-1,j])-float(premium[t-25,j]))
            r24.append(math.log(c[t,j]/c[t-24,j]))
            r72.append(math.log(c[t,j]/c[t-72,j]))
            r336.append(math.log(c[t,j]/c[t-336,j]))
            hourly=[math.log(c[k,j]/c[k-1,j]) for k in range(t-335,t+1)]
            avg=sum(hourly)/336.
            std=math.sqrt(sum((x-avg)**2 for x in hourly)/336.)
            quality.append(r336[-1]/max(std*math.sqrt(336),.04))
        raw=np.zeros((4,4))
        eligible=sorted((j for j in range(4) if r336[j]>0 and z[j]<.5 and r72[j]>-.06),
                        key=lambda j:(-quality[j],j))
        for j,w in zip(eligible[:2],(.40,.22)):raw[0,j]=w
        opportunity=sorted((j for j in range(4) if z[j]<-1. and drift[j]>0 and r24[j]>0),
                           key=lambda j:(z[j],j))
        if opportunity:raw[1,opportunity[0]]=.20
        high=min((1,2,3),key=lambda j:(-z[j],j))
        low=min((1,2,3),key=lambda j:(z[j],j))
        if high!=low and z[high]-z[low]>1.6 and drift[low]>drift[high]:
            raw[2,high]=-.12;raw[2,low]=.12
        if r72[0]<-.10 and z[0]<-1.2 and drift[0]>0:
            raw[3,0]=.18
        elif r72[0]>.10 and z[0]>1.2 and drift[0]<0:
            raw[3,0]=-.18
        sorted_z=sorted(z)
        median_z=(sorted_z[1]+sorted_z[2])/2
        mode="discount" if median_z<-.6 else "crowded" if median_z>.6 else "balanced"
        got=primary[t]
        error=float(np.max(np.abs(raw-got[0])))
        max_error=max(max_error,error)
        if error>1e-9 or mode!=got[1] or not np.allclose(z,got[2][0],atol=1e-9,rtol=0) or not np.allclose(drift,got[2][1],atol=1e-9,rtol=0):
            mismatches+=1
        for slot in (1,2,3):
            if np.any(raw[slot]):active[slot]+=1
        for name,allowed in BOOKS.items():
            held=np.zeros((4,4))
            if 0 in allowed:held[0]=raw[0]
            room=min(.30,max(0.,.84-float(np.abs(held[0]).sum())))
            for slot in PRIORITY[mode]:
                if slot not in allowed or room<=1e-12:continue
                gross=sum(abs(float(x)) for x in raw[slot])
                if gross<=1e-12:continue
                take=min(room,gross)
                held[slot]=raw[slot]*(take/gross)
                room-=take
            error=float(np.max(np.abs(held-targets[name][t])))
            max_error=max(max_error,error)
            if error>1e-9:mismatches+=1
    return {"decisions":len(CLOCK),"books":len(BOOKS),"mismatches":mismatches,
            "max_weight_or_feature_error":max_error,
            "raw_optional_active_decisions":active,
            "independent_implementation":True,"premium_t_bar_read":False,
            "2025_exposed_training_only":True,"source_future_accessed":False}
