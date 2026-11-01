#!/usr/bin/env python3
"""Independent scalar PJ signal and allocation oracle; never imports PJ strategy."""
import math
import numpy as np
CLOCK=tuple(range(744,27048,168))
BOOKS={"PJ_full":(0,1,2,3),"PJ_core_only":(0,),
       "PJ_minus_opportunity":(0,2,3),"PJ_minus_RV":(0,1,3),
       "PJ_minus_stress":(0,1,2)}
PRIORITY={"breakout":(1,2,3),"shock":(3,2,1),"range":(2,1,3)}

def independent_decisions(d,primary,targets):
    c=np.asarray(d["c"],float);h=np.asarray(d["h"],float)
    l=np.asarray(d["l"],float);q=np.asarray(d["q"],float)
    mismatch=0;max_error=0.;active={1:0,2:0,3:0}
    for t in CLOCK:
        ret=lambda j,k:math.log(c[t,j]/c[t-k,j])
        r24=np.array([ret(j,24) for j in range(4)])
        r72=np.array([ret(j,72) for j in range(4)])
        r168=np.array([ret(j,168) for j in range(4)])
        r336=np.array([ret(j,336) for j in range(4)])
        v24=[sum(float(q[k,j]) for k in range(t-23,t+1)) for j in range(4)]
        prev=[sum(float(q[k,j]) for k in range(t-167,t-23))/6. for j in range(4)]
        ups=[];downs=[]
        for j in range(4):
            ups.append(c[t,j]>max(h[k,j] for k in range(t-168,t)) and r336[j]>0 and prev[j]>0 and v24[j]>1.15*prev[j])
            downs.append(c[t,j]<min(l[k,j] for k in range(t-168,t)) and r336[j]<0 and prev[j]>0 and v24[j]>1.15*prev[j])
        hourly=np.array([[math.log(c[k,j]/c[k-1,j]) for j in range(4)] for k in range(t-335,t+1)])
        quality=np.abs(r336)/np.maximum(np.std(hourly,axis=0)*math.sqrt(336),.04)
        raw=np.zeros((4,4))
        ranks=sorted((j for j in range(4) if ups[j] or downs[j]),key=lambda j:(-quality[j],j))
        for j,w in zip(ranks[:2],(.42,.24)):
            raw[0,j]=w if ups[j] else -w
        if prev[0]>0 and v24[0]>1.4*prev[0]:
            if r24[0]>.045:
                js=[j for j in (1,2,3) if r72[j]>0 and r24[j]>0]
                if js:raw[1,sorted(js,key=lambda j:(-r24[j],j))[0]]=.22
            elif r24[0]<-.045:
                js=[j for j in (1,2,3) if r72[j]<0 and r24[j]<0]
                if js:raw[1,sorted(js,key=lambda j:(r24[j],j))[0]]=-.22
        var=float(np.var(hourly[:,0]))
        betas=[]
        for j in range(4):
            cov=float(np.mean((hourly[:,j]-np.mean(hourly[:,j]))*(hourly[:,0]-np.mean(hourly[:,0]))))
            betas.append(min(2.,max(0.,cov/max(var,1e-8))))
        residual=r168-np.asarray(betas)*r168[0]
        high=sorted((1,2,3),key=lambda j:(-residual[j],j))[0]
        low=sorted((1,2,3),key=lambda j:(residual[j],j))[0]
        if high!=low and residual[high]-residual[low]>.12 and residual[high]>.04 and residual[low]<-.04 and r24[high]>r24[low]:
            raw[2,high]=.13;raw[2,low]=-.13
        if prev[0]>0 and v24[0]>1.3*prev[0]:
            if r72[0]<-.09 and c[t,0]<min(l[k,0] for k in range(t-336,t)):
                raw[3,0]=-.20
            elif r336[0]<-.18 and r24[0]>.065:
                raw[3,0]=.20
        mode="breakout" if len(ranks)>=2 else "shock" if r72[0]<-.09 else "range"
        got=primary[t]
        error=float(np.max(np.abs(raw-got[0])))
        max_error=max(max_error,error)
        if error>1e-10 or mode!=got[1] or any(not np.allclose(x,y,rtol=0,atol=1e-10) for x,y in zip((np.asarray(ups),np.asarray(downs),residual),got[2])):
            mismatch+=1
        for slot in (1,2,3):
            if np.any(raw[slot]):active[slot]+=1
        history=np.array([[math.log(c[k,j]/c[k-1,j]) for j in range(4)] for k in range(t-167,t+1)])
        for name,allowed in BOOKS.items():
            held=np.zeros((4,4))
            if 0 in allowed:held[0]=raw[0]
            room=min(.30,max(0.,.84-float(np.abs(held[0]).sum())))
            for slot in PRIORITY[mode]:
                if slot not in allowed or room<=1e-12:continue
                gross=float(np.abs(raw[slot]).sum())
                if gross<=1e-12:continue
                a=history@raw[slot];b=history@held.sum(axis=0)
                if np.std(a)>1e-12 and np.std(b)>1e-12:
                    aa=a-a.mean();bb=b-b.mean()
                    corr=float(np.dot(aa,bb)/math.sqrt(np.dot(aa,aa)*np.dot(bb,bb)))
                else:corr=0.
                take=min(room,gross*(.5 if corr>.45 else 1.))
                held[slot]=raw[slot]*(take/gross)
                room-=take
            error=float(np.max(np.abs(held-targets[name][t])))
            max_error=max(max_error,error)
            if error>1e-10:mismatch+=1
    return {"decisions":len(CLOCK),"books":len(BOOKS),"mismatches":mismatch,
            "max_weight_or_feature_error":max_error,
            "raw_optional_active_decisions":active,
            "independent_implementation":True,"2025_exposed_training_only":True,
            "source_future_accessed":False}
