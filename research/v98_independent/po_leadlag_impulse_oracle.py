#!/usr/bin/env python3
"""Independent PO lagged cross-asset decision/allocator oracle. No PO primary imports."""
import math
import numpy as np

CLOCK=tuple(range(744,27048,168))
BOOKS={"PO_full":(0,1,2,3),"PO_core_only":(0,),
       "PO_minus_opportunity":(0,2,3),"PO_minus_RV":(0,1,3),
       "PO_minus_stress":(0,1,2)}
PRIORITY={"impulse":(3,1,2),"diffusion":(1,2,3),"quiet":(2,1,3)}

def independent_decisions(d,primary,books):
    prices=np.asarray(d["c"],float)
    log=np.log(prices)
    independent={}
    for t in CLOCK:
        delta24=np.log(prices[t]/prices[t-24])
        delta168=np.log(prices[t]/prices[t-168])
        delta336=np.log(prices[t]/prices[t-336])
        r=np.log(prices[t-167:t+1]/prices[t-168:t])
        vol=np.maximum(np.sqrt(np.mean((r-r.mean(axis=0))**2,axis=0))*math.sqrt(168),.04)
        lagged_btc=np.diff(log[t-337:t+1,0])[:-1]
        btc_mean=float(lagged_btc.mean())
        btc_var=float(np.mean((lagged_btc-btc_mean)**2))
        correlations=np.zeros(4)
        residuals=np.zeros(4)
        for j in (1,2,3):
            next_alt=np.diff(log[t-337:t+1,j])[1:]
            am=float(next_alt.mean())
            av=float(np.mean((next_alt-am)**2))
            covariance=float(np.mean((lagged_btc-btc_mean)*(next_alt-am)))
            correlations[j]=covariance/(math.sqrt(max(btc_var,1e-16))*math.sqrt(max(av,1e-16)))
            beta=max(0.,min(2.,covariance/max(btc_var,1e-16)))
            residuals[j]=beta*delta24[0]-delta24[j]
        raw=np.zeros((4,4),float)
        if np.median(delta168)>=0:
            candidates=[j for j in range(4) if delta336[j]>0]
            candidates.sort(key=lambda j:(-delta336[j]/vol[j],j))
            for j,w in zip(candidates[:2],(.34,.18)):raw[0,j]=w
        else:
            candidates=[j for j in range(4) if delta336[j]<0]
            candidates.sort(key=lambda j:(delta336[j]/vol[j],j))
            for j,w in zip(candidates[:2],(-.30,-.16)):raw[0,j]=w
        connected=[j for j in (1,2,3) if correlations[j]>=.10]
        choices=[j for j in connected if abs(residuals[j])>=.025 and residuals[j]*delta24[0]>0]
        winner=None
        if choices:
            winner=sorted(choices,key=lambda j:(-abs(residuals[j]),j))[0]
            raw[1,winner]=.18 if residuals[winner]>0 else -.18
        if len(connected)>=2:
            hi=sorted(connected,key=lambda j:(-residuals[j],j))[0]
            lo=sorted(connected,key=lambda j:(residuals[j],j))[0]
            if hi!=lo and residuals[hi]-residuals[lo]>=.05 and residuals[lo]<0<residuals[hi]:
                raw[2,lo]=.11
                raw[2,hi]=-.11
        intensity=abs(float(delta24[0]))/max(float(vol[0])/math.sqrt(7),.02)
        if intensity>=1.75 and len(connected)>=2:
            lagger=sorted(connected,key=lambda j:(-abs(residuals[j]),j))[0]
            if lagger==winner:
                if delta24[0]!=0:raw[3,0]=-.12 if delta24[0]>0 else .12
            elif residuals[lagger]!=0:
                raw[3,lagger]=.15 if residuals[lagger]>0 else -.15
        regime="impulse" if intensity>=1.75 else "diffusion" if len(connected)>=2 else "quiet"
        independent[t]=(raw,regime)
    if set(independent)!=set(primary):raise ValueError("PO_ORACLE_CLOCK")
    mismatch=0;maximum=0.
    for t in CLOCK:
        expected,regime=independent[t]
        got,mode=primary[t]
        error=float(np.max(np.abs(expected-got)))
        maximum=max(maximum,error)
        if error>1e-10 or mode!=regime:mismatch+=1
    for name,active in BOOKS.items():
        if set(books[name])!=set(CLOCK):raise ValueError("PO_ORACLE_BOOK_CLOCK")
        for t in CLOCK:
            raw,mode=independent[t]
            weights=np.zeros((4,4),float)
            if 0 in active:weights[0]=raw[0]
            available=min(.32,max(0.,.84-float(np.abs(weights).sum())))
            for slot in PRIORITY[mode]:
                if slot not in active or available<=1e-12:continue
                gross=float(np.abs(raw[slot]).sum())
                if gross>1e-12:
                    used=min(gross,available)
                    weights[slot]=raw[slot]*used/gross
                    available-=used
            error=float(np.max(np.abs(weights-books[name][t])))
            maximum=max(maximum,error)
            if error>1e-10:mismatch+=1
    return {"decisions":157,"books":5,"mismatches":mismatch,
            "max_weight_error":maximum,"independent_implementation":True,
            "future_2026_accessed":False}
