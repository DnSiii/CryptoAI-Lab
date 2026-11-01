#!/usr/bin/env python3
"""Independent scalar PL funding polarity signal and allocation oracle; no PL strategy import."""
import math
import numpy as np
CLOCK=tuple(range(744,27048,168))
BOOKS={"PL_full":(0,1,2,3),"PL_core_only":(0,),
       "PL_minus_opportunity":(0,2,3),"PL_minus_RV":(0,1,3),
       "PL_minus_stress":(0,1,2)}
PRIORITY={"negative_carry":(1,2,3),"positive_carry":(3,2,1),"mixed_carry":(2,1,3)}

def independent_decisions(d,premium,primary,targets):
    c=np.asarray(d["c"],float);rate=np.asarray(d["rate"],float)
    mismatch=0;max_error=0.;active={1:0,2:0,3:0}
    for t in CLOCK:
        f=[];f3=[];r24=[];r72=[];r168=[];r336=[];quality=[]
        for j in range(4):
            f.append(sum(float(rate[k,j]) for k in range(t-168,t,8))/21.)
            f3.append(sum(float(rate[k,j]) for k in range(t-24,t,8))/3.)
            r24.append(math.log(c[t,j]/c[t-24,j]))
            r72.append(math.log(c[t,j]/c[t-72,j]))
            r168.append(math.log(c[t,j]/c[t-168,j]))
            r336.append(math.log(c[t,j]/c[t-336,j]))
            hourly=[math.log(c[k,j]/c[k-1,j]) for k in range(t-335,t+1)]
            mean=sum(hourly)/336.
            std=math.sqrt(sum((v-mean)**2 for v in hourly)/336.)
            quality.append(abs(r336[-1])/max(std*math.sqrt(336),.04))
        m=[float(premium[t-1,j]) for j in range(4)]
        raw=np.zeros((4,4))
        longs=[r336[j]>.08 and f[j]<0 and m[j]<0 and r72[j]>0 for j in range(4)]
        shorts=[r336[j]<-.08 and f[j]>0 and m[j]>0 and r72[j]<0 for j in range(4)]
        eligible=sorted((j for j in range(4) if longs[j] or shorts[j]),
                        key=lambda j:(-quality[j],j))
        for j,w in zip(eligible[:2],(.46,.28)):
            raw[0,j]=w if longs[j] else -w
        negative=sorted((j for j in range(4) if f3[j]<-.00006 and f[j]<0 and m[j]<0 and r72[j]>.025),
                        key=lambda j:(f3[j],j))
        positive=sorted((j for j in range(4) if f3[j]>.00006 and f[j]>0 and m[j]>0 and r72[j]<-.025),
                        key=lambda j:(-f3[j],j))
        if negative:raw[1,negative[0]]=.24
        elif positive:raw[1,positive[0]]=-.24
        high=min(range(4),key=lambda j:(-f[j],j))
        low=min(range(4),key=lambda j:(f[j],j))
        if high!=low and f[high]-f[low]>.00010 and abs(r168[high]-r168[low])<.10:
            raw[2,low]=.14;raw[2,high]=-.14
        if r24[0]<-.08 and f[0]>.00005 and m[0]<0:
            raw[3,0]=-.18
        elif r24[0]>.08 and f[0]<-.00005 and m[0]>0:
            raw[3,0]=.18
        sorted_f=sorted(f)
        med=(sorted_f[1]+sorted_f[2])/2
        mode="negative_carry" if med<-.00003 else "positive_carry" if med>.00003 else "mixed_carry"
        got=primary[t]
        err=float(np.max(np.abs(raw-got[0])))
        max_error=max(max_error,err)
        if err>1e-9 or mode!=got[1] or not np.allclose(f,got[2][0],atol=1e-9,rtol=0) or not np.allclose(f3,got[2][1],atol=1e-9,rtol=0):
            mismatch+=1
        for slot in (1,2,3):
            if np.any(raw[slot]):active[slot]+=1
        for name,allowed in BOOKS.items():
            held=np.zeros((4,4))
            if 0 in allowed:held[0]=raw[0]
            room=min(.32,max(0.,.84-float(np.abs(held[0]).sum())))
            for slot in PRIORITY[mode]:
                if slot not in allowed or room<=1e-12:continue
                gross=sum(abs(float(x)) for x in raw[slot])
                if gross<=1e-12:continue
                take=min(room,gross)
                held[slot]=raw[slot]*(take/gross)
                room-=take
            err=float(np.max(np.abs(held-targets[name][t])))
            max_error=max(max_error,err)
            if err>1e-9:mismatch+=1
    return {"decisions":len(CLOCK),"books":len(BOOKS),"mismatches":mismatch,
            "max_weight_or_feature_error":max_error,
            "raw_optional_active_decisions":active,"independent_implementation":True,
            "funding_event_t_read":False,"premium_t_bar_read":False,
            "2025_exposed_training_only":True,"source_future_accessed":False}
