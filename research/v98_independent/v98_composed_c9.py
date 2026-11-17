"""V98 C9 preregistered dispersion/recovery composed sleeves. TRAINING ONLY.

See v98_c9_dispersion_recovery_prereg_20261117.md before running any replay.
"""
import math
from .phase243_native_funding_cashflow import ASSETS

LONG = 2160
MID = 720
SHORT = 168
STEP = 24
RECOVERY_DECISIONS = 14


def composed_c9_sleeves():
    last = {a: (0., 0., 0., 0.) for a in ASSETS}
    was_stressed = False
    armed = False
    recovery_asset = None
    recovery_end = -1

    def compute(history):
        nonlocal last, was_stressed, armed, recovery_asset, recovery_end
        if set(history) != set(ASSETS):
            raise ValueError("C9_CLEAN4_ONLY")
        n = len(history[ASSETS[0]])
        if any(len(history[a]) != n for a in ASSETS):
            raise ValueError("C9_MISALIGNED")
        i = n - 1
        if i < LONG or i % STEP:
            return last
        metrics = {}
        for a in ASSETS:
            p = history[a][i-LONG:i+1]
            if len(p) != LONG+1 or any(not math.isfinite(float(v)) or v <= 0 for v in p):
                raise ValueError("C9_INVALID_CLOSE")
            r90 = math.log(p[-1]/p[0])
            r30 = math.log(p[-1]/p[-MID-1])
            r7 = math.log(p[-1]/p[-SHORT-1])
            high30 = max(p[-MID-1:-1])
            midpoint30 = math.sqrt(min(p[-MID-1:])*max(p[-MID-1:]))
            metrics[a] = (r90, r30, r7, p[-1] > high30, p[-1] > midpoint30)
        core = [a for a in ASSETS if all(metrics[a][k] > 0 for k in (0,1,2))]
        breakout = [a for a in ASSETS if metrics[a][2] > 0 and metrics[a][3]]
        opportunity = sorted(breakout, key=lambda a: (-metrics[a][2], a))[:1]
        positive30 = sum(metrics[a][1] > 0 for a in ASSETS)
        mean30 = sum(metrics[a][1] for a in ASSETS)/len(ASSETS)
        residual = [a for a in ASSETS if metrics[a][1] > 0 and metrics[a][1] > mean30]
        rv = (sorted(residual, key=lambda a: (-(metrics[a][1]-mean30), a))[:1]
              if positive30 >= 3 else [])
        stress = sum(metrics[a][1] < 0 for a in ASSETS) >= 3
        if recovery_asset is not None and i >= recovery_end:
            recovery_asset = None
        if stress and not was_stressed and recovery_asset is None:
            armed = True
        if armed and not stress and recovery_asset is None:
            if sum(metrics[a][2] > 0 for a in ASSETS) >= 3:
                eligible = [a for a in ASSETS if metrics[a][4] and metrics[a][2] > 0]
                if eligible:
                    recovery_asset = sorted(eligible, key=lambda a: (-metrics[a][2], a))[0]
                    recovery_end = i + RECOVERY_DECISIONS*STEP
                    armed = False
        was_stressed = stress
        recovery = [recovery_asset] if recovery_asset is not None else []
        last = {a: (0.40/len(core) if a in core else 0.,
                    0.15 if a in opportunity else 0.,
                    0.10 if a in rv else 0.,
                    0.10 if a in recovery else 0.) for a in ASSETS}
        return last

    return compute
