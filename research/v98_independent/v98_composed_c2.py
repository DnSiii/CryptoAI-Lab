"""V98 C2 preregistered independent seven-slot portfolio candidate.

Distinct from rejected C1: multi-horizon risk-adjusted momentum, volatility
compression expansion, relative leadership persistence, and reclaim after
systemic stress. Four nonnegative sleeves feed the existing causal regime
router and drawdown governor in next-open execution. Training only.
"""
import math
from .phase243_native_funding_cashflow import ASSETS

LOOKBACK=672
FAST=72
MID=336
VOL=168
STEP=168

def composed_c2_sleeves():
    last={a:(0.,0.,0.,0.) for a in ASSETS}
    def compute(history):
        nonlocal last
        if set(history)!=set(ASSETS):
            raise ValueError("C2_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS):
            raise ValueError("C2_MISALIGNED")
        i=n-1
        if i<LOOKBACK or i%STEP:
            return last
        metrics={}
        for a in ASSETS:
            p=history[a][i-LOOKBACK:i+1]
            if any(not math.isfinite(float(x)) or x<=0 for x in p):
                raise ValueError("C2_INVALID_CLOSE")
            r=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol=math.sqrt(sum(x*x for x in r[-VOL:])/VOL)
            prior=math.sqrt(sum(x*x for x in r[-2*VOL:-VOL])/VOL)
            slow=math.log(p[-1]/p[0])
            medium=math.log(p[-1]/p[-MID-1])
            fast=math.log(p[-1]/p[-FAST-1])
            # All features available at the completed decision close.
            metrics[a]=(slow,medium,fast,vol,prior)
        # Growth: persistence across 28d and 14d, selected by return/realized risk.
        eligible=[a for a in ASSETS if metrics[a][0]>0 and metrics[a][1]>0]
        core=sorted(eligible,key=lambda a:(-metrics[a][1]/max(metrics[a][3],1e-8),a))[:2]
        # Opportunity: positive impulse emerging from lower prior volatility.
        impulse=[a for a in ASSETS if metrics[a][2]>0 and
                 metrics[a][3]>metrics[a][4]*1.15 and metrics[a][1]>0]
        opp=sorted(impulse,key=lambda a:(-metrics[a][2],a))[:1]
        # Relative-value: long-only leadership persistence, not C1 dip buying.
        leaders=sorted(ASSETS,key=lambda a:(-metrics[a][1],a))
        rv=[leaders[0]] if metrics[leaders[0]][1]>0 and metrics[leaders[0]][2]>0 else []
        # Stress/recovery: broad market stress followed by positive 72h reclaim.
        stressed=sum(metrics[a][1]<0 for a in ASSETS)>=3
        recovery=sorted((a for a in ASSETS if metrics[a][2]>0 and metrics[a][1]<0),
                        key=lambda a:(-metrics[a][2],a))[:1] if stressed else []
        # Fixed budgets; idle sleeves remain cash. No leverage or redistribution.
        last={a:(0.42/len(core) if a in core else 0.,
                 0.12 if a in opp else 0.,
                 0.12 if a in rv else 0.,
                 0.09 if a in recovery else 0.) for a in ASSETS}
        return last
    return compute
