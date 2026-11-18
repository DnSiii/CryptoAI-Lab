"""V98 C13: preregistered orthogonal seven-slot long-only architecture.
Research-only. No claims of PnL, validation, or production suitability.
All inputs are completed closes; execution must occur no earlier than next open.
"""
import math
from .phase243_native_funding_cashflow import ASSETS
from .v98_b0_causal_overlay import compose_weights

WARMUP = 2160
REBALANCE = 24
CHANNEL = 720
VOL_WINDOW = 168
STRESS_WINDOW = 336
BUDGETS = (0.32, 0.20, 0.12, 0.12)
GROSS_CAP = 0.76
ASSET_CAP = 0.38

def composed_c13_sleeves():
    previous = {a: (0., 0., 0., 0.) for a in ASSETS}
    recovery_end = -1
    was_stressed = False

    def compute(history):
        nonlocal previous, recovery_end, was_stressed
        if set(history) != set(ASSETS):
            raise ValueError("C13_CLEAN4_ONLY")
        n = len(history[ASSETS[0]])
        if any(len(history[a]) != n for a in ASSETS):
            raise ValueError("C13_MISALIGNED")
        i = n - 1
        if i < WARMUP or i % REBALANCE:
            return previous
        features = {}
        for a in ASSETS:
            p = history[a][i-WARMUP:i+1]
            if any(not math.isfinite(float(x)) or x <= 0 for x in p):
                raise ValueError("C13_INVALID_CLOSE")
            r = [math.log(p[k]/p[k-1]) for k in range(1,len(p))]
            vol = max(1e-8, math.sqrt(sum(x*x for x in r[-VOL_WINDOW:])/VOL_WINDOW))
            channel = p[-CHANNEL-1:-1]
            high, low = max(channel), min(channel)
            medium = math.log(p[-1]/p[-STRESS_WINDOW-1])
            short = math.log(p[-1]/p[-VOL_WINDOW-1])
            features[a] = (p[-1], high, low, vol, medium, short)
        # Growth: confirmed 30-day channel breakout, not C12 dual momentum.
        growth = [a for a in ASSETS if features[a][0] > features[a][1]]
        # Opportunity: positive 7-day reversal after a 14-day drawdown,
        # conditional on price remaining above the 30-day channel midpoint.
        opportunity = [a for a in ASSETS
                       if features[a][4] < 0 and features[a][5] > 0
                       and features[a][0] > (features[a][1]+features[a][2])/2]
        # Relative value: top cross-sectional 14-day leader only when
        # its excess return vs equal-weight Clean-4 is positive.
        mean_medium = sum(features[a][4] for a in ASSETS)/len(ASSETS)
        leader = sorted(ASSETS, key=lambda a: (-features[a][4], a))[0]
        relative = [leader] if features[leader][4] > mean_medium and features[leader][4] > 0 else []
        # Stress/recovery: broad market drawdown followed by positive breadth.
        stressed = sum(features[a][4] < 0 for a in ASSETS) >= 3
        if was_stressed and not stressed:
            recovery_end = i + 5*REBALANCE
        if stressed:
            recovery_end = -1
        was_stressed = stressed
        recovery = ([a for a in ASSETS if features[a][5] > 0]
                    if i < recovery_end else [])
        weights = {a: [0.]*4 for a in ASSETS}
        for j, group in enumerate((growth, opportunity, relative, recovery)):
            if not group:
                continue
            inv = {a: 1/features[a][3] for a in group}
            total = sum(inv.values())
            for a in group:
                weights[a][j] = BUDGETS[j]*inv[a]/total
        previous = {a: tuple(weights[a]) for a in ASSETS}
        return previous
    return compute

def c13_router(closes):
    p = list(closes)
    if len(p) < CHANNEL+1:
        return 0.
    q = p[-CHANNEL-1:]
    if any(not math.isfinite(float(x)) or x <= 0 for x in q):
        raise ValueError("C13_INVALID_ROUTER_CLOSE")
    # Independent price-location regime gate; no future information.
    low, high = min(q[:-1]), max(q[:-1])
    if high <= low:
        return 0.
    position = (q[-1]-low)/(high-low)
    return 1. if position >= .65 else (.5 if position >= .35 else .2)

def c13_allocator(sleeves, routers, governor):
    return compose_weights(sleeves, routers, governor,
                           gross_cap=GROSS_CAP, asset_cap=ASSET_CAP)
