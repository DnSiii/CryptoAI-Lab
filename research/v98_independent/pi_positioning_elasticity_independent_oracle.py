#!/usr/bin/env python3
"""Independent PI scalar decisions and allocator oracle.
Never imports the PI primary strategy, executor, other engines or holdout.
"""
import math
import numpy as np

CLOCK = tuple(range(744, 27048, 168))
BOOKS = {
    "PI_full": (0, 1, 2, 3),
    "PI_core_only": (0,),
    "PI_minus_opportunity": (0, 2, 3),
    "PI_minus_RV": (0, 1, 3),
    "PI_minus_stress": (0, 1, 2),
}
ORDER = {
    "expansion": (1, 2, 3),
    "contraction": (3, 2, 1),
    "neutral": (2, 1, 3),
    "unknown": (2, 1, 3),
}


def independent_decisions(d, oi, observed, primary, targets):
    c = np.asarray(d["c"], float)
    oi = np.asarray(oi, float)
    observed = np.asarray(observed, bool)
    mismatches = 0
    max_error = 0.
    missing = 0
    active = {1: 0, 2: 0, 3: 0}
    for t in CLOCK:
        r504 = np.array([math.log(c[t, j]/c[t-504, j]) for j in range(4)])
        r168 = np.array([math.log(c[t, j]/c[t-168, j]) for j in range(4)])
        r72 = np.array([math.log(c[t, j]/c[t-72, j]) for j in range(4)])
        r24 = np.array([math.log(c[t, j]/c[t-24, j]) for j in range(4)])
        sigma = np.array([
            np.std([math.log(c[k, j]/c[k-1, j]) for k in range(t-503, t+1)])
            * math.sqrt(504) for j in range(4)
        ])
        quality = (r504+0.5*r168)/np.maximum(sigma, 0.03)
        raw = np.zeros((4, 4))
        npositive = sum(x > 0 for x in r504)
        if r504[0] > 0 and npositive >= 2:
            ranking = sorted((j for j in range(4) if r168[j] > 0),
                             key=lambda j: (-quality[j], j))
            for j, w in zip(ranking[:2], (0.38, 0.20)):
                raw[0, j] = w
        elif r504[0] < 0 and npositive <= 1:
            ranking = sorted((j for j in range(4) if r168[j] < 0),
                             key=lambda j: (quality[j], j))
            for j, w in zip(ranking[:2], (-0.34, -0.18)):
                raw[0, j] = w
        btc = [math.log(c[k, 0]/c[k-1, 0]) for k in range(t-167, t+1)]
        v168 = float(np.std(btc))
        v24 = float(np.std(btc[-24:]))
        if v168 > 1e-12 and v24/v168 > 1.8:
            if r24[0] < -0.05 and r168[0] < 0:
                raw[3, 0] = -0.18
            elif r24[0] > 0.05 and r72[0] < 0:
                raw[3, 0] = 0.18
        eligible = all(observed[k, j] for k in range(t-167, t+1) for j in range(4))
        mode = "unknown"
        features = None
        if eligible:
            o72 = np.array([math.log(oi[t, j]/oi[t-72, j]) for j in range(4)])
            o168 = np.array([math.log(oi[t, j]/oi[t-167, j]) for j in range(4)])
            candidates = []
            for j in range(4):
                if o72[j] <= 0.06:
                    continue
                if r72[j] > 0.06 and r24[j] > 0.01:
                    candidates.append((-abs(r72[j]), j, 0.22))
                elif r72[j] < -0.06 and r24[j] < -0.01:
                    candidates.append((-abs(r72[j]), j, -0.22))
            if candidates:
                _, j, w = sorted(candidates)[0]
                raw[1, j] = w
            score = r168-0.5*o168
            high = sorted(range(4), key=lambda j: (-score[j], j))[0]
            low = sorted(range(4), key=lambda j: (score[j], j))[0]
            if (high != low and score[high]-score[low] > 0.15
                    and r72[high] > 0 and r72[low] < 0
                    and abs(o168[high]-o168[low]) < 0.25):
                raw[2, high] = 0.14
                raw[2, low] = -0.14
            mode = ("expansion" if sum(o168 > 0.025) >= 3 else
                    "contraction" if sum(o168 < -0.025) >= 3 else "neutral")
            features = (o72, o168, score)
        else:
            missing += 1
        for slot in (1, 2, 3):
            if np.any(raw[slot]):
                active[slot] += 1
        got_raw, got_mode, got_eligible, got_features = primary[t]
        error = float(np.max(np.abs(raw-got_raw)))
        max_error = max(max_error, error)
        if (error > 1e-10 or mode != got_mode or eligible != got_eligible
                or (features is None) != (got_features is None)):
            mismatches += 1
        elif features is not None:
            for x, y in zip(features, got_features):
                error = float(np.max(np.abs(x-y)))
                max_error = max(max_error, error)
                if error > 1e-10:
                    mismatches += 1
        history = np.array([[math.log(c[k, j]/c[k-1, j]) for j in range(4)]
                            for k in range(t-167, t+1)])
        for book, allowed in BOOKS.items():
            rebuilt = np.zeros((4, 4))
            if 0 in allowed:
                rebuilt[0] = raw[0]
            room = min(0.32, max(0., 0.84-float(np.abs(rebuilt[0]).sum())))
            for slot in ORDER[mode]:
                if slot not in allowed or room <= 1e-12:
                    continue
                gross = float(np.abs(raw[slot]).sum())
                if gross <= 1e-12:
                    continue
                candidate = history @ raw[slot]
                existing = history @ rebuilt.sum(axis=0)
                if np.std(candidate) > 1e-12 and np.std(existing) > 1e-12:
                    x = candidate-candidate.mean()
                    y = existing-existing.mean()
                    corr = float(np.dot(x, y)/math.sqrt(np.dot(x, x)*np.dot(y, y)))
                else:
                    corr = 0.
                take = min(room, gross*(0.5 if corr > 0.35 else 1.))
                rebuilt[slot] = raw[slot]*(take/gross)
                room -= take
            error = float(np.max(np.abs(rebuilt-targets[book][t])))
            max_error = max(max_error, error)
            if error > 1e-10:
                mismatches += 1
    return {
        "decisions": len(CLOCK), "books": len(BOOKS),
        "oi_ineligible_decisions": missing,
        "raw_optional_active_decisions": active,
        "mismatches": mismatches, "max_weight_or_feature_error": max_error,
        "independent_implementation": True,
        "source_future_accessed": False, "2025_exposed_training_only": True,
    }
