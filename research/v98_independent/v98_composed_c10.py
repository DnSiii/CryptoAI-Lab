"""V98 C10 distinct efficiency/volatility-budget seven-slot candidate. Training only."""
import math
from .phase243_native_funding_cashflow import ASSETS

LONG, MID, SHORT, STEP = 2160, 720, 168, 24

def composed_c10_sleeves():
    last = {a:(0.,0.,0.,0.) for a in ASSETS}
    was_stress = False
    armed = False
    recovery_asset = None
    recovery_end = -1

    def compute(history):
        nonlocal last,was_stress,armed,recovery_asset,recovery_end
        if set(history)!=set(ASSETS):
            raise ValueError("C10_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS):
            raise ValueError("C10_MISALIGNED")
        i=n-1
        if i<LONG or i%STEP:
            return last
        metrics={}
        for a in ASSETS:
            p=history[a][i-LONG:i+1]
            if len(p)!=LONG+1 or any(not math.isfinite(float(v)) or v<=0 for v in p):
                raise ValueError("C10_INVALID_CLOSE")
            returns=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            r90=sum(returns)
            r30=sum(returns[-MID:])
            r7=sum(returns[-SHORT:])
            efficiency=abs(r30)/max(sum(abs(x) for x in returns[-MID:]),1e-12)
            vol=math.sqrt(sum(x*x for x in returns[-MID:])/MID)
            metrics[a]=(r90,r30,r7,efficiency,vol)
        core=[a for a in ASSETS if metrics[a][0]>0 and metrics[a][1]>0 and metrics[a][3]>.20]
        opportunity=sorted((a for a in ASSETS if metrics[a][2]>0 and metrics[a][3]>.35),
                           key=lambda a:(-metrics[a][2],a))[:1]
        med=sorted(metrics[a][1] for a in ASSETS)
        median=(med[1]+med[2])/2
        rv=sorted((a for a in ASSETS if metrics[a][1]>median and metrics[a][2]>0),
                  key=lambda a:(-(metrics[a][1]-median),a))[:1]
        stress=sum(metrics[a][1]<0 for a in ASSETS)>=3
        if recovery_asset is not None and (i>=recovery_end or metrics[recovery_asset][2]<=0):
            recovery_asset=None
        if stress and not was_stress and recovery_asset is None:
            armed=True
        if armed and not stress and recovery_asset is None and sum(metrics[a][2]>0 for a in ASSETS)>=3:
            eligible=[a for a in ASSETS if metrics[a][2]>0 and metrics[a][1]>0]
            if eligible:
                recovery_asset=min(eligible,key=lambda a:(metrics[a][4],a))
                recovery_end=i+7*STEP
                armed=False
        was_stress=stress
        groups=(core,opportunity,rv,[recovery_asset] if recovery_asset else [])
        budgets=(.32,.16,.12,.12)
        weights={a:[0.]*4 for a in ASSETS}
        for slot,(eligible,budget) in enumerate(zip(groups,budgets)):
            if eligible:
                inverse={a:1/max(metrics[a][4],1e-8) for a in eligible}
                total=sum(inverse.values())
                for a in eligible:
                    weights[a][slot]=budget*inverse[a]/total
        last={a:tuple(weights[a]) for a in ASSETS}
        return last
    return compute

def efficiency_router(completed_closes):
    p=list(completed_closes)
    if len(p)<MID+1:
        return 0.
    p=p[-MID-1:]
    if any(not math.isfinite(float(v)) or v<=0 for v in p):
        raise ValueError("C10_ROUTER_INVALID_CLOSE")
    r=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
    net=sum(r)
    efficiency=abs(net)/max(sum(abs(x) for x in r),1e-12)
    return 1. if net>0 and efficiency>.20 else (.5 if net>0 else .25)

def c10_allocator(sleeves,routers,governor):
    from .v98_b0_causal_overlay import compose_weights
    return compose_weights(sleeves,routers,governor,gross_cap=.72,asset_cap=.35)
