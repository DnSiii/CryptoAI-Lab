#!/usr/bin/env python3
"""V98 OY independent signal + allocation oracle; does not import OY engine."""
import math
import numpy as np

def independent_decisions(d,primary,targets):
    prices=np.asarray(d["c"],float)
    volumes=np.asarray(d["q"],float)
    raw_expected={};modes={}
    for t in range(744,27048,168):
        lookback336=np.log(prices[t]/prices[t-336])
        lookback72=np.log(prices[t]/prices[t-72])
        lookback24=np.log(prices[t]/prices[t-24])
        pressure_long=[];pressure_short=[];ratio=[]
        for k in range(4):
            sign_volume_long=0.;sum_volume_long=0.
            for h in range(t-335,t+1):
                signed=math.log(prices[h,k]/prices[h-1,k])
                sign_volume_long+=np.sign(signed)*volumes[h,k]
                sum_volume_long+=volumes[h,k]
            pressure_long.append(sign_volume_long/max(sum_volume_long,1e-12))
            sign_volume_short=0.;sum_volume_short=0.
            for h in range(t-71,t+1):
                signed=math.log(prices[h,k]/prices[h-1,k])
                sign_volume_short+=np.sign(signed)*volumes[h,k]
                sum_volume_short+=volumes[h,k]
            pressure_short.append(sign_volume_short/max(sum_volume_short,1e-12))
            recent=float(sum(volumes[t-23:t+1,k]))/24.
            baseline=float(sum(volumes[t-191:t-23,k]))/168.
            ratio.append(recent/max(baseline,1e-12))
        plus=sum(pressure_long[k]>0 and lookback336[k]>0 for k in range(4))
        minus=sum(pressure_long[k]<0 and lookback336[k]<0 for k in range(4))
        mode="accumulation" if plus>=3 else ("distribution" if minus>=3 else "mixed")
        weights=np.zeros((4,4))
        scores=[pressure_long[k]*abs(lookback336[k]) for k in range(4)]
        if mode=="accumulation":
            ranked=sorted((k for k in range(4) if pressure_long[k]>0 and lookback336[k]>0),key=lambda k:(-scores[k],k))
            for k,w in zip(ranked[:2],(.42,.24)):weights[0,k]=w
        elif mode=="distribution":
            ranked=sorted((k for k in range(4) if pressure_long[k]<0 and lookback336[k]<0),key=lambda k:(scores[k],k))
            for k,w in zip(ranked[:2],(-.34,-.20)):weights[0,k]=w
        else:
            ups=[k for k in range(4) if pressure_long[k]>.10 and lookback336[k]>0 and lookback72[k]>0]
            downs=[k for k in range(4) if pressure_long[k]<-.10 and lookback336[k]<0 and lookback72[k]<0]
            if ups:weights[0,min(ups,key=lambda k:(-scores[k],k))]=.30
            elif downs:weights[0,min(downs,key=lambda k:(scores[k],k))]=-.24
        breakout_up=[k for k in range(4) if ratio[k]>1.4 and lookback24[k]>.035 and lookback72[k]>0 and pressure_long[k]>0]
        breakout_down=[k for k in range(4) if ratio[k]>1.4 and lookback24[k]<-.035 and lookback72[k]<0 and pressure_long[k]<0]
        if breakout_up:weights[1,min(breakout_up,key=lambda k:(-lookback24[k],k))]=.18
        elif breakout_down:weights[1,min(breakout_down,key=lambda k:(lookback24[k],k))]=-.18
        residual={k:lookback72[k]-lookback72[0] for k in (1,2,3)}
        positive=[k for k in (1,2,3) if residual[k]>.07 and pressure_short[k]>0]
        negative=[k for k in (1,2,3) if residual[k]<-.07 and pressure_short[k]<0]
        if positive and negative:
            weights[2,min(positive,key=lambda k:(-residual[k],k))]=.12
            weights[2,min(negative,key=lambda k:(residual[k],k))]=-.12
        if sum(lookback72<-.08)>=3 and sum(x>1.25 for x in ratio)>=3 and sum(lookback24>0)>=3:
            weights[3,min(range(4),key=lambda k:(-lookback24[k],k))]=.16
        elif sum(lookback24<-.06)>=3 and lookback72[0]<-.07 and ratio[0]>1.25:
            weights[3,0]=-.16
        factors={"accumulation":(1.,.75,.5),"distribution":(.75,1.,1.),
                 "mixed":(.75,1.,.75)}[mode]
        for slot in (1,2,3):weights[slot]*=factors[slot-1]
        raw_expected[t]=weights;modes[t]=mode
    if len(raw_expected)!=157 or set(primary)!=set(raw_expected):
        raise ValueError("OY_ORACLE_CLOCK")
    mismatches=0;max_error=0.
    for t in raw_expected:
        observed,mode=primary[t]
        err=float(np.max(np.abs(raw_expected[t]-observed)))
        max_error=max(max_error,err)
        if err>1e-10 or mode!=modes[t]:mismatches+=1
    books={"OY_full":(0,1,2,3),"OY_core_only":(0,),
           "OY_minus_opportunity":(0,2,3),"OY_minus_RV":(0,1,3),
           "OY_minus_stress":(0,1,2)}
    priority={"accumulation":(1,2,3),"distribution":(3,1,2),"mixed":(2,3,1)}
    if set(targets)!=set(books):raise ValueError("OY_ORACLE_BOOKS")
    for book,active in books.items():
        if set(targets[book])!=set(raw_expected):raise ValueError("OY_ORACLE_BOOK_CLOCK")
        for t,raw in raw_expected.items():
            expected=np.zeros((4,4))
            expected[0]=raw[0]
            available=min(.30,max(0.,.90-float(np.sum(np.abs(expected)))))
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
