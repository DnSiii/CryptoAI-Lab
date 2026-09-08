from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import FuturesData
from paper_once_v15 import build_v15

REPORT_PATH = PROJECT / "reports" / "candidate_v99_r17_superior.json"
HORIZONS = (7, 30, 90, 180, 365)
TOP_N_ISOLATED = 6


def summary(equity: pd.Series) -> dict:
    e = equity.dropna().astype(float)
    if len(e) < 2:
        return {"return": 0.0, "max_drawdown": 0.0, "best_day": 0.0, "worst_day": 0.0, "positive_days": 0.0}
    norm = e / float(e.iloc[0])
    peak = norm.cummax()
    dd = norm / peak - 1.0
    daily = norm.resample("1D").last().pct_change(fill_method=None).dropna()
    return {
        "return": float(norm.iloc[-1] - 1.0),
        "max_drawdown": float(dd.min()),
        "best_day": float(daily.max()) if len(daily) else 0.0,
        "worst_day": float(daily.min()) if len(daily) else 0.0,
        "positive_days": float((daily > 0.0).mean()) if len(daily) else 0.0,
    }


def horizon_summary(equity: pd.Series, days: int) -> dict:
    e = equity.dropna()
    if len(e) < 2:
        return summary(e)
    end = e.index[-1]
    start = end - pd.Timedelta(days=days)
    s = e.loc[e.index >= start]
    return summary(s)


def slice_data(data: FuturesData, start: pd.Timestamp, end: pd.Timestamp) -> FuturesData:
    return FuturesData(
        frames={name: frame.loc[start:end].copy() for name, frame in data.frames.items()},
        funding=data.funding.loc[start:end].copy(),
        symbols=data.symbols,
    )


