from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path

from cryptoai.metrics import performance
from cryptoai.replay import CandidateSpec, load_universe, run_replay
from cryptoai.splits import ResearchSplit
from cryptoai.universe import select_discovery_universe


CORE_MODELS = ("momentum", "ema", "breakout", "ensemble")
HORIZON_SETS = (
    (20, 40, 60),
    (30, 60, 90),
    (60, 90, 120, 150),
    (90, 120, 180),
    (120, 180, 240),
)
RISK_PROFILES = (
    {"target_volatility": 0.30, "max_gross_leverage": 1.25, "max_single_weight": 0.50},
    {"target_volatility": 0.45, "max_gross_leverage": 1.75, "max_single_weight": 0.60},
    {"target_volatility": 0.60, "max_gross_leverage": 2.25, "max_single_weight": 0.70},
)


def slice_perf(returns, start: str, end: str) -> dict[str, float | int]:
    segment = returns.loc[start:end]
    return performance(segment).to_dict()


def robust_score(discovery: dict, val1: dict, val2: dict, pre: dict) -> float:
    cagrs = [float(discovery["cagr"]), float(val1["cagr"]), float(val2["cagr"])]
    min_cagr = min(cagrs)
    mean_cagr = sum(cagrs) / len(cagrs)
    dd_penalty = max(0.0, abs(float(pre["max_drawdown"])) - 0.35) * 3.0
    negative_penalty = sum(max(0.0, -x) for x in cagrs) * 4.0
    return min_cagr * 0.60 + mean_cagr * 0.40 - dd_penalty - negative_penalty


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max-symbols", type=int, default=12)
    p.add_argument("--cache-dir", default=".cache/cryptoai")
    p.add_argument("--report", default="reports/core_discovery.json")
    args = p.parse_args()

    split = ResearchSplit()
    symbols, universe_meta = select_discovery_universe(args.max_symbols, existed_by="2021-01")
    data = load_universe(symbols, split.discovery_start, "2024-12-31", Path(args.cache_dir))

    rows: list[dict[str, object]] = []
    for model in CORE_MODELS:
        for horizons in HORIZON_SETS:
            for risk in RISK_PROFILES:
                spec = CandidateSpec(
                    core_model=model,
                    horizons_days=horizons,
                    carry_base_allocation=0.0,
                    carry_dominant_allocation=0.0,
                    target_volatility=risk["target_volatility"],
                    max_gross_leverage=risk["max_gross_leverage"],
                    max_single_weight=risk["max_single_weight"],
                )
                result = run_replay(data, spec)
                returns = result["returns"]
                split.assert_selection_index_is_pre_holdout(returns.index)
                discovery = slice_perf(returns, "2020-01-01", "2022-12-31 23:00:00+00:00")
                val1 = slice_perf(returns, "2023-01-01", "2023-12-31 23:00:00+00:00")
                val2 = slice_perf(returns, "2024-01-01", "2024-12-31 23:00:00+00:00")
                pre = slice_perf(returns, "2020-01-01", "2024-12-31 23:00:00+00:00")
                score = robust_score(discovery, val1, val2, pre)
                rows.append({
                    "spec": asdict(spec),
                    "score": score,
                    "discovery": discovery,
                    "validation_2023": val1,
                    "validation_2024": val2,
                    "pre_holdout": pre,
                    "decisions_per_month": result["decisions_per_month"],
                    "diagnostics": result["diagnostics"],
                })

    rows.sort(key=lambda x: float(x["score"]), reverse=True)
    top = rows[:12]

    # Stress only the best 5 pre-holdout candidates; no holdout access is allowed here.
    stress: list[dict[str, object]] = []
    for row in top[:5]:
        raw = row["spec"]
        spec = CandidateSpec(**raw)
        severe = run_replay(data, spec, cost_multiplier=3.0)
        delayed = run_replay(data, replace(spec, execution_delay_hours=3))
        severe_pre = slice_perf(severe["returns"], "2020-01-01", "2024-12-31 23:00:00+00:00")
        delayed_pre = slice_perf(delayed["returns"], "2020-01-01", "2024-12-31 23:00:00+00:00")
        stress.append({
            "spec": raw,
            "score": row["score"],
            "base_pre_holdout": row["pre_holdout"],
            "severe_cost_pre_holdout": severe_pre,
            "delay_3h_pre_holdout": delayed_pre,
        })

    report = {
        "status": "CORE_DISCOVERY_PRE_HOLDOUT_ONLY",
        "selection_boundary": "No data from 2025-01-01 onward was loaded or used.",
        "universe": universe_meta,
        "tested_candidates": len(rows),
        "top_candidates": top,
        "top_stress": stress,
    }
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    best = top[0]
    print(json.dumps({
        "status": report["status"],
        "tested_candidates": len(rows),
        "best_model": best["spec"]["core_model"],
        "best_horizons": best["spec"]["horizons_days"],
        "best_score": best["score"],
        "discovery_cagr": best["discovery"]["cagr"],
        "validation_2023_cagr": best["validation_2023"]["cagr"],
        "validation_2024_cagr": best["validation_2024"]["cagr"],
        "pre_holdout_cagr": best["pre_holdout"]["cagr"],
        "pre_holdout_max_drawdown": best["pre_holdout"]["max_drawdown"],
        "report": str(path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
