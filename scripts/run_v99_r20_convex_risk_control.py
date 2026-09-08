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

REPORT_PATH = PROJECT / "reports" / "candidate_v99_r20_convex_risk_control.json"
HORIZONS = (7, 30, 90, 180, 365)
SEED = 20260908


def stats(equity: pd.Series) -> dict:
    e = equity.dropna().astype(float)
    if len(e) < 2:
        return {"return": 0.0, "max_drawdown": 0.0, "best_day": 0.0, "worst_day": 0.0, "positive_days": 0.0}
    n = e / float(e.iloc[0])
    dd = n / n.cummax() - 1.0
    daily = n.resample("1D").last().pct_change(fill_method=None).dropna()
    return {
        "return": float(n.iloc[-1] - 1.0),
        "max_drawdown": float(dd.min()),
        "best_day": float(daily.max()) if len(daily) else 0.0,
        "worst_day": float(daily.min()) if len(daily) else 0.0,
        "positive_days": float((daily > 0.0).mean()) if len(daily) else 0.0,
    }


def slice_data(data: FuturesData, start: pd.Timestamp, end: pd.Timestamp) -> FuturesData:
    return FuturesData(
        frames={k: v.loc[start:end].copy() for k, v in data.frames.items()},
        funding=data.funding.loc[start:end].copy(),
        symbols=data.symbols,
    )