def cap_gross(targets: pd.DataFrame, cap: float) -> pd.DataFrame:
    gross = targets.abs().sum(axis=1)
    factor = (cap / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    return targets.mul(factor, axis=0)


def causal_scale(base_equity: pd.Series, strong: float, weak: float, strong_votes: int) -> pd.Series:
    e = base_equity.astype(float)
    r7 = e.div(e.shift(24 * 7)).sub(1.0)
    r30 = e.div(e.shift(24 * 30)).sub(1.0)
    r90 = e.div(e.shift(24 * 90)).sub(1.0)
    r24 = e.div(e.shift(24)).sub(1.0)
    dd = e.div(e.cummax()).sub(1.0)
    votes = pd.concat([(r7 > 0.0), (r30 > 0.0), (r90 > 0.0)], axis=1).sum(axis=1)

    scale = pd.Series(1.0, index=e.index, dtype=float)
    strong_mask = (votes >= strong_votes) & (dd > -0.05) & (r30 > 0.0)
    weak_mask = (votes <= 1) | (dd < -0.09) | (r30 < -0.04)
    scale.loc[strong_mask] = strong
    scale.loc[weak_mask] = weak

    # Acute brake after a bad 24h move. The signal is lagged below, so the
    # current close can only affect subsequent targets.
    scale.loc[r24 < -0.025] = np.minimum(scale.loc[r24 < -0.025], 0.40)
    scale.loc[r24 < -0.045] = np.minimum(scale.loc[r24 < -0.045], 0.25)
    return scale.shift(1).fillna(1.0)


def run_exact(data, targets, execution, guard, gross_guard_cap, cost_per_side):
    return exact_fast(
        data,
        targets,
        cost_per_side=cost_per_side,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_guard_cap,
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )


def isolated(data, targets, execution, guard, gross_guard_cap, cost, days):
    end = data.close.index[-1]
    start = end - pd.Timedelta(days=days)
    d = slice_data(data, start, end)
    t = targets.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    r = run_exact(d, t, execution, guard, gross_guard_cap, cost)
    return summary(r.equity)


def main() -> None:
    candidate, data, v15_targets, v15_result, _, quarantined, metadata = build_v15()
    v14 = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text())
    finalist = json.loads((PROJECT / "config" / v14["frozen_core_config"]).read_text())
    base = json.loads((PROJECT / "config" / finalist["base_candidate_config"]).read_text())
    execution = base["execution"]
    guard = v14["circuit_breaker"]

    v15_full = summary(v15_result.equity)
    v15_trailing = {str(d): horizon_summary(v15_result.equity, d) for d in HORIZONS}
    v15_isolated = {
        str(d): isolated(data, v15_targets, execution, guard, v14["allocation"]["gross_drift_guard_cap"], execution["base_cost_per_side"], d)
        for d in HORIZONS
    }

    grid = list(itertools.product(
        (1.25, 1.45, 1.65),
        (0.45, 0.70),
        (2, 3),
        (1.90, 2.15),
    ))
    rows = []
    target_cache = {}
    for strong, weak, strong_votes, max_gross in grid:
        scale = causal_scale(v15_result.equity.reindex(v15_targets.index).ffill(), strong, weak, strong_votes)
        scaled = cap_gross(v15_targets.mul(scale, axis=0), max_gross)
        key = f"s{strong:.2f}_w{weak:.2f}_v{strong_votes}_g{max_gross:.2f}"
        target_cache[key] = scaled
        result = run_exact(
            data,
            scaled,
            execution,
            guard,
            max_gross + 0.15,
            execution["base_cost_per_side"],
        )
        s = summary(result.equity)
        trailing = {str(d): horizon_summary(result.equity, d) for d in HORIZONS}
        wealth_ratio = (1.0 + s["return"]) / max(1e-12, 1.0 + v15_full["return"])
        dd_ratio = abs(s["max_drawdown"]) / max(1e-12, abs(v15_full["max_drawdown"]))
        horizon_wins = sum(
            trailing[str(d)]["return"] >= v15_trailing[str(d)]["return"]
            for d in HORIZONS
        )
        score = (
            3.0 * np.log(max(wealth_ratio, 1e-12))
            + 0.12 * horizon_wins
            - 1.8 * max(0.0, dd_ratio - 1.0)
            - 1.2 * max(0.0, abs(s["worst_day"]) / max(abs(v15_full["worst_day"]), 1e-12) - 1.0)
        )
        rows.append({
            "key": key,
            "params": {
                "strong_multiplier": strong,
                "weak_multiplier": weak,
                "strong_votes": strong_votes,
                "maximum_target_gross": max_gross,
            },
            "summary": s,
            "trailing": trailing,
            "wealth_ratio_to_v15": float(wealth_ratio),
            "drawdown_ratio_to_v15": float(dd_ratio),
            "trailing_horizon_wins_vs_v15": int(horizon_wins),
            "score": float(score),
        })

    ranking = sorted(rows, key=lambda r: r["score"], reverse=True)
    finalists = []
    for row in ranking[:TOP_N_ISOLATED]:
        key = row["key"]
        targets = target_cache[key]
        isolated_result = {
            str(d): isolated(
                data,
                targets,
                execution,
                guard,
                row["params"]["maximum_target_gross"] + 0.15,
                execution["base_cost_per_side"],
                d,
            )
            for d in HORIZONS
        }
        severe = run_exact(
            data,
            targets,
            execution,
            guard,
            row["params"]["maximum_target_gross"] + 0.15,
            execution["severe_cost_per_side"],
        )
        severe_summary = summary(severe.equity)
        isolated_wins = {
            str(d): bool(isolated_result[str(d)]["return"] >= v15_isolated[str(d)]["return"])
            for d in HORIZONS
        }
        isolated_dd_ok = {
            str(d): bool(abs(isolated_result[str(d)]["max_drawdown"]) <= 1.05 * abs(v15_isolated[str(d)]["max_drawdown"]) + 1e-12)
            for d in HORIZONS
        }
        superior_gate = bool(
            all(isolated_wins.values())
            and all(isolated_dd_ok.values())
            and row["wealth_ratio_to_v15"] >= 1.10
            and row["drawdown_ratio_to_v15"] <= 1.05
            and abs(row["summary"]["worst_day"]) <= 1.05 * abs(v15_full["worst_day"]) + 1e-12
            and severe_summary["return"] > 0.0
        )
        finalists.append({
            **row,
            "isolated": isolated_result,
            "isolated_wins_vs_v15": isolated_wins,
            "isolated_drawdown_ok": isolated_dd_ok,
            "severe_cost": severe_summary,
            "superior_gate_passed": superior_gate,
        })

    finalists.sort(
        key=lambda r: (
            r["superior_gate_passed"],
            sum(r["isolated_wins_vs_v15"].values()),
            r["wealth_ratio_to_v15"],
            -r["drawdown_ratio_to_v15"],
        ),
        reverse=True,
    )
    selected = finalists[0] if finalists else None
    report = {
        "study": "V99 R17 V15-first causal convexity sweep",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "beat V15 decisively on compounded ROI while keeping drawdown and worst-day damage near or below V15",
        "architecture": "V15 alpha core + causal performance-regime exposure accelerator + acute loss brake",
        "selection_disclosure": "This is researched historical replay, not a pristine holdout. Parameters are screened on historical data; any winner must be frozen before a new independent forward boundary.",
        "grid_size": len(grid),
        "v15": {
            "summary": v15_full,
            "trailing": v15_trailing,
            "isolated": v15_isolated,
        },
        "selected": selected,
        "finalists": finalists,
        "screening_ranking": ranking,
        "promotion_rule": {
            "must_beat_v15_isolated_7_30_90_180_365": True,
            "full_wealth_ratio_minimum": 1.10,
            "max_drawdown_ratio_to_v15_maximum": 1.05,
            "worst_day_ratio_to_v15_maximum": 1.05,
            "severe_cost_return_must_be_positive": True,
            "next_step_if_passed": "freeze parameters and start a NEW V99 revision with a new independent paper boundary",
        },
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "study": report["study"],
        "grid_size": report["grid_size"],
        "v15_full": v15_full,
        "selected": selected,
    }, indent=2))


if __name__ == "__main__":
    main()
