"""V98 C26 independent sparse-breakout seven-slot model; preregistered training only."""
import math
import statistics
from .phase243_native_funding_cashflow import ASSETS
from .v98_b0_causal_overlay import compose_weights

WARMUP=4320
BUDGETS=(.55,.20,.15,.10)

def c26_model():
    def compute(history):
        if set(history)!=set(ASSETS):
            raise ValueError("C26_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS):
            raise ValueError("C26_MISALIGNED")
        if n<WARMUP+1:
            return {a:(0.,)*4 for a in ASSETS}
        features={}
        for a in ASSETS:
            p=[float(x) for x in history[a][-WARMUP-1:]]
            if any(not math.isfinite(x) or x<=0 for x in p):
                raise ValueError("C26_INVALID_CLOSE")
            r=[math.log(p[i]/p[i-1]) for i in range(1,len(p))]
            v14=max(1e-4,math.sqrt(sum(x*x for x in r[-336:])/336))
            v30=max(1e-4,math.sqrt(sum(x*x for x in r[-720:])/720))
            v90=max(1e-4,math.sqrt(sum(x*x for x in r[-2160:])/2160))
            m90=math.log(p[-1]/p[-2161])
            m180=math.log(p[-1]/p[-4321])
            above90=p[-1]>sum(p[-2160:])/2160
            above30=p[-1]>sum(p[-720:])/720
            high180=p[-1]>max(p[-4321:-1])
            high30=p[-1]>max(p[-721:-1])
            consolidation=(max(p[-721:-1])/min(p[-721:-1])-1)<.30
            drawdown60=min(p[-1441:-337])/max(p[-1441:-337])-1
            recovery=math.log(p[-1]/p[-337])
            features[a]=(v14,v30,v90,m90,m180,above90,above30,high180,high30,consolidation,drawdown60,recovery)
        median=statistics.median(features[a][3]/features[a][2] for a in ASSETS)
        scores={}
        for a in ASSETS:
            v14,v30,v90,m90,m180,above90,above30,high180,high30,consolidation,dd,recovery=features[a]
            core=max(0.,m90)/v30 if high180 and m90>0 else 0.
            opportunity=max(0.,m90)/v14 if consolidation and high30 and m90>0 and v14<v90 else 0.
            relative=max(0.,m90/v90-median) if above90 and m90>0 else 0.
            stress=max(0.,recovery)/v30 if dd<=-.15 and recovery>0 and above30 else 0.
            scores[a]=(core,opportunity,relative,stress)
        totals=[sum(scores[a][j] for a in ASSETS) for j in range(4)]
        return {a:tuple(BUDGETS[j]*scores[a][j]/totals[j] if totals[j]>0 else 0.
                        for j in range(4)) for a in ASSETS}
    def router(history):
        if len(history)<WARMUP+1:
            return 0.
        p=[float(x) for x in history[-WARMUP-1:]]
        if any(not math.isfinite(x) or x<=0 for x in p):
            raise ValueError("C26_INVALID_ROUTER_CLOSE")
        if p[-1]<=p[-4321]:
            return 0.
        base=1. if p[-1]>sum(p[-2160:])/2160 else .5
        r=[math.log(p[i]/p[i-1]) for i in range(1,len(p))]
        v14=math.sqrt(sum(x*x for x in r[-336:])/336)
        v90=math.sqrt(sum(x*x for x in r[-2160:])/2160)
        return base*(.5 if v90>0 and v14>2*v90 else 1.)
    return compute,router

def c26_allocator(sleeves,routers,governor):
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
