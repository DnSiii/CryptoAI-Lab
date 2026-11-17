"""V98 C11 preregistered breadth/leadership seven-slot training candidate."""
import math
from .phase243_native_funding_cashflow import ASSETS
from .v98_b0_causal_overlay import compose_weights

LONG, MID, SHORT, STEP = 2160, 720, 168, 24

def composed_c11_sleeves():
    last = {a: (0., 0., 0., 0.) for a in ASSETS}
    was_stressed = False
    armed = False
    recovery_asset = None
    recovery_end = -1
    def compute(history):
        nonlocal last, was_stressed, armed, recovery_asset, recovery_end
        if set(history) != set(ASSETS):
            raise ValueError("C11_CLEAN4_ONLY")
        n = len(history[ASSETS[0]])
        if any(len(history[a]) != n for a in ASSETS):
            raise ValueError("C11_MISALIGNED")
        i = n - 1
        if i < LONG or i % STEP:
            return last
        m = {}
        for a in ASSETS:
            p = history[a]
            q = (p[i-LONG], p[i-MID], p[i-SHORT], p[i])
            if any(not math.isfinite(float(v)) or v <= 0 for v in q):
                raise ValueError("C11_INVALID_CLOSE")
            m[a] = (math.log(q[3]/q[0]), math.log(q[3]/q[1]), math.log(q[3]/q[2]))
        core = [a for a in ASSETS if m[a][0] > 0 and m[a][1] > 0]
        opp = sorted((a for a in ASSETS if m[a][1] > 0 and m[a][2] > 0),
                     key=lambda a: (-m[a][2], a))[:1]
        ordered = sorted(m[a][1] for a in ASSETS)
        median = (ordered[1]+ordered[2])/2
        rv = sorted((a for a in ASSETS if m[a][1] > median and m[a][1] > 0),
                    key=lambda a: (-m[a][1], a))[:1]
        stress = sum(m[a][1] < 0 for a in ASSETS) >= 3
        if recovery_asset is not None and i >= recovery_end:
            recovery_asset = None
        if stress and not was_stressed and recovery_asset is None:
            armed = True
        if armed and not stress and recovery_asset is None:
            if sum(m[a][2] > 0 for a in ASSETS) >= 3 and sum(m[a][1] > 0 for a in ASSETS) >= 2:
                eligible = [a for a in ASSETS if m[a][1] > 0 and m[a][2] > 0]
                if eligible:
                    recovery_asset = sorted(eligible, key=lambda a: (-m[a][2], a))[0]
                    recovery_end = i + 14*STEP
                    armed = False
        was_stressed = stress
        groups = (core, opp, rv, [recovery_asset] if recovery_asset else [])
        budgets = (.40, .16, .12, .10)
        last = {a: tuple(budgets[j]/len(groups[j]) if a in groups[j] else 0.
                         for j in range(4)) for a in ASSETS}
        return last
    return compute

def breadth_router(completed_closes):
    p = list(completed_closes)
    if len(p) < MID+1:
        return 0.
    x = (p[-MID-1], p[-SHORT-1], p[-1])
    if any(not math.isfinite(float(v)) or v <= 0 for v in x):
        raise ValueError("C11_ROUTER_INVALID_CLOSE")
    r30 = math.log(x[2]/x[0])
    r7 = math.log(x[2]/x[1])
    return 1. if r30 > 0 else (.75 if r7 > 0 else .50)

def c11_allocator(sleeves, routers, governor):
    return compose_weights(sleeves, routers, governor, gross_cap=.78, asset_cap=.42)
