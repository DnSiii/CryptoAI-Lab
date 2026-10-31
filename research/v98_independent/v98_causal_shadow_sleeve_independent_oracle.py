#!/usr/bin/env python3
"""V98 future-only independent arithmetic oracle for shadow allocator, no market PnL."""
import itertools,math
import numpy as np
from v98_causal_shadow_sleeve_allocator import allocate
ACT=(0.,.5,1.)
W=(.1,.2,.3,.4)
def independent(core,sleeves,old,shadow,funding,ready=True,fee=.0004,slip=.0002,cap=.84):
    inputs=[list(map(float,core))]+[list(map(float,s)) for s in sleeves]
    gross=[math.fsum(abs(v) for v in s) for s in inputs]
    means=[max(-.5,min(.5,math.fsum(float(shadow[i][k])*W[k] for k in range(4)))) for i in range(4)]
    cov=[[math.fsum(W[k]*(float(shadow[i][k])-means[i])*(float(shadow[j][k])-means[j]) for k in range(4))*(1. if i==j else .5)
          for j in range(4)] for i in range(4)]
    rates=[math.fsum(float(funding[k][j]) for k in range(21))/21 for j in range(4)]
    choices=[]
    for factors in itertools.product(ACT,repeat=4):
        if not ready and any(factors[1:]):continue
        vg=math.fsum(gross[i]*factors[i] for i in range(4))
        if vg>cap+1e-10:continue
        net=[math.fsum(inputs[i][j]*factors[i] for i in range(4)) for j in range(4)]
        turn=math.fsum(abs(net[j]-float(old[j])) for j in range(4))
        exposure=[gross[i]*factors[i] for i in range(4)]
        predicted=math.fsum(exposure[i]*means[i] for i in range(4))
        variance=math.fsum(exposure[i]*cov[i][j]*exposure[j] for i in range(4) for j in range(4))
        carry=42*math.fsum(net[j]*rates[j] for j in range(4))
        utility=predicted-.5*max(0.,variance)-turn*(fee+slip)-carry
        choices.append((utility,turn,vg,factors,net))
    return min(choices,key=lambda x:(-x[0],x[1],x[2],x[3]))
def run():
    rng=np.random.default_rng(9803102)
    checked=0
    for case in range(200):
        core=rng.uniform(-.14,.14,4)
        sleeves=rng.uniform(-.065,.065,(3,4))
        old=rng.uniform(-.2,.2,4)
        shadow=rng.normal(0,.12,(4,4))
        funding=rng.normal(0,.0003,(21,4))
        ready=(case%9)!=0
        original=allocate(core,sleeves,old,shadow,funding,ready=ready)
        other=independent(core,sleeves,old,shadow,funding,ready=ready)
        if original["factors"]!=other[3]:
            raise ValueError("V98_SHADOW_INDEPENDENT_ACTION_MISMATCH_"+str(case))
        if abs(original["expected_net_log_utility"]-other[0])>1e-10:
            raise ValueError("V98_SHADOW_INDEPENDENT_UTILITY_MISMATCH_"+str(case))
        if max(abs(original["net_weights"][j]-other[4][j]) for j in range(4))>1e-10:
            raise ValueError("V98_SHADOW_INDEPENDENT_NET_MISMATCH_"+str(case))
        if abs(original["virtual_gross"]-other[2])>1e-10:
            raise ValueError("V98_SHADOW_INDEPENDENT_GROSS_MISMATCH_"+str(case))
        tampered=original["net_weights"].copy();tampered[0]+=.001
        if max(abs(tampered[j]-other[4][j]) for j in range(4))<1e-4:
            raise AssertionError("V98_SHADOW_ORACLE_TAMPER_NOT_DETECTED")
        checked+=1
    return {"decision":"PASS_INDEPENDENT_200_ACTION_UTILITY_NET_GROSS_RECONCILIATIONS_NOT_PNL",
            "checked":checked,"mismatches":0,"tamper_detected":True,
            "training_or_holdout_accessed":False,"live_authorized":False}
if __name__=="__main__":
    print(run())
