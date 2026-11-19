"""V98 C21 preregistered cross-sectional defensive rotation, training-only."""
import math
import statistics
from .phase243_native_funding_cashflow import ASSETS

WARMUP=2160
REBALANCE=168
BUDGETS=(.50,.15,.15,.10)

def c21_model():
    previous={a:(0.,)*4 for a in ASSETS}
    regime=0.
    def compute(history):
        nonlocal previous,regime
        if set(history)!=set(ASSETS): raise ValueError("C21_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS): raise ValueError("C21_MISALIGNED")
        if n<WARMUP+1 or (n-1)%REBALANCE: return previous
        f={}
        for a in ASSETS:
            p=history[a][-WARMUP-1:]
            if any(not math.isfinite(float(x)) or x<=0 for x in p): raise ValueError("C21_INVALID_PRICE")
            r=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            v=max(1e-8,math.sqrt(sum(x*x for x in r[-720:])/720))
            f[a]=dict(m90=math.log(p[-1]/p[-2161]),m30=math.log(p[-1]/p[-721]),
                      m7=math.log(p[-1]/p[-169]),m24=math.log(p[-1]/p[-25]),
                      vol=v,price=p[-1],high30=max(p[-721:-1]),
                      low30=min(p[-721:-1]),median7=statistics.median(p[-168:]),
                      vrecent=math.sqrt(sum(x*x for x in r[-168:])/168))
        breadth=sum(f[a]["m90"]>0 and f[a]["m30"]>0 for a in ASSETS)
        regime=0. if breadth==0 else (.5 if breadth==1 else 1.)
        leaders=sorted((a for a in ASSETS if f[a]["m90"]>0 and f[a]["m30"]>0),
                       key=lambda a:(-f[a]["m90"]/f[a]["vol"],ASSETS.index(a)))[:2]
        opportunity=[a for a in ASSETS if f[a]["price"]>f[a]["high30"] and
                     f[a]["vrecent"]<f[a]["vol"] and f[a]["m7"]>0]
        median90=statistics.median(f[a]["m90"] for a in ASSETS)
        relative=[a for a in ASSETS if f[a]["m90"]>median90 and f[a]["m7"]>0]
        recovery=[a for a in ASSETS if f[a]["low30"]/f[a]["high30"]<.80 and
                  f[a]["price"]>f[a]["median7"] and f[a]["m7"]>0 and f[a]["m90"]<0]
        groups=(leaders,opportunity,relative,recovery)
        weights={a:[0.]*4 for a in ASSETS}
        for j,g in enumerate(groups):
            if not g: continue
            if j==0:
                scores={a:max(1e-8,f[a]["m90"]/f[a]["vol"]) for a in g}
            else:
                scores={a:1. for a in g}
            denom=sum(scores.values())
            for a in g: weights[a][j]=BUDGETS[j]*scores[a]/denom
        previous={a:tuple(weights[a]) for a in ASSETS}
        return previous
    def router(_): return regime
    return compute,router

def c21_allocator(sleeves,routers,governor):
    from .v98_b0_causal_overlay import compose_weights
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
