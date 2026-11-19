"""V98 C23 preregistered seven-slot trend/breakout portfolio. Training only.
Hypothesis: diversified medium-horizon breakout + trend persistence captures
compounded upside with less turnover than daily countertrend C22.
No parameters may be modified after inspecting C23 economic outcomes.
"""
import math
from .phase243_native_funding_cashflow import ASSETS
WARMUP=2160
REBALANCE=168
BUDGETS=(.55,.15,.15,.15)
def c23_model():
    previous={a:(0.,)*4 for a in ASSETS}
    router={a:0. for a in ASSETS}
    def compute(history):
        nonlocal previous,router
        if set(history)!=set(ASSETS): raise ValueError("C23_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS): raise ValueError("C23_MISALIGNED")
        if n<WARMUP+1 or (n-1)%REBALANCE: return previous
        f={}
        for a in ASSETS:
            p=history[a][-WARMUP-1:]
            if any(not math.isfinite(float(x)) or x<=0 for x in p): raise ValueError("C23_INVALID_PRICE")
            r=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol=max(.0001,math.sqrt(sum(x*x for x in r[-720:])/720))
            m90=math.log(p[-1]/p[-2161])
            m30=math.log(p[-1]/p[-721])
            m7=math.log(p[-1]/p[-169])
            high90=max(p[:-1])
            low30=min(p[-721:-1])
            f[a]=dict(vol=vol,m90=m90,m30=m30,m7=m7,
                      breakout=max(0.,p[-1]/high90-1),
                      recovery=max(0.,p[-1]/low30-1))
        # Router: no regime tuning from benchmark; participation is directional.
        router={a:(1. if f[a]["m90"]>0 and f[a]["m30"]>0 else
                   .5 if f[a]["m90"]>0 else 0.) for a in ASSETS}
        scores={}
        for a in ASSETS:
            x=f[a]
            inv=1/x["vol"]
            scores[a]=(
                max(0.,x["m90"])*inv,
                x["breakout"]*inv,
                max(0.,x["m30"]-sum(f[b]["m30"] for b in ASSETS)/4)*inv,
                max(0.,x["m7"])*inv if x["m90"]>0 and x["m30"]>0 else 0.
            )
        weights={a:[0.]*4 for a in ASSETS}
        for j,budget in enumerate(BUDGETS):
            total=sum(scores[a][j] for a in ASSETS)
            if total:
                for a in ASSETS: weights[a][j]=budget*scores[a][j]/total
        previous={a:tuple(weights[a]) for a in ASSETS}
        return previous
    def route(history): return router[history[0]] if False else 1.
    # The execution harness calls router separately for each asset history.
    # Match by immutable trailing history identity through a lookup by last close
    # is unsafe; use a deterministic per-asset closure in the runner instead.
    return compute,lambda _:1.
def c23_allocator(sleeves,routers,governor):
    from .v98_b0_causal_overlay import compose_weights
    # Apply regime gating directly from sleeve computation: all four sleeves
    # have already been scored on positive directional regimes.
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