def cap_gross(targets: pd.DataFrame, cap: float) -> pd.DataFrame:
    gross = targets.abs().sum(axis=1)
    factor = (cap / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    return targets.mul(factor, axis=0)


def persistent(trigger: pd.Series, hours: int) -> pd.Series:
    return trigger.astype(float).rolling(hours, min_periods=1).max().gt(0.0)


def regime_scale(
    equity: pd.Series,
    *,
    attack_scale: float,
    defense_scale: float,
    attack_votes_required: int,
    dd_defense: float,
    defense_persistence: int,
) -> tuple[pd.Series, pd.DataFrame]:
    e = equity.astype(float)
    r24 = e.div(e.shift(24)).sub(1.0)
    r7 = e.div(e.shift(24 * 7)).sub(1.0)
    r30 = e.div(e.shift(24 * 30)).sub(1.0)
    r90 = e.div(e.shift(24 * 90)).sub(1.0)
    dd = e.div(e.cummax()).sub(1.0)
    rv7 = e.pct_change(fill_method=None).rolling(24 * 7, min_periods=24).std() * np.sqrt(24 * 365)
    rv30 = e.pct_change(fill_method=None).rolling(24 * 30, min_periods=24 * 7).std() * np.sqrt(24 * 365)

    attack_votes = pd.concat([
        (r7 > 0.025),
        (r30 > 0.06),
        (r90 > 0.10),
    ], axis=1).sum(axis=1)
    attack = (
        (attack_votes >= attack_votes_required)
        & (dd > -0.035)
        & (r24 > -0.02)
        & ((rv7 <= 1.25 * rv30) | rv30.isna())
    ).fillna(False)

    defense_trigger = (
        (dd <= -abs(dd_defense))
        | (r24 < -0.035)
        | ((r7 < -0.06) & (r30 < 0.0))
        | ((rv7 > 1.55 * rv30) & (r7 < 0.0))
    ).fillna(False)
    defense = persistent(defense_trigger, defense_persistence)

    scale = pd.Series(1.0, index=e.index, dtype=float)
    scale.loc[attack & ~defense] = float(attack_scale)
    scale.loc[defense] = float(defense_scale)

    # Use close-t information only for the next target; execution remains t+1 open.
    scale = scale.shift(1).fillna(1.0)
    diag = pd.DataFrame(index=e.index)
    diag["attack"] = attack
    diag["defense"] = defense
    diag["scale"] = scale
    diag["drawdown"] = dd
    diag["r24"] = r24
    diag["r7"] = r7
    diag["r30"] = r30
    diag["r90"] = r90
    diag["rv7"] = rv7
    diag["rv30"] = rv30
    return scale, diag


def run_exact(data, targets, execution, guard, gross_cap, cost):
    return exact_fast(
        data,
        targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )


def isolated(data, targets, execution, guard, gross_cap, cost, days):
    end = data.close.index[-1]
    start = end - pd.Timedelta(days=int(days))
    d = slice_data(data, start, end)
    t = targets.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    return stats(run_exact(d, t, execution, guard, gross_cap, cost).equity)


def random_window_score(data, candidate_targets, benchmark_targets, execution, guard, gross_cap, cost, windows=48):
    idx = data.close.index
    rng = np.random.default_rng(SEED)
    lengths = np.array([30, 60, 90, 180, 365])
    rows = []
    min_ts = idx[0]
    max_ts = idx[-1]
    for _ in range(windows):
        days = int(rng.choice(lengths))
        max_start = max_ts - pd.Timedelta(days=days)
        eligible = idx[(idx >= min_ts) & (idx <= max_start)]
        if len(eligible) == 0:
            continue
        start = pd.Timestamp(rng.choice(eligible.to_numpy()))
        end = min(max_ts, start + pd.Timedelta(days=days))
        d = slice_data(data, start, end)
        ct = candidate_targets.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
        bt = benchmark_targets.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
        cs = stats(run_exact(d, ct, execution, guard, gross_cap, cost).equity)
        bs = stats(run_exact(d, bt, execution, guard, gross_cap, cost).equity)
        rows.append({
            "days": days,
            "candidate_return": cs["return"],
            "benchmark_return": bs["return"],
            "candidate_dd": cs["max_drawdown"],
            "benchmark_dd": bs["max_drawdown"],
            "return_win": cs["return"] >= bs["return"],
            "dd_win": abs(cs["max_drawdown"]) <= abs(bs["max_drawdown"]),
        })
    return {
        "windows": len(rows),
        "return_win_rate": float(np.mean([r["return_win"] for r in rows])) if rows else 0.0,
        "drawdown_win_rate": float(np.mean([r["dd_win"] for r in rows])) if rows else 0.0,
        "both_win_rate": float(np.mean([r["return_win"] and r["dd_win"] for r in rows])) if rows else 0.0,
        "median_return_advantage": float(np.median([r["candidate_return"] - r["benchmark_return"] for r in rows])) if rows else 0.0,
        "rows": rows,
    }


def main() -> None:
    candidate, data, v15_targets, v15_result, _, quarantined, metadata = build_v15()
    v14 = json.loads((PROJECT / "config" / candidate["parent_candidate_config"]).read_text())
    finalist = json.loads((PROJECT / "config" / v14["frozen_core_config"]).read_text())
    base = json.loads((PROJECT / "config" / finalist["base_candidate_config"]).read_text())
    execution = base["execution"]
    guard = v14["circuit_breaker"]
    base_gross_cap = float(v14["allocation"]["gross_drift_guard_cap"])

    # Re-run benchmark on exactly the same data/execution contract.
    v15 = run_exact(data, v15_targets, execution, guard, base_gross_cap, execution["base_cost_per_side"])
    v15_full = stats(v15.equity)
    v15_severe = stats(run_exact(data, v15_targets, execution, guard, base_gross_cap, execution["severe_cost_per_side"]).equity)
    v15_iso = {
        str(d): isolated(data, v15_targets, execution, guard, base_gross_cap, execution["base_cost_per_side"], d)
        for d in HORIZONS
    }

    rows = []
    cache = {}
    grid = itertools.product(
        (1.10, 1.20, 1.30),
        (0.20, 0.40, 0.60),
        (2, 3),
        (0.05, 0.08),
        (24, 72),
    )
    for attack_scale, defense_scale, attack_votes, dd_defense, persistence in grid:
        scale, diag = regime_scale(
            v15.equity.reindex(v15_targets.index).ffill(),
            attack_scale=attack_scale,
            defense_scale=defense_scale,
            attack_votes_required=attack_votes,
            dd_defense=dd_defense,
            defense_persistence=persistence,
        )
        max_target_gross = float(v15_targets.abs().sum(axis=1).max()) * attack_scale
        targets = cap_gross(v15_targets.mul(scale, axis=0), max_target_gross)
        gross_cap = max(base_gross_cap, max_target_gross + 0.10)
        result = run_exact(data, targets, execution, guard, gross_cap, execution["base_cost_per_side"])
        s = stats(result.equity)
        wealth_ratio = (1.0 + s["return"]) / max(1e-12, 1.0 + v15_full["return"])
        dd_ratio = abs(s["max_drawdown"]) / max(1e-12, abs(v15_full["max_drawdown"]))
        worst_ratio = abs(s["worst_day"]) / max(1e-12, abs(v15_full["worst_day"]))
        key = f"a{attack_scale:.2f}_d{defense_scale:.2f}_v{attack_votes}_dd{dd_defense:.2f}_p{persistence}"
        score = (
            5.0 * np.log(max(wealth_ratio, 1e-12))
            + 2.0 * max(0.0, 1.0 - dd_ratio)
            - 3.0 * max(0.0, dd_ratio - 1.0)
            - 1.5 * max(0.0, worst_ratio - 1.0)
        )
        row = {
            "key": key,
            "params": {
                "attack_scale": attack_scale,
                "defense_scale": defense_scale,
                "attack_votes_required": attack_votes,
                "dd_defense": dd_defense,
                "defense_persistence_hours": persistence,
                "gross_guard_cap": gross_cap,
            },
            "summary": s,
            "wealth_ratio_to_v15": float(wealth_ratio),
            "drawdown_ratio_to_v15": float(dd_ratio),
            "worst_day_ratio_to_v15": float(worst_ratio),
            "attack_fraction": float(diag["attack"].mean()),
            "defense_fraction": float(diag["defense"].mean()),
            "average_scale": float(diag["scale"].mean()),
            "score": float(score),
        }
        rows.append(row)
        cache[key] = (targets, gross_cap)

    ranking = sorted(rows, key=lambda r: r["score"], reverse=True)
    finalists = []
    for row in ranking[:10]:
        targets, gross_cap = cache[row["key"]]
        iso = {
            str(d): isolated(data, targets, execution, guard, gross_cap, execution["base_cost_per_side"], d)
            for d in HORIZONS
        }
        iso_wins = {str(d): iso[str(d)]["return"] >= v15_iso[str(d)]["return"] for d in HORIZONS}
        iso_dd = {str(d): abs(iso[str(d)]["max_drawdown"]) <= abs(v15_iso[str(d)]["max_drawdown"]) for d in HORIZONS}
        severe = stats(run_exact(data, targets, execution, guard, gross_cap, execution["severe_cost_per_side"]).equity)
        severe_ratio = (1.0 + severe["return"]) / max(1e-12, 1.0 + v15_severe["return"])
        rw = random_window_score(
            data, targets, v15_targets, execution, guard, gross_cap,
            execution["base_cost_per_side"], windows=48,
        )
        gate = bool(
            all(iso_wins.values())
            and row["wealth_ratio_to_v15"] >= 1.15
            and row["drawdown_ratio_to_v15"] <= 0.85
            and row["worst_day_ratio_to_v15"] <= 0.90
            and severe_ratio >= 1.10
            and rw["return_win_rate"] >= 0.65
            and rw["both_win_rate"] >= 0.50
        )
        finalists.append({
            **row,
            "isolated": iso,
            "isolated_return_wins_vs_v15": iso_wins,
            "isolated_drawdown_wins_vs_v15": iso_dd,
            "severe_cost": severe,
            "severe_wealth_ratio_to_v15": float(severe_ratio),
            "random_window_validation": rw,
            "superior_gate_passed": gate,
        })

    finalists.sort(key=lambda r: (
        r["superior_gate_passed"],
        sum(r["isolated_return_wins_vs_v15"].values()),
        r["random_window_validation"]["both_win_rate"],
        r["wealth_ratio_to_v15"],
        -r["drawdown_ratio_to_v15"],
    ), reverse=True)
    selected = finalists[0] if finalists else None
    report = {
        "study": "V99 R20 convex growth / hard defense risk-control",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "materially exceed V15 wealth while cutting drawdown and worst-day loss using only causal V15 equity-state information",
        "architecture": "V15 core; modest scale-up only in strong low-drawdown regimes; hard de-risk after acute loss, drawdown or volatility shock",
        "selection_disclosure": "Historical research screen. No future information is used in the regime signal, but parameters are researched on history. A winner still requires freezing and a new independent forward paper boundary.",
        "grid_size": len(rows),
        "v15": {"summary": v15_full, "isolated": v15_iso, "severe_cost": v15_severe},
        "selected": selected,
        "finalists": finalists,
        "screening_ranking": ranking,
        "promotion_rule": {
            "beat_v15_isolated_all_horizons": True,
            "full_wealth_ratio_minimum": 1.15,
            "drawdown_ratio_maximum": 0.85,
            "worst_day_ratio_maximum": 0.90,
            "severe_cost_wealth_ratio_minimum": 1.10,
            "random_window_return_win_rate_minimum": 0.65,
            "random_window_both_return_and_dd_win_rate_minimum": 0.50,
        },
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "study": report["study"],
        "grid_size": report["grid_size"],
        "v15": v15_full,
        "selected": selected,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
