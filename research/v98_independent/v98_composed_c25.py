"""V98 C25 independent seven-slot composed candidate. Training only; preregistered."""
import math
import statistics
from .phase243_native_funding_cashflow import ASSETS
from .v98_b0_causal_overlay import compose_weights

WARMUP=2880
BUDGETS=(.50,.20,.20,.10)

def c25_model():
    def compute(history):
        if set(history)!=set(ASSETS): raise ValueError("C25_CLEAN4_ONLY")
        n=len(history[ASSETS[0]])
        if any(len(history[a])!=n for a in ASSETS): raise ValueError("C25_MISALIGNED")
        if n<WARMUP+1: return {a:(0.,)*4 for a in ASSETS}
        f={}
        for a in ASSETS:
            p=history[a][-WARMUP-1:]
            if any(not math.isfinite(float(v)) or v<=0 for v in p):
                raise ValueError("C25_INVALID_CLOSE")
            r=[math.log(p[i]/p[i-1]) for i in range(1,len(p))]
            vol14=math.sqrt(sum(v*v for v in r[-336:])/336)
            vol90=math.sqrt(sum(v*v for v in r[-2160:])/2160)
            m120=math.log(p[-1]/p[-2881])
            m30=math.log(p[-1]/p[-721])
            m7=math.log(p[-1]/p[-169])
            dd30=p[-1]/max(p[-721:])-1
            f[a]=(max(vol14,1e-4),max(vol90,1e-4),m120,m30,m7,dd30)
        median30=statistics.median(f[a][3]/f[a][0] for a in ASSETS)
        scores={}
        for a in ASSETS:
            v14,v90,m120,m30,m7,dd=f[a]
            core=max(0.,m120)*max(0.,m30)/v90 if m30>0 else 0.
            opportunity=max(0.,1-v14/v90)*max(0.,m7)/v14 if m30>0 else 0.
            relative=max(0.,m30/v14-median30) if m120>0 else 0.
            recovery=max(0.,m7)/v14 if dd<=-.12 and m30>0 else 0.
            scores[a]=(core,opportunity,relative,recovery)
        totals=[sum(scores[a][j] for a in ASSETS) for j in range(4)]
        return {a:tuple(BUDGETS[j]*scores[a][j]/totals[j] if totals[j]>0 else 0.
                        for j in range(4)) for a in ASSETS}
    def router(history):
        if len(history)<WARMUP+1:return 0.
        p=history[-WARMUP-1:]
        if any(not math.isfinite(float(x)) or x<=0 for x in p): raise ValueError("C25_INVALID_ROUTER_CLOSE")
        m120=math.log(p[-1]/p[-2881]);m30=math.log(p[-1]/p[-721])
        if m120<=0:return 0.
        base=1. if m30>0 else .5
        r=[math.log(p[i]/p[i-1]) for i in range(1,len(p))]
        v14=math.sqrt(sum(x*x for x in r[-336:])/336)
        v90=math.sqrt(sum(x*x for x in r[-2160:])/2160)
        return base*(.5 if v90>0 and v14>1.75*v90 else 1.)
    return compute,router

def c25_allocator(sleeves,routers,governor):
    return compose_weights(sleeves,routers,governor,gross_cap=.90,asset_cap=.40)
