"""V98 C1 composed portfolio: predeclared causal breadth allocator, research only.

Four alpha sleeves, cross-sectional regime router (existing), dynamic allocator,
and drawdown governor (existing). This is a new hypothesis, not a B0 rescue.
No 2026 data, holdout, benchmarks, optimization, or promotion.
"""
import math
from .phase243_native_funding_cashflow import ASSETS

LONG = 720
SHORT = 168
RECOVERY = 336
REBALANCE = 168

def composed_c1_sleeves():
    last = {a: (0., 0., 0., 0.) for a in ASSETS}
    def compute(history):
        nonlocal last
        if set(history) != set(ASSETS):
            raise ValueError("C1_CLEAN4_ONLY")
        length = len(history[ASSETS[0]])
        if any(len(history[a]) != length for a in ASSETS):
            raise ValueError("C1_MISALIGNED_HISTORY")
        i = length - 1
        if i < LONG or i % REBALANCE:
            return last
        for a in ASSETS:
            segment = history[a][i-LONG:i+1]
            if any(not math.isfinite(float(v)) or v <= 0 for v in segment):
                raise ValueError("C1_INVALID_COMPLETED_CLOSE")
        long_ret = {a: history[a][i]/history[a][i-LONG]-1 for a in ASSETS}
        short_ret = {a: history[a][i]/history[a][i-SHORT]-1 for a in ASSETS}
        breadth = sum(long_ret[a] > 0 for a in ASSETS)
        # Fixed a priori: breadth determines the allocation between the
        # directional core and diversifying opportunity/relative/recovery.
        core_budget = (0.50 if breadth >= 3 else 0.30 if breadth >= 1 else 0.)
        opp_budget = (0.15 if breadth >= 2 else 0.08)
        rv_budget = 0.12
        stress_budget = 0.08
        growth = sorted((a for a in ASSETS if long_ret[a] > 0),
                        key=lambda a: (-long_ret[a], a))[:2]
        breakout = [a for a in ASSETS if short_ret[a] > 0
                    and history[a][i] >= max(history[a][i-SHORT:i+1])]
        opportunity = sorted(breakout, key=lambda a: (-short_ret[a], a))[:1]
        pullbacks = [a for a in ASSETS if long_ret[a] > 0 and short_ret[a] < 0]
        relative = sorted(pullbacks, key=lambda a: (short_ret[a], a))[:1]
        recovering = [a for a in ASSETS if long_ret[a] > 0 and
                      -0.25 < history[a][i]/max(history[a][i-RECOVERY:i+1])-1 < -0.10]
        recovery = sorted(recovering, key=lambda a: (-long_ret[a], a))[:1]
        last = {a: (
            core_budget/len(growth) if a in growth else 0.,
            opp_budget if a in opportunity else 0.,
            rv_budget if a in relative else 0.,
            stress_budget if a in recovery else 0.
        ) for a in ASSETS}
        return last
    return compute
