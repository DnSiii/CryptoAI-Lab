"""C16 preregistered seven-slot V98 candidate; no benchmark or holdout inputs."""
import math
import statistics
from .phase243_native_funding_cashflow import ASSETS

WARMUP=2160
REBALANCE=24
BUDGETS=(.45,.20,.20,.15)
WINDOW30=720
WINDOW7=168

def c16_model():
    previous={a:(0.,)*4 for a in ASSETS}
    regime=0.
    def compute(history):
        nonlocal previous,regime
        if set(history)!=set(ASSETS): raise ValueError("C16_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS):raise ValueError("C16_MISALIGNED")
        i=n-1
        if i<WARMUP or i%REBALANCE:return previous
        f={}
        for a in ASSETS:
            p=history[a][-WARMUP-1:]
            if any(not math.isfinite(float(x)) or x<=0 for x in p):raise ValueError("C16_INVALID_CLOSE")
            returns=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol=max(1e-8,math.sqrt(sum(x*x for x in returns[-WINDOW30:])/WINDOW30))
            # Four preceding, non-overlapping 7-day windows (no current window leakage).
            prior=[sum(returns[-WINDOW7*(k+2):-WINDOW7*(k+1)]) for k in range(4)]
            trailing=p[-WINDOW30-1:]
            dd=p[-1]/max(trailing)-1
            f[a]=dict(m90=math.log(p[-1]/p[-2161]),
                      m30=math.log(p[-1]/p[-721]),
                      m7=math.log(p[-1]/p[-169]),
                      m2=math.log(p[-1]/p[-49]),
                      median_prior=statistics.median(prior),
                      dd=dd,vol=vol)
        basket=sum(f[a]["m30"] for a in ASSETS)/4
        breadth=sum(f[a]["m30"]>0 for a in ASSETS)
        regime=0. if basket<math.log(.8) else (1. if basket>0 and breadth>=2 else .5)
        growth=[a for a in ASSETS if f[a]["m30"]>basket and f[a]["m90"]>0]
        opportunity=[a for a in ASSETS if f[a]["m7"]>f[a]["median_prior"] and f[a]["m30"]>0]
        relative=sorted([a for a in ASSETS if f[a]["m30"]>basket and f[a]["m30"]-basket>0],
                        key=lambda a:(-f[a]["m30"],ASSETS.index(a)))[:2]
        recovery=[a for a in ASSETS if f[a]["dd"]<=-.20 and f[a]["m7"]>math.log(1.05) and f[a]["m2"]>0]
        groups=(growth,opportunity,relative,recovery)
        active=sum(BUDGETS[j] for j,g in enumerate(groups) if g)
        weights={a:[0.]*4 for a in ASSETS}
        if active:
            for j,group in enumerate(groups):
                if not group:continue
                inv={a:1/f[a]["vol"] for a in group}
                denom=sum(inv.values())
                for a in group:weights[a][j]=(BUDGETS[j]/active)*inv[a]/denom
        previous={a:tuple(weights[a]) for a in ASSETS}
        return previous
    def router(_completed_closes):
        return regime
    return compute,router

def c16_allocator(sleeves,routers,governor):
    from .v98_b0_causal_overlay import compose_weights
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
