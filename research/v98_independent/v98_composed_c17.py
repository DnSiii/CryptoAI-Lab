"""Preregistered C17 sparse seven-slot architecture; no benchmark/holdout inputs."""
import math
from .phase243_native_funding_cashflow import ASSETS

WARMUP = 2160
REBALANCE = 168
BUDGETS = (.50, .20, .20, .10)

def c17_model():
    previous = {a:(0.,)*4 for a in ASSETS}
    regime = 0.
    def compute(history):
        nonlocal previous, regime
        if set(history) != set(ASSETS):
            raise ValueError("C17_CLEAN4_ONLY")
        n = len(history[ASSETS[0]])
        if any(len(history[a]) != n for a in ASSETS):
            raise ValueError("C17_MISALIGNED")
        i = n-1
        if i < WARMUP or i % REBALANCE:
            return previous
        f = {}
        for a in ASSETS:
            p = history[a][-WARMUP-1:]
            if len(p) != WARMUP+1 or any(not math.isfinite(float(x)) or x <= 0 for x in p):
                raise ValueError("C17_INVALID_CLOSE")
            logreturns = [math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol = max(1e-8, math.sqrt(sum(x*x for x in logreturns[-720:])/720))
            f[a] = dict(m90=math.log(p[-1]/p[-2161]),
                        m30=math.log(p[-1]/p[-721]),
                        m14=math.log(p[-1]/p[-337]),
                        m7=math.log(p[-1]/p[-169]),
                        breakout=p[-1]>max(p[-721:-1]),
                        dd=p[-1]/max(p[-721:])-1,
                        vol=vol)
        basket = sum(f[a]["m30"] for a in ASSETS)/len(ASSETS)
        breadth = sum(f[a]["m30"]>0 for a in ASSETS)
        regime = 0. if basket < math.log(.8) else (1. if basket > 0 and breadth >= 2 else .5)
        growth = [a for a in ASSETS if f[a]["m90"]>0 and f[a]["m30"]>0]
        opportunity = [a for a in ASSETS if f[a]["breakout"] and f[a]["m7"]>0]
        ranked = sorted(ASSETS,key=lambda a:(-f[a]["m90"],ASSETS.index(a)))
        relative = [a for a in ranked[:2] if f[a]["m90"]>0]
        recovery = [a for a in ASSETS if f[a]["dd"]<=-.20 and f[a]["m14"]>=math.log(1.08) and f[a]["m7"]>0]
        groups = (growth,opportunity,relative,recovery)
        active = sum(BUDGETS[j] for j,g in enumerate(groups) if g)
        weights = {a:[0.]*4 for a in ASSETS}
        if active:
            for j,group in enumerate(groups):
                if not group: continue
                inv = {a:1/f[a]["vol"] for a in group}
                denominator = sum(inv.values())
                for a in group:
                    weights[a][j] = (BUDGETS[j]/active)*inv[a]/denominator
        previous = {a:tuple(weights[a]) for a in ASSETS}
        return previous
    def router(_completed_closes):
        return regime
    return compute, router

def c17_allocator(sleeves,routers,governor):
    from .v98_b0_causal_overlay import compose_weights
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
