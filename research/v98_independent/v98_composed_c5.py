"""V98 C5 preregistered crisis-confirmation composed sleeves. Training only."""
import math
from .phase243_native_funding_cashflow import ASSETS

LONG=2160
MID=720
SHORT=168
STEP=24

def composed_c5_sleeves():
    last={a:(0.,0.,0.,0.) for a in ASSETS}
    def compute(history):
        nonlocal last
        if set(history)!=set(ASSETS):
            raise ValueError("C5_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS):
            raise ValueError("C5_MISALIGNED")
        i=n-1
        if i<LONG or i%STEP:
            return last
        metrics={}
        for a in ASSETS:
            p=history[a][i-LONG:i+1]
            if len(p)!=LONG+1 or any(not math.isfinite(float(x)) or x<=0 for x in p):
                raise ValueError("C5_INVALID_CLOSE")
            r90=math.log(p[-1]/p[0])
            r30=math.log(p[-1]/p[-MID-1])
            r7=math.log(p[-1]/p[-SHORT-1])
            hourly=[math.log(p[k]/p[k-1]) for k in range(len(p)-MID,len(p))]
            mu=sum(hourly)/MID
            sd=math.sqrt(sum((x-mu)**2 for x in hourly)/(MID-1))
            recent=p[-MID-1:]
            midpoint=math.sqrt(min(recent)*max(recent))
            metrics[a]=(r90,r30,r7,sd,p[-1]>midpoint)
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
        recovery=[]
        if sum(metrics[a][1]<0 for a in ASSETS)>=3 and seven_positive>=3:
            recovery=[a for a in ASSETS if metrics[a][2]>0 and metrics[a][4]]
        last={a:(0.45/len(core) if a in core else 0.,
                 0.10 if a in opportunity else 0.,
                 0.10/len(rv) if a in rv else 0.,
                 0.10/len(recovery) if a in recovery else 0.) for a in ASSETS}
        return last
    return compute
