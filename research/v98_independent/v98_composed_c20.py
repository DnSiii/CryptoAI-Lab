"""V98 C20 independent seven-slot slow trend / displacement composition."""
import math
import statistics
from .phase243_native_funding_cashflow import ASSETS

WARMUP=4320
REBALANCE=168
BUDGETS=(.55,.15,.20,.10)

def c20_model():
    previous={a:(0.,)*4 for a in ASSETS}
    regime=0.
    def compute(history):
        nonlocal previous,regime
        if set(history)!=set(ASSETS):
            raise ValueError("C20_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS):
            raise ValueError("C20_MISALIGNED")
        i=n-1
        if i<WARMUP or i%REBALANCE:
            return previous
        f={}
        for a in ASSETS:
            p=history[a][-WARMUP-1:]
            if len(p)!=WARMUP+1 or any(not math.isfinite(float(v)) or v<=0 for v in p):
                raise ValueError("C20_INVALID_CLOSE")
            returns=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol=max(1e-8,math.sqrt(sum(r*r for r in returns[-720:])/720))
            f[a]=dict(
                m180=math.log(p[-1]/p[-4321]),
                m90=math.log(p[-1]/p[-2161]),
                m30=math.log(p[-1]/p[-721]),
                m7=math.log(p[-1]/p[-169]),
                m24=math.log(p[-1]/p[-25]),
                vol=vol,
                median30=statistics.median(p[-720:]),
                price=p[-1],
                dd30=p[-1]/max(p[-721:])-1)
        breadth=sum(f[a]["m30"]>0 and f[a]["m180"]>0 for a in ASSETS)
        regime=0. if breadth==0 else (.5 if breadth==1 else 1.)
        med90=statistics.median(f[a]["m90"] for a in ASSETS)
        growth=[a for a in ASSETS if f[a]["m180"]>0 and f[a]["m30"]>0 and f[a]["price"]>f[a]["median30"]]
        opportunity=[a for a in ASSETS if f[a]["m30"]>0 and f[a]["m24"]>1.5*f[a]["vol"]*math.sqrt(24)]
        relative=sorted((a for a in ASSETS if f[a]["m90"]>med90 and f[a]["m30"]>0),
                        key=lambda a:(-f[a]["m90"],ASSETS.index(a)))[:2]
        recovery=[a for a in ASSETS if f[a]["dd30"]<=-.15 and f[a]["m7"]>0 and f[a]["m24"]>0]
        groups=(growth,opportunity,relative,recovery)
        active=sum(BUDGETS[j] for j,g in enumerate(groups) if g)
        w={a:[0.]*4 for a in ASSETS}
        if active:
            for j,g in enumerate(groups):
                if not g:continue
                scores={a:(max(1e-9,f[a]["m180"]/f[a]["vol"]) if j==0 else 1.) for a in g}
                denom=sum(scores.values())
                for a in g:w[a][j]=BUDGETS[j]/active*scores[a]/denom
        previous={a:tuple(w[a]) for a in ASSETS}
        return previous
    def router(_completed_closes):return regime
    return compute,router

def c20_allocator(sleeves,routers,governor):
    from .v98_b0_causal_overlay import compose_weights
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
