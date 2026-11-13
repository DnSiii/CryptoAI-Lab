"""V98 C4 preregistered breadth / volatility-normalized seven-slot sleeves.
See v98_c4_architecture_prereg_20261113.md. Training only.
"""
import math
from .phase243_native_funding_cashflow import ASSETS

LONG = 2160
MID = 720
SHORT = 168
STEP = 24

def composed_c4_sleeves():
    last = {a: (0., 0., 0., 0.) for a in ASSETS}

    def compute(history):
        nonlocal last
        if set(history) != set(ASSETS):
            raise ValueError("C4_CLEAN4_ONLY")
        n = len(history[ASSETS[0]])
        if any(len(history[a]) != n for a in ASSETS):
            raise ValueError("C4_MISALIGNED")
        i = n - 1
        if i < LONG or i % STEP:
            return last
        metrics = {}
        for a in ASSETS:
            p = history[a][i-LONG:i+1]
            if len(p) != LONG + 1 or any(not math.isfinite(float(v)) or v <= 0 for v in p):
                raise ValueError("C4_INVALID_CLOSE")
            r90 = math.log(p[-1] / p[0])
            r30 = math.log(p[-1] / p[-MID-1])
            r7 = math.log(p[-1] / p[-SHORT-1])
            hourly = [math.log(p[k] / p[k-1]) for k in range(len(p)-MID, len(p))]
            mean = sum(hourly)/MID
            sd = math.sqrt(sum((x-mean)**2 for x in hourly)/(MID-1))
            metrics[a] = (r90, r30, r7, sd)
        market = sum(metrics[a][1] for a in ASSETS)/len(ASSETS)
        core = [a for a in ASSETS if metrics[a][0] > 0 and metrics[a][1] > 0
                and metrics[a][1] > 2*metrics[a][3]*math.sqrt(MID)]
        opportunity = []
        if market > 0:
            eligible = [a for a in ASSETS if metrics[a][2] > 0
                        and metrics[a][2] > metrics[a][1]/4]
            opportunity = sorted(eligible, key=lambda a: (-metrics[a][2], a))[:1]
        rv = [a for a in ASSETS if market > 0 and metrics[a][1] > market]
        stress = sum(metrics[a][1] < 0 for a in ASSETS) >= 2
        recovery = [a for a in ASSETS if stress and metrics[a][1] < 0 and metrics[a][2] > 0]
        last = {a: (0.45/len(core) if a in core else 0.,
                    0.10 if a in opportunity else 0.,
                    0.10/len(rv) if a in rv else 0.,
                    0.10/len(recovery) if a in recovery else 0.) for a in ASSETS}
        return last
    return compute
