#!/usr/bin/env python3
"""Independent PU decision/portfolio oracle. Never imports PU primary strategy or allocator."""
import math,itertools
import numpy as np

BOOKS={"PU_full":(0,1,2,3),"PU_core_only":(0,),
       "PU_minus_opportunity":(0,2,3),"PU_minus_RV":(0,1,3),
       "PU_minus_stress":(0,1,2)}
PRIORITY={"up":(1,2,3),"down":(3,2,1),"mixed":(2,1,3)}

def independent_decisions(d,primary,targets):
    prices=np.asarray(d["c"],float);volumes=np.asarray(d["q"],float);funding=np.asarray(d["rate"],float)
    previous={name:np.zeros(4,float) for name in BOOKS}
    mismatches=0;max_error=0.;activated=[0,0,0]
    for t in range(744,27048,168):
        hourly=np.log(prices[t-335:t+1]/prices[t-336:t])
        weights=[2**(-(335-i)/168.) for i in range(336)]
        scale=sum(weights);weights=[x/scale for x in weights]
        expected=np.array([sum(float(hourly[k,j])*weights[k] for k in range(336)) for j in range(4)])
        residual=hourly-expected
        empirical=np.zeros((4,4))
        for i in range(4):
            for j in range(4):
                empirical[i,j]=sum(weights[k]*float(residual[k,i])*float(residual[k,j]) for k in range(336))
        covariance=.5*empirical+.5*np.diag(np.diag(empirical))
        fr=np.array([sum(float(funding[t-160+8*k,j]) for k in range(21))/168. for j in range(4)])
        e=expected-fr
        r24=np.log(prices[t]/prices[t-24]);r72=np.log(prices[t]/prices[t-72])
        r168=np.log(prices[t]/prices[t-168]);r336=np.log(prices[t]/prices[t-336])
        prior168=np.log(prices[t-168]/prices[t-336])
        accel=r168-prior168
        liquidity=np.array([sum(float(x) for x in volumes[t-71:t+1,j])/
                            max(sum(float(x) for x in volumes[t-143:t-71,j]),1.) for j in range(4)])
        raw=np.zeros((4,4))
        score=np.array([168*(abs(e[j])-.5*covariance[j,j]) for j in range(4)])
        eligible=sorted((j for j in range(4) if score[j]>.015 and abs(r336[j])>=.04 and e[j]*r336[j]>0),
                        key=lambda j:(-score[j],j))
        for j,w in zip(eligible[:2],(.42,.20)):raw[0,j]=w if e[j]>0 else -w
        options=sorted((j for j in range(4) if abs(accel[j])>=.12 and liquidity[j]>=1.20 and accel[j]*e[j]>0),
                       key=lambda j:(-abs(accel[j]),j))
        if options:raw[1,options[0]]=.16 if accel[options[0]]>0 else -.16
        hi=sorted(range(4),key=lambda j:(-fr[j],j))[0]
        lo=sorted(range(4),key=lambda j:(fr[j],j))[0]
        if hi!=lo and 8*(fr[hi]-fr[lo])>=.0015:raw[2,lo]=.10;raw[2,hi]=-.10
        if sum(r72<=-.10)>=3 and r24[0]<=-.04:raw[3,0]=-.14
        elif sum(r72<=-.08)>=3 and r24[0]>=.04:raw[3,0]=.14
        breadth=sum(r336>0)
        mode="up" if breadth>=3 else "down" if breadth<=1 else "mixed"
        p,m,mu,cov,f=primary[t]
        err=max(float(np.max(np.abs(raw-p))),float(np.max(np.abs(expected-mu))),
                float(np.max(np.abs(covariance-cov))),float(np.max(np.abs(fr-f))))
        max_error=max(max_error,err)
        if err>1e-10 or m!=mode:mismatches+=1
        for j in (1,2,3):
            if np.any(raw[j]):activated[j-1]+=1
        for name,active in BOOKS.items():
            candidates=[]
            for bits in itertools.product((0,1),repeat=3):
                alloc=np.zeros((4,4))
                if 0 in active:alloc[0]=raw[0]
                remaining=min(.28,max(0.,.84-sum(abs(float(x)) for x in alloc.flat)))
                for slot in PRIORITY[mode]:
                    if slot not in active or bits[slot-1]==0 or remaining<=1e-12:continue
                    gross=sum(abs(float(x)) for x in raw[slot])
                    if gross>1e-12:
                        taken=min(gross,remaining)
                        alloc[slot]=raw[slot]*(taken/gross)
                        remaining-=taken
                net=alloc.sum(axis=0)
                turnover=sum(abs(float(x)) for x in net-previous[name])
                gross=sum(abs(float(x)) for x in alloc.flat)
                utility=168*(float(np.dot(net,expected-fr))-.5*float(net@covariance@net))-.0006*turnover
                candidates.append((utility,turnover,gross,bits,alloc,net))
            baseline=next(z for z in candidates if z[3]==(0,0,0))
            selected=min(candidates,key=lambda z:(-round(z[0],12),z[1],z[2],z[3]))
            if selected[0]<=baseline[0]+1e-12:selected=baseline
            target=targets[name][t]
            err=float(np.max(np.abs(target-selected[4])))
            max_error=max(max_error,err)
            if err>1e-10:mismatches+=1
            previous[name]=selected[5]
    return {"decisions":157,"books":5,"mismatches":mismatches,
            "max_weight_error":max_error,"raw_optional_activations":activated,
            "independent_implementation":True,"source_future_accessed":False}
