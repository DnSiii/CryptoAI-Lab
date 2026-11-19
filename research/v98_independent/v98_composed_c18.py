"""V98 C18 preregistered seven-slot portfolio; completed-close signals only."""
import math
import statistics
from .phase243_native_funding_cashflow import ASSETS

WARMUP=2160
REBALANCE=48
BUDGETS=(.45,.20,.25,.10)

def c18_model():
    previous={a:(0.,)*4 for a in ASSETS}
    regime=0.
    def compute(history):
        nonlocal previous,regime
        if set(history)!=set(ASSETS): raise ValueError("C18_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS): raise ValueError("C18_MISALIGNED")
        i=n-1
        if i<WARMUP or i%REBALANCE: return previous
        features={}
        for a in ASSETS:
            p=history[a][-WARMUP-1:]
            if len(p)!=WARMUP+1 or any(not math.isfinite(float(x)) or x<=0 for x in p):
                raise ValueError("C18_INVALID_CLOSE")
            r=[math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol14=max(1e-8,math.sqrt(sum(x*x for x in r[-336:])/336))
            preceding=[math.sqrt(sum(x*x for x in r[-336*(j+2):-336*(j+1)])/336) for j in range(3)]
            m60=math.log(p[-1]/p[-1441])
            m30=math.log(p[-1]/p[-721])
            m14=math.log(p[-1]/p[-337])
            m7=math.log(p[-1]/p[-169])
            prev7=math.log(p[-169]/p[-337])
            features[a]=dict(m60=m60,m30=m30,m14=m14,m7=m7,prev7=prev7,
                             sma60=sum(p[-1440:])/1440,
                             vol14=vol14,prev_vol_median=statistics.median(preceding),
                             dd30=p[-1]/max(p[-721:])-1,close=p[-1])
        basket=sum(features[a]["m30"] for a in ASSETS)/len(ASSETS)
        breadth=sum(features[a]["m14"]>0 for a in ASSETS)
        regime=0. if breadth==0 else (.5 if breadth==1 else 1.)
        growth=[a for a in ASSETS if features[a]["m60"]>0 and features[a]["close"]>features[a]["sma60"]]
        opportunity=[a for a in ASSETS if features[a]["vol14"]<features[a]["prev_vol_median"] and features[a]["m14"]>0]
        relative=sorted([a for a in ASSETS if features[a]["m30"]>max(0.,basket)],
                        key=lambda a:(-features[a]["m30"]/features[a]["vol14"],ASSETS.index(a)))[:2]
        recovery=[a for a in ASSETS if features[a]["dd30"]<=-.15 and features[a]["m7"]>0
                  and features[a]["m7"]>features[a]["prev7"]]
        groups=(growth,opportunity,relative,recovery)
        active=sum(BUDGETS[j] for j,g in enumerate(groups) if g)
        weights={a:[0.]*4 for a in ASSETS}
        if active:
            for j,g in enumerate(groups):
                if not g: continue
                inv={a:1/features[a]["vol14"] for a in g}
                denom=sum(inv.values())
                for a in g: weights[a][j]=BUDGETS[j]/active*inv[a]/denom
        previous={a:tuple(weights[a]) for a in ASSETS}
        return previous
    def router(_completed_closes):
        return regime
    return compute,router

def c18_allocator(sleeves,routers,governor):
    from .v98_b0_causal_overlay import compose_weights
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
