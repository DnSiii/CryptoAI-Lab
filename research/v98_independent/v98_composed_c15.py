"""V98 C15 preregistered structural-breakout seven-slot research candidate."""
import math
from .phase243_native_funding_cashflow import ASSETS
from .v98_b0_causal_overlay import compose_weights
WARMUP=2160
REBALANCE=24
BUDGETS=(.40,.22,.20,.12)
GROSS_CAP=.90
ASSET_CAP=.40

def composed_c15_sleeves():
    previous={a:(0.,0.,0.,0.) for a in ASSETS}
    def compute(history):
        nonlocal previous
        if set(history)!=set(ASSETS): raise ValueError("C15_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS): raise ValueError("C15_MISALIGNED")
        i=n-1
        if i<WARMUP or i%REBALANCE: return previous
        f={}
        for a in ASSETS:
            p=history[a][i-WARMUP:i+1]
            if any(not math.isfinite(float(v)) or v<=0 for v in p): raise ValueError("C15_INVALID_CLOSE")
            r=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol=max(1e-8,math.sqrt(sum(x*x for x in r[-168:])/168))
            vol14=math.sqrt(sum(x*x for x in r[-336:])/336)
            volprior42=math.sqrt(sum(x*x for x in r[-1344:-336])/1008)
            f[a]=dict(m90=math.log(p[-1]/p[-2161]),m30=math.log(p[-1]/p[-721]),
                      m7=math.log(p[-1]/p[-169]),m2=math.log(p[-1]/p[-49]),
                      breakout90=p[-1]>max(p[-2161:-1]),
                      breakout14=p[-1]>max(p[-337:-1]),
                      compression=vol14<volprior42,vol=vol)
        growth=[a for a in ASSETS if f[a]['breakout90'] and f[a]['m30']>0]
        opportunity=[a for a in ASSETS if f[a]['compression'] and f[a]['breakout14']]
        leader=max(ASSETS,key=lambda a:(f[a]['m30'],-list(ASSETS).index(a)))
        relative=[leader] if f[leader]['m30']>max(0.,sum(f[a]['m30'] for a in ASSETS)/4) else []
        recovery=[a for a in ASSETS if f[a]['m30']<math.log(.85) and f[a]['m7']>0 and f[a]['m2']>0]
        w={a:[0.]*4 for a in ASSETS}
        for j,group in enumerate((growth,opportunity,relative,recovery)):
            if not group: continue
            inverse={a:1/f[a]['vol'] for a in group}
            denom=sum(inverse.values())
            for a in group:w[a][j]=BUDGETS[j]*inverse[a]/denom
        previous={a:tuple(w[a]) for a in ASSETS}
        return previous
    return compute

def c15_router(closes):
    p=list(closes)
    if len(p)<2161:return 0.
    q=p[-2161:]
    if any(not math.isfinite(float(v)) or v<=0 for v in q):raise ValueError("C15_INVALID_ROUTER_CLOSE")
    # Per-asset causal router: 90d drift; breadth is represented by active sleeves.
    return 1. if q[-1]>q[0] else .4 if q[-1]>q[-721] else 0.

def c15_allocator(sleeves,routers,governor):
    return compose_weights(sleeves,routers,governor,gross_cap=GROSS_CAP,asset_cap=ASSET_CAP)
