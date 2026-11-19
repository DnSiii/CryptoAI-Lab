"""V98 C19 preregistered composed seven-slot portfolio. Completed-close signals only."""
import math
import statistics
from .phase243_native_funding_cashflow import ASSETS

WARMUP = 2160
REBALANCE = 72
BUDGETS = (.50, .20, .20, .10)

def c19_model():
    previous = {a: (0.,)*4 for a in ASSETS}
    regime = 0.
    def compute(history):
        nonlocal previous, regime
        if set(history) != set(ASSETS):
            raise ValueError("C19_CLEAN4_ONLY")
        n = len(history[ASSETS[0]])
        if any(len(history[a]) != n for a in ASSETS):
            raise ValueError("C19_MISALIGNED")
        i = n-1
        if i < WARMUP or i % REBALANCE:
            return previous
        f = {}
        for a in ASSETS:
            p = history[a][-WARMUP-1:]
            if len(p) != WARMUP+1 or any(not math.isfinite(float(x)) or x <= 0 for x in p):
                raise ValueError("C19_INVALID_CLOSE")
            r = [math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol30 = max(1e-8,math.sqrt(sum(x*x for x in r[-720:])/720))
            m90 = math.log(p[-1]/p[-2161])
            m30 = math.log(p[-1]/p[-721])
            m7 = math.log(p[-1]/p[-169])
            m3 = math.log(p[-1]/p[-73])
            prior7 = math.log(p[-169]/p[-337])
            geo90 = math.exp(sum(math.log(x) for x in p[-2160:])/2160)
            f[a] = dict(m90=m90,m30=m30,m7=m7,m3=m3,prior7=prior7,
                        vol30=vol30,geo90=geo90,close=p[-1],
                        prior_high30=max(p[-721:-1]),
                        dd30=p[-1]/max(p[-721:])-1)
        breadth = sum(f[a]["m90"]>0 for a in ASSETS)
        regime = 0. if breadth==0 else (.5 if breadth==1 else 1.)
        median30 = statistics.median(f[a]["m30"] for a in ASSETS)
        growth = [a for a in ASSETS if f[a]["m90"]>0 and f[a]["close"]>f[a]["geo90"]]
        opportunity = [a for a in ASSETS if f[a]["m3"]>0 and f[a]["close"]>f[a]["prior_high30"]]
        relative = sorted([a for a in ASSETS if f[a]["m30"]>max(0.,median30) and f[a]["m7"]>0],
                          key=lambda a:(-(f[a]["m30"]-median30),ASSETS.index(a)))[:2]
        recovery = [a for a in ASSETS if f[a]["dd30"]<=-.20 and f[a]["m3"]>0
                    and f[a]["m7"]>f[a]["prior7"]]
        groups=(growth,opportunity,relative,recovery)
        active=sum(BUDGETS[j] for j,g in enumerate(groups) if g)
        weights={a:[0.]*4 for a in ASSETS}
        if active:
            for j,g in enumerate(groups):
                if not g: continue
                if j==0:
                    scores={a:max(1e-12,f[a]["m90"]/f[a]["vol30"]) for a in g}
                else:
                    scores={a:1. for a in g}
                denominator=sum(scores.values())
                for a in g:
                    weights[a][j]=BUDGETS[j]/active*scores[a]/denominator
        previous={a:tuple(weights[a]) for a in ASSETS}
        return previous
    def router(_completed_closes):
        return regime
    return compute,router

def c19_allocator(sleeves,routers,governor):
    from .v98_b0_causal_overlay import compose_weights
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
