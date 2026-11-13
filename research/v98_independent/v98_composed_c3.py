"""V98 C3 preregistered seven-slot slow-trend candidate, training only.

Protocol: v98_c3_architecture_prereg_20261113.md
The existing causal replay supplies router, allocator and governor.
"""
import math
from .phase243_native_funding_cashflow import ASSETS

LOOKBACK = 1344
MID = 672
FAST = 336
STEP = 168

def composed_c3_sleeves():
    last = {a: (0., 0., 0., 0.) for a in ASSETS}
    def compute(history):
        nonlocal last
        if set(history) != set(ASSETS):
            raise ValueError("C3_CLEAN4_ONLY")
        n = len(history[ASSETS[0]])
        if any(len(history[a]) != n for a in ASSETS):
            raise ValueError("C3_MISALIGNED")
        i = n - 1
        if i < LOOKBACK or i % STEP:
            return last
        metrics = {}
        for a in ASSETS:
            p = history[a][i - LOOKBACK:i + 1]
            if len(p) != LOOKBACK + 1 or any(not math.isfinite(float(x)) or x <= 0 for x in p):
                raise ValueError("C3_INVALID_CLOSE")
            slow = math.log(p[-1] / p[0])
            mid = math.log(p[-1] / p[-MID-1])
            fast = math.log(p[-1] / p[-FAST-1])
            # Breakout against the 28 days preceding the latest 14-day window.
            breakout = p[-1] > max(p[-(MID+FAST+1):-(FAST+1)])
            metrics[a] = (slow, mid, fast, breakout)
        core = sorted((a for a in ASSETS if metrics[a][0] > 0 and metrics[a][1] > 0),
                      key=lambda a: (-metrics[a][0], a))[:2]
        opportunity = sorted((a for a in ASSETS if metrics[a][3] and metrics[a][2] > 0),
                             key=lambda a: (-metrics[a][2], a))[:1]
        sorted_slow = sorted(metrics[a][0] for a in ASSETS)
        median = (sorted_slow[1] + sorted_slow[2]) / 2
        rv = sorted((a for a in ASSETS if metrics[a][0] > max(0., median)),
                    key=lambda a: (-metrics[a][0], a))[:1]
        stressed = sum(metrics[a][1] < 0 for a in ASSETS) >= 3
        recovery = (sorted((a for a in ASSETS if metrics[a][1] < 0 and metrics[a][2] > 0),
                           key=lambda a: (-metrics[a][2], a))[:1] if stressed else [])
        last = {a: (0.42 / len(core) if a in core else 0.,
                    0.12 if a in opportunity else 0.,
                    0.12 if a in rv else 0.,
                    0.09 if a in recovery else 0.) for a in ASSETS}
        return last
    return compute
