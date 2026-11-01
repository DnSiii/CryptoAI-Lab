#!/usr/bin/env python3
"""Independent PH scalar feature, signal and allocator oracle.
No import of PH primary implementation, other engines or future/holdout data.
"""
import math
import numpy as np

CLOCK = tuple(range(744, 27048, 168))
BOOKS = {
    "PH_full": (0, 1, 2, 3),
    "PH_core_only": (0,),
    "PH_minus_opportunity": (0, 2, 3),
    "PH_minus_RV": (0, 1, 3),
    "PH_minus_stress": (0, 1, 2),
}
ORDER = {
    "unwind": (3, 1, 2),
    "crowded": (2, 1, 3),
    "balanced": (1, 2, 3),
    "unknown": (1, 2, 3),
}


def independent_decisions(d, oi, observed, primary, targets):
    close = np.asarray(d["c"], float)
    rates = np.asarray(d["rate"], float)
    events = np.asarray(d["event"], bool)
    mismatches = 0
    maximum = 0.
    missing = 0
    active = {1: 0, 2: 0, 3: 0}
    for t in CLOCK:
        r504 = np.log(close[t] / close[t-504])
        r168 = np.log(close[t] / close[t-168])
        r72 = np.log(close[t] / close[t-72])
        r24 = np.log(close[t] / close[t-24])
        hourly = np.log(close[t-503:t+1] / close[t-504:t])
        sigma = np.std(hourly, axis=0)*np.sqrt(504)
        quality = r504 / np.maximum(0.03, sigma)
        raw = np.zeros((4, 4))
        positive = int(sum(r504 > 0))
        if r504[0] > 0 and positive >= 2:
            ranked = [i for i in range(4) if r168[i] > 0]
            ranked.sort(key=lambda i: (-quality[i], i))
            for i, w in zip(ranked[:2], (0.38, 0.20)):
                raw[0, i] = w
        elif r504[0] < 0 and positive <= 1:
            ranked = [i for i in range(4) if r168[i] < 0]
            ranked.sort(key=lambda i: (quality[i], i))
            for i, w in zip(ranked[:2], (-0.34, -0.18)):
                raw[0, i] = w
        eligible = all(bool(observed[z, i]) for z in range(t-167, t+1)
                       for i in range(4))
        mode = "unknown"
        features = None
        if eligible:
            oi72 = np.log(oi[t] / oi[t-72])
            oi168 = np.log(oi[t] / oi[t-167])
            funding = np.zeros(4)
            for z in range(t-167, t+1):
                for i in range(4):
                    if events[z, i]:
                        funding[i] += rates[z, i]
            candidates = []
            for i in range(4):
                if oi72[i] >= -0.05:
                    continue
                if funding[i] < 0 and r72[i] < 0 and r24[i] > 0:
                    candidates.append((-abs(float(oi72[i])), i, 0.22))
                elif funding[i] > 0 and r72[i] > 0 and r24[i] < 0:
                    candidates.append((-abs(float(oi72[i])), i, -0.22))
            if candidates:
                _, i, signed = sorted(candidates)[0]
                raw[1, i] = signed
            hi = sorted(range(4), key=lambda i: (-funding[i], i))[0]
            lo = sorted(range(4), key=lambda i: (funding[i], i))[0]
            if (hi != lo and funding[hi]-funding[lo] > 0.0012
                    and oi168[hi] > 0.02 and oi168[lo] > -0.02
                    and abs(r168[hi]-r168[lo]) < 0.12):
                raw[2, hi] = -0.15
                raw[2, lo] = 0.15
            unwind = int(sum(oi72 < -0.04)) >= 3
            if unwind and r24[0] < -0.04:
                raw[3, 0] = -0.20
            elif unwind and r72[0] < -0.08 and r24[0] > 0.02:
                raw[3, 0] = 0.20
            mode = ("unwind" if unwind else
                    "crowded" if int(sum(oi168 > 0.03)) >= 3
                    else "balanced")
            features = (oi72, oi168, funding)
        else:
            missing += 1
        for slot in (1, 2, 3):
            if np.any(raw[slot]):
                active[slot] += 1
        expected, actual_mode, actual_eligible, actual_features = primary[t]
        err = float(np.max(np.abs(raw-expected)))
        maximum = max(maximum, err)
        if (err > 1e-10 or mode != actual_mode or eligible != actual_eligible
                or (features is None) != (actual_features is None)):
            mismatches += 1
        elif features is not None:
            for left, right in zip(features, actual_features):
                err = float(np.max(np.abs(left-right)))
                maximum = max(maximum, err)
                if err > 1e-10:
                    mismatches += 1
        history = np.log(close[t-167:t+1] / close[t-168:t])
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
                    ca = candidate-candidate.mean()
                    cb = existing-existing.mean()
                    corr = float(np.dot(ca, cb) /
                                 np.sqrt(np.dot(ca, ca)*np.dot(cb, cb)))
                else:
                    corr = 0.
                take = min(room, gross*(0.5 if corr > 0.35 else 1.))
                rebuilt[slot] = raw[slot]*(take/gross)
                room -= take
            err = float(np.max(np.abs(rebuilt-targets[book][t])))
            maximum = max(maximum, err)
            if err > 1e-10:
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
