#!/usr/bin/env python3
"""WO independent asynchronous multi-timescale seven-slot strategy; no market PnL here."""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS, source_gate

CLOCK = tuple(range(743, HOURS-1, 24))
SLOTS = ("Growth_Core", "Opportunity", "Relative_Value", "Stress_Recovery")
BOOKS = {
    "WO_full": (0,1,2,3), "WO_core_only": (0,),
    "WO_minus_opportunity": (0,2,3), "WO_minus_RV": (0,1,3),
    "WO_minus_stress": (0,1,2),
}

def targets(d):
    source_gate(d)
    p = np.log(np.asarray(d["c"], dtype=float))
    volume = np.asarray(d["q"], dtype=float)
    if p.shape != (HOURS, 4) or volume.shape != (HOURS, 4):
        raise ValueError("WO_SOURCE_SHAPE")
    if len(CLOCK) != 1096:
        raise ValueError("WO_DAILY_CLOCK")
    core = np.zeros(4)
    opportunity = np.zeros(4)
    relative = np.zeros(4)
    out = {}
    for t in CLOCK:
        r672 = p[t] - p[t-672]
        r336 = p[t] - p[t-336]
        r168 = p[t] - p[t-168]
        r24 = p[t] - p[t-24]
        if (t-743) % 672 == 0:
            core = np.zeros(4)
            ranked = sorted(range(4), key=lambda j: (-r672[j], j))
            positive = [j for j in ranked if r672[j] > 0]
            if len(positive) >= 2:
                core[positive[:2]] = .26
            elif len(positive) == 1:
                core[positive[0]] = .36
            else:
                weakest = min(range(4), key=lambda j: (r672[j], j))
                core[weakest] = -.36
        if (t-743) % 168 == 0:
            opportunity = np.zeros(4)
            relative = np.zeros(4)
            market168 = float(np.mean(r168))
            if market168 > 0:
                j = min(range(4), key=lambda k: (-r168[k], k))
                if float(np.sum(volume[t-167:t+1,j])) > float(np.sum(volume[t-335:t-167,j])):
                    opportunity[j] = +.12
            elif market168 < 0:
                j = min(range(4), key=lambda k: (r168[k], k))
                if float(np.sum(volume[t-167:t+1,j])) > float(np.sum(volume[t-335:t-167,j])):
                    opportunity[j] = -.12
            residual = r336 - float(np.mean(r336))
            hi = min(range(4), key=lambda k: (-residual[k], k))
            lo = min(range(4), key=lambda k: (residual[k], k))
            if hi != lo and residual[hi] - residual[lo] > .08:
                relative[hi] = +.08
                relative[lo] = -.08
        stress = np.zeros(4)
        market24 = float(np.mean(r24))
        market168 = float(np.mean(r168))
        if market168 < 0 and market24 < -.06:
            j = min(range(4), key=lambda k: (r24[k], k))
            stress[j] = -.12
        elif market168 < 0 and market24 > .06:
            j = min(range(4), key=lambda k: (-r24[k], k))
            stress[j] = +.12
        raw = np.vstack((core, opportunity, relative, stress)).copy()
        regime = "negative_month" if float(np.mean(r672)) < 0 else "positive_month"
        if regime == "negative_month":
            for i in (0,1,2):
                raw[i] = np.where(raw[i] > 0, raw[i] * .50, raw[i])
        gross = float(np.abs(raw).sum())
        if gross > .70:
            raw *= .70 / gross
        if not np.isfinite(raw).all() or float(np.abs(raw).sum()) > .70 + 1e-10:
            raise ValueError("WO_GROSS_OR_NONFINITE")
        out[t] = {"weights": raw, "regime": regime}
    return out

def books_from_decisions(dec):
    return {name: {t: np.sum(x["weights"][list(slots)], axis=0)
                   for t, x in dec.items()} for name, slots in BOOKS.items()}

def incidence(dec):
    return {slot: int(sum(np.abs(x["weights"][i]).sum() > 1e-12
                          for x in dec.values()))
            for i, slot in enumerate(SLOTS)}

def synthetic_test():
    h = np.arange(HOURS, dtype=float)[:,None]
    j = np.arange(4, dtype=float)[None,:]
    close = 100 * np.exp(.00004*h*(1+j/8) + .06*np.sin(h/180+j))
    vol = np.broadcast_to(1e6*(1+.3*np.sin(h/30+j)), (HOURS,4)).copy()
    d = {"o":close.copy(), "h":close*1.01, "l":close*.99, "c":close.copy(),
         "q":vol, "rate":np.zeros((HOURS,4)), "event":np.zeros((HOURS,4),bool),
         "mark_lower":close*.99, "mark_upper":close*1.01}
    d["event"][::8] = True
    d["rate"][::8] = [.0001,-.00005,.00002,.0002]
    a = targets(d)
    b = {k:v.copy() for k,v in d.items()}
    for key in ("o","h","l","c","mark_lower","mark_upper"):
        b[key][14000:] *= np.array([1.5,.8,1.2,1.8])
    b["q"][14000:] *= 2
    b["rate"][14000:] *= 2
    c = targets(b)
    for t in CLOCK:
        if t >= 14000:
            break
        if a[t]["regime"] != c[t]["regime"] or not np.array_equal(a[t]["weights"],c[t]["weights"]):
            raise ValueError("WO_FUTURE_MUTATION_LEAK")
    if len(a) != 1096 or len(books_from_decisions(a)) != 5:
        raise ValueError("WO_BOOKS")
    return {"decision":"PASS_WO_SYNTHETIC_CAUSAL_NOT_PNL",
            "decisions":len(a), "incidence":incidence(a),
            "future_mutation_safe":True, "2026_accessed":False}

if __name__ == "__main__":
    print(json.dumps(synthetic_test(), sort_keys=True))
