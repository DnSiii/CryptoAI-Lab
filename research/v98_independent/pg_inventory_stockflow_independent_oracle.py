#!/usr/bin/env python3
"""V98 PG independent scalar feature, seven-slot and allocation oracle.
No imports from PG primary engine. No benchmark, holdout, future or paper access.
"""
import math
import numpy as np

CLOCK = tuple(range(744, 27048, 168))
BOOKS = {
    "PG_full": (0, 1, 2, 3),
    "PG_core_only": (0,),
    "PG_minus_opportunity": (0, 2, 3),
    "PG_minus_RV": (0, 1, 3),
    "PG_minus_stress": (0, 1, 2),
}
ORDER = {
    "accumulation": (1, 2, 3),
    "liquidation": (3, 2, 1),
    "mixed": (2, 1, 3),
    "unknown": (1, 2, 3),
}


def independent_decisions(d, oi, observed, primary, targets):
    close = np.asarray(d["c"], float)
    volume = np.asarray(d["q"], float)
    mismatches = 0
    maximum = 0.0
    missing = 0
    active = {1: 0, 2: 0, 3: 0}
    for t in CLOCK:
        ret672 = np.log(close[t] / close[t-672])
        ret168 = np.log(close[t] / close[t-168])
        ret72 = np.log(close[t] / close[t-72])
        ret24 = np.log(close[t] / close[t-24])
        hret = np.log(close[t-335:t+1] / close[t-336:t])
        vol336 = np.std(hret, axis=0) * np.sqrt(336)
        quality = (ret672 + ret168) / np.maximum(.02, vol336)
        raw = np.zeros((4, 4))
        if ret672[0] > 0:
            indices = [i for i in range(4) if ret168[i] > 0]
            indices.sort(key=lambda i: (-quality[i], i))
            for i, w in zip(indices[:2], (.36, .20)):
                raw[0, i] = w
        elif ret672[0] < 0:
            indices = [i for i in range(4) if ret168[i] < 0]
            indices.sort(key=lambda i: (quality[i], i))
            for i, w in zip(indices[:2], (-.34, -.18)):
                raw[0, i] = w
        eligible = all(bool(observed[z, i]) for z in range(t-167, t+1) for i in range(4))
        sf = None
        mode = "unknown"
        if eligible:
            recent_vol = volume[t-167:t+1].sum(axis=0)
            previous_vol = volume[t-335:t-167].sum(axis=0)
            if min(recent_vol) <= 0 or min(previous_vol) <= 0:
                eligible = False
            else:
                sf = np.log(oi[t] / oi[t-167]) - np.log(recent_vol / previous_vol)
                candidates = [i for i in range(4) if abs(ret72[i]) < .04 and sf[i] > .12]
                if candidates:
                    i = min(candidates, key=lambda z: (-sf[z], z))
                    raw[1, i] = .20
                high = min(range(4), key=lambda z: (-sf[z], z))
                low = min(range(4), key=lambda z: (sf[z], z))
                if sf[high] - sf[low] > .20 and abs(ret168[high] - ret168[low]) < .06:
                    raw[2, high] = .12
                    raw[2, low] = -.12
                btc_recent = np.log(close[t-71:t+1, 0] / close[t-72:t, 0])
                btc_prior = np.log(close[t-335:t-71, 0] / close[t-336:t-72, 0])
                if sum(sf < -.10) >= 3 and np.var(btc_recent) > 1.3 * np.var(btc_prior):
                    raw[3, 0] = -.18
                elif sum(sf > .10) >= 3 and ret72[0] < 0 and ret24[0] > 0:
                    raw[3, 0] = .18
                mode = ("accumulation" if sum(sf > 0) >= 3 else
                        "liquidation" if sum(sf < 0) >= 3 else "mixed")
        if not eligible:
            raw[1:] = 0
            sf = None
            mode = "unknown"
            missing += 1
        for i in (1, 2, 3):
            if np.any(raw[i]):
                active[i] += 1
        expected, actual_mode, actual_eligible, actual_sf = primary[t]
        err = float(np.max(np.abs(expected - raw)))
        maximum = max(maximum, err)
        if (err > 1e-10 or actual_mode != mode or actual_eligible != eligible
                or (sf is None) != (actual_sf is None)):
            mismatches += 1
        elif sf is not None:
            delta = float(np.max(np.abs(sf - actual_sf)))
            maximum = max(maximum, delta)
            if delta > 1e-10:
                mismatches += 1
        history = np.log(close[t-167:t+1] / close[t-168:t])
        for book, allowed in BOOKS.items():
            rebuilt = np.zeros((4, 4))
            if 0 in allowed:
                rebuilt[0] = raw[0]
            remaining = min(.30, max(0., .84 - float(np.abs(rebuilt[0]).sum())))
            for sleeve in ORDER[mode]:
                if sleeve not in allowed or remaining <= 1e-12:
                    continue
                gross = float(np.abs(raw[sleeve]).sum())
                if gross <= 1e-12:
                    continue
                a = history @ raw[sleeve]
                b = history @ rebuilt.sum(axis=0)
                if np.std(a) > 1e-12 and np.std(b) > 1e-12:
                    centered_a = a - a.mean()
                    centered_b = b - b.mean()
                    corr = float(np.dot(centered_a, centered_b) /
                                 np.sqrt(np.dot(centered_a, centered_a) *
                                         np.dot(centered_b, centered_b)))
                else:
                    corr = 0.0
                desired = gross * (.5 if corr > .5 else 1.)
                used = min(remaining, desired)
                rebuilt[sleeve] = raw[sleeve] * (used / gross)
                remaining -= used
            delta = float(np.max(np.abs(rebuilt - targets[book][t])))
            maximum = max(maximum, delta)
            if delta > 1e-10:
                mismatches += 1
    return {
        "decisions": len(CLOCK),
        "books": len(BOOKS),
        "oi_ineligible_decisions": missing,
        "raw_optional_active_decisions": active,
        "mismatches": mismatches,
        "max_weight_or_feature_error": maximum,
        "independent_implementation": True,
        "source_future_accessed": False,
        "2025_exposed_training_only": True,
    }
