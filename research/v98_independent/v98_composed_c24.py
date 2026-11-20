"""V98 C24 preregistered composed engine. Training only.
Distinct from rejected C23: hourly continuous cap projection with slow
time-series trend, cross-sectional acceleration, volatility-adjusted
breakout and stress/recovery sleeve. No C23 tuning or rescue.
Freeze before authenticated economic results. Clean-4 only.
"""
import math
from .phase243_native_funding_cashflow import ASSETS
from .v98_b0_causal_overlay import compose_weights
WARMUP=2160
BUDGETS=(.45,.20,.20,.15)
def c24_model():
    def compute(history):
        if set(history)!=set(ASSETS): raise ValueError("C24_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS): raise ValueError("C24_MISALIGNED")
        if n<WARMUP+1: return {a:(0.,)*4 for a in ASSETS}
        features={}
        for a in ASSETS:
            p=history[a][-WARMUP-1:]
            if any(not math.isfinite(float(v)) or v<=0 for v in p):
                raise ValueError("C24_INVALID_CLOSE")
            r=[math.log(p[i]/p[i-1]) for i in range(1,len(p))]
            vol=max(0.0001,math.sqrt(sum(v*v for v in r[-336:])/336))
            m90=math.log(p[-1]/p[-2161])
            m30=math.log(p[-1]/p[-721])
            m14=math.log(p[-1]/p[-337])
            m7=math.log(p[-1]/p[-169])
            prior_high=max(p[-721:-25])
            drawdown=p[-1]/max(p[-721:])-1
            features[a]=(vol,m90,m30,m14,m7,max(0.,p[-1]/prior_high-1),drawdown)
        avg30=sum(features[a][2] for a in ASSETS)/4
        scores={}
        for a in ASSETS:
            vol,m90,m30,m14,m7,breakout,dd=features[a]
            inv=1/vol
            scores[a]=(
                max(0.,.6*m90+.4*m30)*inv,
                breakout*inv if m90>0 else 0.,
                max(0.,m14-avg30*.5)*inv if m90>0 else 0.,
                max(0.,m7)*inv if dd<-.08 and m30>0 else 0.
            )
        totals=[sum(scores[a][j] for a in ASSETS) for j in range(4)]
        return {a:tuple(BUDGETS[j]*scores[a][j]/totals[j] if totals[j] else 0.
                        for j in range(4)) for a in ASSETS}
    def router(history):
        if len(history)<WARMUP+1:return 0.
        p=history
        m90=math.log(p[-1]/p[-2161]);m30=math.log(p[-1]/p[-721])
        return 1. if m90>0 and m30>0 else (.65 if m90>0 else .25)
    return compute,router
def c24_allocator(sleeves,routers,governor):
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
