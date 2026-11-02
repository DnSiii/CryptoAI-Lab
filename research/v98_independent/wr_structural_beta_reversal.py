#!/usr/bin/env python3
"""WR: preregistered weekly structural-beta / cross-sectional reversal seven-slot targets.

Only exposed training; no economic PnL in this module. Never read benchmark engines.
"""
from __future__ import annotations
import json
import numpy as np
from vy_cross_sectional_spread import HOURS, source_gate

CLOCK = tuple(range(743, HOURS - 1, 168))
SLOTS = ("Growth_Core", "Opportunity", "Relative_Value", "Stress_Recovery")
BOOKS = {
    "WR_full": (0, 1, 2, 3),
    "WR_core_only": (0,),
    "WR_minus_opportunity": (0, 2, 3),
    "WR_minus_RV": (0, 1, 3),
    "WR_minus_stress": (0, 1, 2),
}

def targets(d):
    source_gate(d)
    p = np.log(np.asarray(d["c"], dtype=float))
    result = {}
    for t in CLOCK:
        r672 = p[t] - p[t - 672]
        r168 = p[t] - p[t - 168]
        realized = np.std(np.diff(p[t-672:t+1], axis=0), axis=0)
        score = r672 / np.maximum(realized, 1e-9)
        raw = np.zeros((4, 4), dtype=float)

        eligible = [j for j in range(4) if r672[j] > 0]
        eligible.sort(key=lambda j: (-score[j], j))
        for j in eligible[:2]:
            raw[0, j] = .24

        pullbacks = [j for j in range(4) if r672[j] > 0 and r168[j] < 0]
        if pullbacks:
            j = min(pullbacks, key=lambda k: (r168[k], k))
            raw[1, j] = .10

        # Historical 168h cross-asset dispersion, evaluated only on already closed bars.
        # At the first weekly decision the 744h warmup truncates the earliest samples.
        past = np.arange(max(168, t-672), t, 24)
        historical_dispersion = np.array([
            np.std(p[u] - p[u-168]) for u in past
        ], dtype=float)
        current_dispersion = float(np.std(r168))
        if current_dispersion > float(np.median(historical_dispersion)):
            weak = min(range(4), key=lambda j: (r168[j], j))
            strong = min(range(4), key=lambda j: (-r168[j], j))
            if weak != strong:
                raw[2, weak] = .06
                raw[2, strong] = -.06

        market168 = float(np.mean(r168))
        market672 = float(np.mean(r672))
        if market672 < 0 and market168 < 0:
            j = min(range(4), key=lambda k: (r168[k], k))
            raw[3, j] = -.12
        elif market672 < 0 and market168 > 0:
            j = min(range(4), key=lambda k: (-r168[k], k))
            raw[3, j] = +.12

        breadth = int(np.sum(r672 > 0))
        regime = "negative_breadth" if breadth < 2 else "positive_breadth"
        if breadth < 2:
            raw[:2] = np.where(raw[:2] > 0, raw[:2] * .5, raw[:2])
        gross = float(np.abs(raw).sum())
        if gross > .70:
            raw *= .70 / gross
        if not np.isfinite(raw).all() or np.abs(raw).sum() > .70 + 1e-10:
            raise ValueError("WR_NONFINITE_OR_GROSS")
        result[t] = {"weights": raw, "regime": regime}
    return result

def books_from_decisions(dec):
    return {
        name: {t: np.sum(x["weights"][list(slots)], axis=0)
               for t, x in dec.items()}
        for name, slots in BOOKS.items()
    }

def incidence(dec):
    return {
        slot: int(sum(np.abs(x["weights"][i]).sum() > 1e-12
                      for x in dec.values()))
        for i, slot in enumerate(SLOTS)
    }

def synthetic_test():
    h = np.arange(HOURS, dtype=float)[:, None]
    j = np.arange(4, dtype=float)[None, :]
    close = 100 * np.exp(.000035 * h * (1 + j / 8) + .13 * np.sin(h / 120 + j))
    volume = np.broadcast_to(1e6 * (1 + .2 * np.sin(h / 35 + j)),
                             (HOURS, 4)).copy()
    d = {"o": close.copy(), "h": close * 1.01, "l": close * .99,
         "c": close.copy(), "q": volume,
         "rate": np.zeros((HOURS, 4)),
         "event": np.zeros((HOURS, 4), dtype=bool),
         "mark_lower": close * .99, "mark_upper": close * 1.01}
    d["event"][::8] = True
    d["rate"][::8] = np.array([-.0001, .0002, -.00008, .00015])
    a = targets(d)
    b = {k: v.copy() for k, v in d.items()}
    for key in ("o", "h", "l", "c", "mark_lower", "mark_upper"):
        b[key][14000:] *= np.array([1.5, .8, 1.2, 1.8])
    b["q"][14000:] *= 2
    b["rate"][14000:] *= 2
    c = targets(b)
    for t in CLOCK:
        if t >= 14000:
            break
        if a[t]["regime"] != c[t]["regime"] or not np.array_equal(
                a[t]["weights"], c[t]["weights"]):
            raise ValueError("WR_FUTURE_MUTATION_LEAK")
    if len(a) != 157 or len(books_from_decisions(a)) != 5:
        raise ValueError("WR_CLOCK_OR_BOOKS")
    return {"decision": "PASS_WR_SYNTHETIC_CAUSAL_ONLY_NOT_PNL",
            "decisions": len(a), "incidence": incidence(a),
            "future_mutation_safe": True, "2026_accessed": False}

if __name__ == "__main__":
    print(json.dumps(synthetic_test(), sort_keys=True))
