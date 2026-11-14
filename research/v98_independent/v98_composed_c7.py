"""V98 C7 preregistered volatility-contraction breakout composed sleeves. Training only."""
import math
from .phase243_native_funding_cashflow import ASSETS

LONG=2160
MID=720
SHORT=168
STEP=24

def p_median_confirm(prices,i):
    # 30-day median close; t-1 historical information only.
    closes=sorted(prices[i-MID+1:i+1])
    return prices[i]>(closes[MID//2-1]+closes[MID//2])/2

def composed_c7_sleeves():
    last={a:(0.,0.,0.,0.) for a in ASSETS}
    pending_stress=False
    def compute(history):
        nonlocal last,pending_stress
        if set(history)!=set(ASSETS):
            raise ValueError("C7_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS):
            raise ValueError("C7_MISALIGNED")
        i=n-1
        if i<LONG or i%STEP:
            return last
        metrics={}
        for a in ASSETS:
            p=history[a][i-LONG:i+1]
            if len(p)!=LONG+1 or any(not math.isfinite(float(v)) or v<=0 for v in p):
                raise ValueError("C7_INVALID_CLOSE")
            r90=math.log(p[-1]/p[0])
            r30=math.log(p[-1]/p[-MID-1])
            r7=math.log(p[-1]/p[-SHORT-1])
            returns=[math.log(p[k]/p[k-1]) for k in range(len(p)-MID,len(p))]
            def sd(v):
                mean=sum(v)/len(v)
                return math.sqrt(sum((x-mean)**2 for x in v)/(len(v)-1))
            vol30=sd(returns)
            vol7=sd(returns[-SHORT:])
            vol24=sd(returns[-24:])
            breakout=p[-1]>max(p[-25:-1])
            metrics[a]=(r90,r30,r7,vol30,vol7,vol24,breakout)
        core=[a for a in ASSETS if metrics[a][0]>0 and metrics[a][1]>0
              and metrics[a][1]>metrics[a][3]*math.sqrt(MID)]
        seven_positive=sum(metrics[a][2]>0 for a in ASSETS)
        opportunity=[]
        if seven_positive>=3:
            opportunity=sorted((a for a in ASSETS if metrics[a][2]>0),
                               key=lambda a:(-metrics[a][2],a))[:1]
        ranked=sorted(metrics[a][1] for a in ASSETS)
        median=(ranked[1]+ranked[2])/2
        positive30=sum(metrics[a][1]>0 for a in ASSETS)
        rv=[a for a in ASSETS if positive30>=2 and metrics[a][1]>max(0.,median)]
        stress=sum(metrics[a][1]<0 for a in ASSETS)>=3
        if stress:
            pending_stress=True
        recovery=[]
        if pending_stress and not stress and seven_positive>=3:
            eligible=[a for a in ASSETS if metrics[a][1]>0 and metrics[a][2]>0
                      and p_median_confirm(history[a],i)]
            recovery=sorted(eligible,key=lambda a:(-metrics[a][1],a))[:1]
            if recovery:
                pending_stress=False
        last={a:(0.45/len(core) if a in core else 0.,
                 0.10 if a in opportunity else 0.,
                 0.10/len(rv) if a in rv else 0.,
                 0.10/len(recovery) if a in recovery else 0.) for a in ASSETS}
        return last
    return compute
