"""C12 preregistered seven-slot *different* architecture: volatility-adjusted
persistent trend, compression breakout, relative strength and post-stress
re-entry. Clean-4 training only; never tune from C11 ablation outcomes.
"""
import math
from .phase243_native_funding_cashflow import ASSETS
from .v98_b0_causal_overlay import compose_weights

LOOKBACK=1440
SLOW=480
FAST=96
STEP=24

def composed_c12_sleeves():
    last={a:(0.,0.,0.,0.) for a in ASSETS}
    prev_stress=False
    recovery_until=-1
    def compute(history):
        nonlocal last,prev_stress,recovery_until
        if set(history)!=set(ASSETS): raise ValueError("C12_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS): raise ValueError("C12_MISALIGNED")
        i=n-1
        if i<LOOKBACK or i%STEP: return last
        m={}
        for a in ASSETS:
            p=history[a][i-LOOKBACK:i+1]
            if any(not math.isfinite(float(x)) or x<=0 for x in p):
                raise ValueError("C12_BAD_CLOSE")
            logret=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol=math.sqrt(sum(x*x for x in logret[-SLOW:])/SLOW)
            prior=math.sqrt(sum(x*x for x in logret[-LOOKBACK:-SLOW])/ (LOOKBACK-SLOW))
            slow=sum(logret[-SLOW:])
            fast=sum(logret[-FAST:])
            m[a]=(slow,fast,max(vol,1e-8),prior)
        # Growth: diversified, persistent positive slow/fast trend, risk parity.
        growth=[a for a in ASSETS if m[a][0]>0 and m[a][1]>0]
        # Opportunity: volatility compression followed by positive impulse.
        opp=[a for a in ASSETS if m[a][2]<m[a][3] and m[a][1]>0]
        # Relative value: leadership conditional on positive absolute trend.
        leaders=sorted((a for a in ASSETS if m[a][0]>0),
                       key=lambda a:(-m[a][0]/m[a][2],a))[:1]
        # Stress/recovery: enter only after a broad negative regime ends.
        stressed=sum(m[a][0]<0 for a in ASSETS)>=3
        if prev_stress and not stressed: recovery_until=i+7*STEP
        if stressed: recovery_until=-1
        prev_stress=stressed
        recovery=[a for a in ASSETS if i<recovery_until and m[a][1]>0]
        groups=(growth,opp,leaders,recovery)
        budgets=(.36,.14,.12,.10)
        weights={a:[0.]*4 for a in ASSETS}
        for slot,(group,budget) in enumerate(zip(groups,budgets)):
            if not group: continue
            inverse={a:1/m[a][2] for a in group}
            denom=sum(inverse.values())
            for a in group: weights[a][slot]=budget*inverse[a]/denom
        last={a:tuple(weights[a]) for a in ASSETS}
        return last
    return compute

def c12_router(closes):
    p=list(closes)
    if len(p)<SLOW+1: return 0.
    if any(not math.isfinite(float(x)) or x<=0 for x in p[-SLOW-1:]):
        raise ValueError("C12_BAD_ROUTER_CLOSE")
    slow=math.log(p[-1]/p[-SLOW-1])
    fast=math.log(p[-1]/p[-FAST-1])
    return 1. if slow>0 and fast>0 else (.5 if fast>0 else .25)

def c12_allocator(sleeves,routers,governor):
    return compose_weights(sleeves,routers,governor,gross_cap=.72,asset_cap=.36)
