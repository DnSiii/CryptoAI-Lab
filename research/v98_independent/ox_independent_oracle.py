#!/usr/bin/env python3
"""V98 OX independent signal + allocation oracle; does not import OX engine."""
import math
import numpy as np

def pearson(a,b):
    aa=a-np.mean(a);bb=b-np.mean(b)
    den=float(np.linalg.norm(aa)*np.linalg.norm(bb))
    return float(np.sum(aa*bb)/den) if den>1e-18 else 0.

def independent_decisions(d,primary,targets):
    close=np.asarray(d["c"],float)
    raw_expected={};modes={}
    for t in range(744,27048,168):
        returns336=np.log(close[t]/close[t-336])
        returns72=np.log(close[t]/close[t-72])
        log_prices=np.log(close[t-168:t+1])
        hourly=log_prices[1:]-log_prices[:-1]
        correlation_long=np.median([pearson(hourly[:,0],hourly[:,i]) for i in (1,2,3)])
        correlation_short=np.median([pearson(hourly[-72:,0],hourly[-72:,i]) for i in (1,2,3)])
        nup=int(sum(returns336>0));ndown=int(sum(returns336<0))
        mode=("coherent_up" if correlation_long>=.65 and nup>=3 else
              "coherent_down" if correlation_long>=.65 and ndown>=3 else "fractured")
        weight=np.zeros((4,4))
        if mode=="coherent_up":
            ranked=sorted((i for i in range(4) if returns336[i]>0),key=lambda i:(-returns336[i],i))
            for i,w in zip(ranked[:2],(.38,.24)):weight[0,i]=w
        elif mode=="coherent_down":
            ranked=sorted((i for i in range(4) if returns336[i]<0),key=lambda i:(returns336[i],i))
            for i,w in zip(ranked[:2],(-.32,-.20)):weight[0,i]=w
        else:
            leader=min(range(4),key=lambda i:(-returns336[i],i))
            laggard=min(range(4),key=lambda i:(returns336[i],i))
            if returns336[leader]>0 and returns72[leader]>0:weight[0,leader]=.28
            elif returns336[laggard]<0 and returns72[laggard]<0:weight[0,laggard]=-.24
        if correlation_short-correlation_long>.20:
            if sum(returns72>0)>=3 and returns72[0]>0:
                leader=min((1,2,3),key=lambda i:(-returns72[i],i))
                weight[1,leader]=.14
            elif sum(returns72<0)>=3 and returns72[0]<0:
                laggard=min((1,2,3),key=lambda i:(returns72[i],i))
                weight[1,laggard]=-.14
        xb=hourly[:,0]-np.mean(hourly[:,0])
        variance=max(float(np.sum(xb**2)),1e-15)
        residual_scores=[]
        for i in (1,2,3):
            ya=hourly[:,i]
            centered=ya-np.mean(ya)
            beta=min(2.5,max(.2,float(np.sum(centered*xb))/variance))
            errors=ya-beta*hourly[:,0]
            residual_scores.append(float(np.sum(errors[-72:])/
                                         (max(float(np.std(errors)),1e-12)*math.sqrt(72))))
        winner=min(range(3),key=lambda i:(-residual_scores[i],i))
        loser=min(range(3),key=lambda i:(residual_scores[i],i))
        if winner!=loser and residual_scores[winner]>1.5 and residual_scores[loser]<-1.5:
            weight[2,winner+1]=-.10;weight[2,loser+1]=.10
        if correlation_short<.20 and returns72[0]<-.05:weight[3,0]=-.16
        elif correlation_short>.65 and correlation_long<.35 and returns72[0]>.04:
            weight[3,0]=.16
        multipliers={"coherent_up":(1.,.75,.5),"coherent_down":(.75,1.,1.),
                     "fractured":(.75,1.,.75)}[mode]
        for slot in (1,2,3):weight[slot]*=multipliers[slot-1]
        raw_expected[t]=weight;modes[t]=mode
    if len(raw_expected)!=157 or set(primary)!=set(raw_expected):
        raise ValueError("OX_ORACLE_CLOCK")
    mismatches=0;max_error=0.
    for t in raw_expected:
        observed,mode=primary[t]
        err=float(np.max(np.abs(raw_expected[t]-observed)))
        max_error=max(max_error,err)
        if err>1e-10 or mode!=modes[t]:mismatches+=1
    books={"OX_full":(0,1,2,3),"OX_core_only":(0,),
           "OX_minus_opportunity":(0,2,3),"OX_minus_RV":(0,1,3),
           "OX_minus_stress":(0,1,2)}
    priority={"coherent_up":(1,2,3),"coherent_down":(3,2,1),"fractured":(2,3,1)}
    if set(targets)!=set(books):raise ValueError("OX_ORACLE_BOOKS")
    for book,active in books.items():
        if set(targets[book])!=set(raw_expected):raise ValueError("OX_ORACLE_BOOK_CLOCK")
        for t,raw in raw_expected.items():
            expected=np.zeros((4,4))
            expected[0]=raw[0]
            available=min(.26,max(0.,.84-float(np.sum(np.abs(expected)))))
            for slot in priority[modes[t]]:
                if slot not in active:continue
                gross=float(np.sum(np.abs(raw[slot])))
                if gross>0 and available>0:
                    taken=min(gross,available)
                    expected[slot]=raw[slot]*(taken/gross)
                    available-=taken
            err=float(np.max(np.abs(expected-targets[book][t])))
            max_error=max(max_error,err)
            if err>1e-10:mismatches+=1
    return {"decisions":157,"books":5,"signal_and_allocation_mismatches":mismatches,
            "max_weight_error":max_error,"source_future_accessed":False,
            "independent_implementation":True}
