#!/usr/bin/env python3
"""V98 WP preregistered channel-state seven-slot targets. Exposed training only; no PnL."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS, source_gate

CLOCK = tuple(range(743, HOURS - 1, 24))
SLOTS = ("Growth_Core", "Opportunity", "Relative_Value", "Stress_Recovery")
BOOKS = {"WP_full": (0, 1, 2, 3), "WP_core_only": (0,),
         "WP_minus_opportunity": (0, 2, 3), "WP_minus_RV": (0, 1, 3),
         "WP_minus_stress": (0, 1, 2)}

def targets(d):
    source_gate(d)
    p = np.log(np.asarray(d["c"], dtype=float))
    states = np.zeros(4, dtype=int)
    result = {}
    for t in CLOCK:
        high336 = np.max(p[t-336:t], axis=0)
        low336 = np.min(p[t-336:t], axis=0)
        high168 = np.max(p[t-168:t], axis=0)
        low168 = np.min(p[t-168:t], axis=0)
        midpoint168 = (high168 + low168) / 2.
        midpoint336 = (high336 + low336) / 2.
        for j in range(4):
            if p[t,j] > high336[j]:
                states[j] = 1
            elif p[t,j] < low336[j]:
                states[j] = -1
            elif (states[j] > 0 and p[t,j] < midpoint168[j]) or (states[j] < 0 and p[t,j] > midpoint168[j]):
                states[j] = 0
        raw = np.zeros((4,4), dtype=float)
        active = [j for j in range(4) if states[j] != 0]
        active.sort(key=lambda j: (-states[j]*(p[t,j]-midpoint336[j])/
                                   max(high336[j]-low336[j],1e-12), j))
        for j in active[:2]:
            raw[0,j] = .28 * states[j]
        r24 = p[t] - p[t-24]
        r48 = p[t] - p[t-48]
        r168 = p[t] - p[t-168]
        r336 = p[t] - p[t-336]
        vol72 = np.std(np.diff(p[t-72:t+1],axis=0),axis=0)
        vol336 = np.std(np.diff(p[t-336:t+1],axis=0),axis=0)
        hist24 = p[t-335:t+1] - p[t-359:t-23]
        std24 = np.std(hist24,axis=0)
        eligible = [j for j in range(4) if vol72[j] < .70*vol336[j] and
                    abs(r24[j]) > 2.5*max(std24[j],1e-12)]
        if eligible:
            j = min(eligible,key=lambda k:(-abs(r24[k])/max(std24[k],1e-12),k))
            raw[1,j] = .12 if r24[j]>0 else -.12
        residual = r168 - float(np.mean(r168))
        hi = min(range(4),key=lambda j:(-residual[j],j))
        lo = min(range(4),key=lambda j:(residual[j],j))
        if hi != lo and residual[hi]-residual[lo] > .10:
            raw[2,lo] = .07
            raw[2,hi] = -.07
        if float(np.mean(r48)) < -.05:
            if float(np.mean(r24)) > 0:
                j = min(range(4),key=lambda k:(-r24[k],k))
                raw[3,j] = .10
            else:
                j = min(range(4),key=lambda k:(r24[k],k))
                raw[3,j] = -.10
        regime = "negative_channel" if float(np.mean(r336))<0 else "positive_channel"
        if regime == "negative_channel":
            raw[:2] = np.where(raw[:2]>0,raw[:2]*.50,raw[:2])
        gross = float(np.abs(raw).sum())
        if gross > .70:
            raw *= .70/gross
        if not np.isfinite(raw).all() or float(np.abs(raw).sum()) > .70+1e-10:
            raise ValueError("WP_GROSS_OR_NONFINITE")
        result[t] = {"weights":raw,"regime":regime}
    return result

def books_from_decisions(dec):
    return {name:{t:np.sum(x["weights"][list(slots)],axis=0)
                  for t,x in dec.items()} for name,slots in BOOKS.items()}

def incidence(dec):
    return {slot:int(sum(np.abs(x["weights"][i]).sum()>1e-12 for x in dec.values()))
            for i,slot in enumerate(SLOTS)}

def synthetic_test():
    h=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    close=100*np.exp(.00006*h*(1+j/7)+.12*np.sin(h/110+j))
    volume=np.ones((HOURS,4))*1e6
    d={"o":close.copy(),"h":close*1.01,"l":close*.99,"c":close.copy(),
       "q":volume,"rate":np.zeros((HOURS,4)),
       "event":np.zeros((HOURS,4),bool),
       "mark_lower":close*.99,"mark_upper":close*1.01}
    d["event"][::8]=True
    d["rate"][::8]=np.array([.0001,-.0001,.00003,.00015])
    a=targets(d)
    b={k:v.copy() for k,v in d.items()}
    for key in ("o","h","l","c","mark_lower","mark_upper"):
        b[key][14000:]*=np.array([1.5,.8,1.2,1.8])
    b["q"][14000:]*=2
    b["rate"][14000:]*=2
    c=targets(b)
    for t in CLOCK:
        if t>=14000:break
        if a[t]["regime"]!=c[t]["regime"] or not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WP_FUTURE_MUTATION_LEAK")
    if len(a)!=1096 or len(books_from_decisions(a))!=5:
        raise ValueError("WP_CLOCK_OR_BOOKS")
    return {"decision":"PASS_WP_SYNTHETIC_CAUSAL_ONLY_NOT_PNL",
            "decisions":len(a),"incidence":incidence(a),
            "future_mutation_safe":True,"2026_accessed":False}

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
