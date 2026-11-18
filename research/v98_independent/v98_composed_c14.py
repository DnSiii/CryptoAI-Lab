"""V98 C14 preregistered seven-slot research candidate; no production or PnL claims."""
import math
from .phase243_native_funding_cashflow import ASSETS
from .v98_b0_causal_overlay import compose_weights

WARMUP=2160
REBALANCE=24
GROSS_CAP=.90
ASSET_CAP=.40
BUDGETS=(.38,.18,.16,.12)

def composed_c14_sleeves():
    previous={a:(0.,0.,0.,0.) for a in ASSETS}
    def compute(history):
        nonlocal previous
        if set(history)!=set(ASSETS): raise ValueError("C14_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS): raise ValueError("C14_MISALIGNED")
        i=n-1
        if i<WARMUP or i%REBALANCE: return previous
        f={}
        for a in ASSETS:
            p=history[a][i-WARMUP:i+1]
            if any(not math.isfinite(float(v)) or v<=0 for v in p): raise ValueError("C14_INVALID_CLOSE")
            r=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol=max(1e-8,math.sqrt(sum(x*x for x in r[-168:])/168))
            m30=math.log(p[-1]/p[-721])
            m7=math.log(p[-1]/p[-169])
            m2=math.log(p[-1]/p[-49])
            # Independent efficiency proxy: directional path divided by absolute path.
            efficiency=abs(sum(r[-336:]))/max(1e-8,sum(abs(x) for x in r[-336:]))
            f[a]=(m30,m7,m2,vol,efficiency)
        # Growth: persistent multi-horizon positive drift with efficient path.
        growth=[a for a in ASSETS if f[a][0]>0 and f[a][1]>0 and f[a][4]>.12]
        # Opportunity: positive medium drift after a short pullback.
        opportunity=[a for a in ASSETS if f[a][0]>0 and f[a][1]>0 and f[a][2]<0]
        # Relative-value: dispersion leadership on 7d, gated by positive 30d.
        leader=max(ASSETS,key=lambda a:(f[a][1],-list(ASSETS).index(a)))
        relative=[leader] if f[leader][1]>0 and f[leader][0]>0 and f[leader][1]>sum(f[a][1] for a in ASSETS)/4 else []
        # Stress/recovery: broad positive 48h breadth after negative 7d breadth.
        stress=[a for a in ASSETS if f[a][1]<0 and f[a][2]>0]
        recovery=stress if len(stress)>=2 else []
        w={a:[0.]*4 for a in ASSETS}
        for j,group in enumerate((growth,opportunity,relative,recovery)):
            if not group: continue
            inverse={a:1/f[a][3] for a in group}
            denom=sum(inverse.values())
            for a in group: w[a][j]=BUDGETS[j]*inverse[a]/denom
        previous={a:tuple(w[a]) for a in ASSETS}
        return previous
    return compute

def c14_router(closes):
    p=list(closes)
    if len(p)<721:return 0.
    q=p[-721:]
    if any(not math.isfinite(float(v)) or v<=0 for v in q):raise ValueError("C14_INVALID_ROUTER_CLOSE")
    r30=math.log(q[-1]/q[0])
    r7=math.log(q[-1]/q[-169])
    return 1. if r30>0 and r7>0 else (.35 if r30>0 else .0)

def c14_allocator(sleeves,routers,governor):
    return compose_weights(sleeves,routers,governor,gross_cap=GROSS_CAP,asset_cap=ASSET_CAP)
