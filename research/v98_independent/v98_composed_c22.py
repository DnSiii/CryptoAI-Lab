"""V98 C22 preregistered continuous participation seven-slot composed engine; training only."""
import math
from .phase243_native_funding_cashflow import ASSETS

WARMUP=2160
REBALANCE=24
BUDGETS=(.50,.15,.15,.10)

def c22_model():
    previous={a:(0.,)*4 for a in ASSETS}
    regime=0.
    def compute(history):
        nonlocal previous,regime
        if set(history)!=set(ASSETS): raise ValueError("C22_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS): raise ValueError("C22_MISALIGNED")
        if n<WARMUP+1 or (n-1)%REBALANCE: return previous
        f={}
        for a in ASSETS:
            p=history[a][-WARMUP-1:]
            if any(not math.isfinite(float(x)) or x<=0 for x in p): raise ValueError("C22_INVALID_PRICE")
            r=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            v=max(.0001,math.sqrt(sum(x*x for x in r[-720:])/720))
            f[a]=dict(m90=math.log(p[-1]/p[-2161]),m30=math.log(p[-1]/p[-721]),
                      m7=math.log(p[-1]/p[-169]),vol=v,
                      draw30=p[-1]/max(p[-721:])-1)
        breadth=sum(f[a]["m90"]>0 for a in ASSETS)
        regime=(.50 if breadth==0 else .75 if breadth==1 else 1.)
        med30=sorted(f[a]["m30"] for a in ASSETS)[1:3]
        median30=sum(med30)/2
        scores={}
        for a in ASSETS:
            x=f[a]
            inv=1/x["vol"]
            scores[a]=(
                max(0.,min(x["m90"],x["m30"]))*inv,
                max(0.,-x["m7"])*inv if x["m90"]>0 and x["m30"]>0 else 0.,
                max(0.,x["m30"]-median30)*inv if x["m90"]>0 else 0.,
                max(0.,x["m7"])*inv if x["draw30"]<-.15 and x["m30"]<0 else 0.
            )
        weights={a:[0.]*4 for a in ASSETS}
        for j,budget in enumerate(BUDGETS):
            total=sum(scores[a][j] for a in ASSETS)
            if total>0:
                for a in ASSETS: weights[a][j]=budget*scores[a][j]/total
        previous={a:tuple(weights[a]) for a in ASSETS}
        return previous
    def router(_): return regime
    return compute,router

def c22_allocator(sleeves,routers,governor):
    from .v98_b0_causal_overlay import compose_weights
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
