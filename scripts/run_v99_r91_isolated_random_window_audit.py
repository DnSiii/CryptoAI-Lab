from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r88_selective_exposure_expansion as r88

r36 = r88.r36
REPORT = PROJECT / "reports" / "v99_r91_isolated_random_window_audit.json"
RNG_SEED = 99091
WINDOW_DAYS = (30, 90, 180, 365)
SAMPLES_PER_DURATION = 8


def wealth_ratio(c: dict, p: dict) -> float:
    return float((1.0 + c["return"]) / max(1e-12, 1.0 + p["return"]))


def main():
    cfg, data, raw, ex, guard, gross, quarantined, metadata = r36.v15_setup()
    cost = float(ex["base_cost_per_side"])
    idx = data.close.index
    rng = np.random.default_rng(RNG_SEED)

    audits = {}
    for days in WINDOW_DAYS:
        span = int(days) * 24
        valid_positions = np.arange(0, max(0, len(idx) - span - 1), 24, dtype=int)
        if len(valid_positions) == 0:
            audits[str(days)] = {"days": int(days), "samples": 0}
            continue
        chosen = np.sort(rng.choice(valid_positions, size=min(SAMPLES_PER_DURATION, len(valid_positions)), replace=False))
        rows = []
        for pos in chosen:
            start = idx[int(pos)]
            end = idx[int(pos + span)]
            c, p = r88.eval_slice(data, raw, ex, guard, gross, cost, start, end)
            wr = wealth_ratio(c, p)
            return_win = bool(c["return"] >= p["return"])
            dd_win = bool(abs(c["max_drawdown"]) <= abs(p["max_drawdown"]))
            worst_win = bool(abs(c["worst_day"]) <= abs(p["worst_day"]))
            rows.append({
                "start": start.isoformat(),
                "end": end.isoformat(),
                "candidate": c,
                "parent_r73": p,
                "wealth_ratio": wr,
                "return_win": return_win,
                "dd_win": dd_win,
                "worst_day_win": worst_win,
                "strict_triplet_win": bool(return_win and dd_win and worst_win),
            })
        wrs = np.array([r["wealth_ratio"] for r in rows], dtype=float)
        audits[str(days)] = {
            "days": int(days),
            "samples": int(len(rows)),
            "return_win_rate": float(np.mean([r["return_win"] for r in rows])) if rows else 0.0,
            "dd_win_rate": float(np.mean([r["dd_win"] for r in rows])) if rows else 0.0,
            "worst_day_win_rate": float(np.mean([r["worst_day_win"] for r in rows])) if rows else 0.0,
            "strict_triplet_win_rate": float(np.mean([r["strict_triplet_win"] for r in rows])) if rows else 0.0,
            "median_wealth_ratio": float(np.median(wrs)) if len(wrs) else 0.0,
            "p10_wealth_ratio": float(np.quantile(wrs, 0.10)) if len(wrs) else 0.0,
            "p90_wealth_ratio": float(np.quantile(wrs, 0.90)) if len(wrs) else 0.0,
            "windows": rows,
        }

    same_60pct_gate = all(v.get("return_win_rate", 0.0) >= 0.60 for v in audits.values())
    all_medians_positive = all(v.get("median_wealth_ratio", 0.0) > 1.0 for v in audits.values())
    long_horizon_consistency = all(audits[str(d)].get("return_win_rate", 0.0) >= 0.60 for d in (180, 365))

    out = {
        "study": "V99 R91 isolated random-window audit of frozen R88",
        "status": "DIAGNOSTIC_ONLY_NO_PROMOTION_AND_NO_PARAMETER_SELECTION",
        "objective": "repeat R90 random-window consistency as isolated replays that restart state inside each sampled window, using the unchanged R88 threshold/scale and the same >=60% return-win criterion",
        "frozen_r88": {
            "threshold": r88.STRATEGY_R72_THRESHOLD,
            "scale": r88.SCALE,
            "decision_cadence_hours": 24,
            "hold_hours": 24,
        },
        "sampling": {
            "seed": RNG_SEED,
            "durations_days": list(WINDOW_DAYS),
            "samples_per_duration": SAMPLES_PER_DURATION,
            "candidate_starts": "every 24 hourly rows; deterministic random sample without replacement",
            "state_policy": "each replay uses the same isolated-slice method as prior V99 horizon validation; no inherited equity/positions from before the sampled window",
        },
        "audits": audits,
        "gates": {
            "same_60pct_all_durations_pass": bool(same_60pct_gate),
            "all_duration_medians_above_parent": bool(all_medians_positive),
            "long_horizon_180_365_consistency_pass": bool(long_horizon_consistency),
            "isolated_consistency_pass": bool(same_60pct_gate and all_medians_positive),
        },
        "interpretation_policy": "R91 validates R88 only. No sampled window, duration or result may change the frozen R87 threshold or R88 1.10 scale. Failure cannot authorize choosing another threshold/scale from R90 probes.",
        "disclosure": "Historical research only. Frozen V99 and official paper remain untouched.",
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"study": out["study"], "gates": out["gates"], "summary": {k: {kk: vv for kk, vv in v.items() if kk != "windows"} for k, v in audits.items()}}, indent=2), flush=True)


if __name__ == "__main__":
    main()
