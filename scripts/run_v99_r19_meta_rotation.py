from __future__ import annotations

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
from paper_once_v16 import build_v16

REPORT_PATH = PROJECT / "reports" / "candidate_v99_r19_meta_rotation.json"
V16_CONFIG = PROJECT / "config" / "candidate_v16_experimental_balanced_relaxed.json"
HORIZONS = (7, 30, 90, 180, 365)


def stats(equity: pd.Series) -> dict:
    e = equity.dropna().astype(float)
    if len(e) < 2:
        return {"return": 0.0, "max_drawdown": 0.0, "best_day": 0.0,
                "worst_day": 0.0, "positive_days": 0.0}
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


def trailing_stats(equity: pd.Series, days: int) -> dict:
    e = equity.dropna()
    if len(e) < 2:
        return stats(e)
    return stats(e.loc[e.index >= e.index[-1] - pd.Timedelta(days=int(days))])


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


def run_exact(data, targets, execution, guard, gross_guard_cap, cost):
    return exact_fast(
        data,
        targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_guard_cap,
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )


def source_features(v15_equity: pd.Series, v16_equity: pd.Series) -> pd.DataFrame:
    idx = v15_equity.index.intersection(v16_equity.index)
    a = v15_equity.reindex(idx).ffill().astype(float)
    b = v16_equity.reindex(idx).ffill().astype(float)
    out = pd.DataFrame(index=idx)
    for hours, label in ((24 * 7, "7"), (24 * 30, "30"), (24 * 90, "90")):
        out[f"v15_r{label}"] = a.div(a.shift(hours)).sub(1.0)
        out[f"v16_r{label}"] = b.div(b.shift(hours)).sub(1.0)
    out["v15_dd"] = a.div(a.cummax()).sub(1.0)
    out["v16_dd"] = b.div(b.cummax()).sub(1.0)
    out["v15_r24"] = a.div(a.shift(24)).sub(1.0)
    out["v16_r24"] = b.div(b.shift(24)).sub(1.0)
    return out


def persistence_mask(trigger: pd.Series, hours: int) -> pd.Series:
    # A trigger at close t can affect target t, which executes at open t+1.
    # Rolling persistence is therefore causal and uses no future rows.
    return trigger.astype(float).rolling(hours, min_periods=1).max().gt(0.0)


def meta_targets(
    v15_targets: pd.DataFrame,
    v16_targets: pd.DataFrame,
    features: pd.DataFrame,
    *,
    dd_threshold: float,
    lead_votes_required: int,
    v16_weight: float,
    persistence_hours: int,
    joint_stress_scale: float,
    max_target_gross: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    idx = v15_targets.index
    f = features.reindex(idx).ffill()
    votes = sum(
        (f[f"v16_r{w}"] > f[f"v15_r{w}"] + 0.01).astype(int)
        for w in ("7", "30", "90")
    )
    relative_defense = (
        (f["v15_dd"] <= -abs(dd_threshold))
        & (votes >= lead_votes_required)
    )
    negative_regime = (
        (f["v15_r30"] < 0.0)
        & (f["v16_r30"] > f["v15_r30"] + 0.02)
        & (votes >= lead_votes_required)
    )
    acute_damage = (
        (f["v15_r24"] < -0.035)
        & (f["v16_r24"] > f["v15_r24"] + 0.01)
    )
    defensive_trigger = (relative_defense | negative_regime | acute_damage).fillna(False)
    defensive = persistence_mask(defensive_trigger, persistence_hours)

    w = defensive.astype(float) * float(v16_weight)
    v16 = v16_targets.reindex(index=idx, columns=v15_targets.columns).fillna(0.0)
    combined = v15_targets.mul(1.0 - w, axis=0).add(v16.mul(w, axis=0))

    joint_stress = (
        (f["v15_dd"] < -0.12)
        & (f["v15_r30"] < -0.06)
        & (f["v16_r30"] < -0.03)
    ).fillna(False)
    severe = persistence_mask(joint_stress, min(72, persistence_hours))
    scale = pd.Series(1.0, index=idx)
    scale.loc[severe] = float(joint_stress_scale)
    combined = combined.mul(scale, axis=0)
    combined = cap_gross(combined, max_target_gross)

    diagnostics = pd.DataFrame(index=idx)
    diagnostics["v16_weight"] = w
    diagnostics["joint_stress_scale"] = scale
    diagnostics["lead_votes"] = votes
    diagnostics["v15_dd"] = f["v15_dd"]
    diagnostics["defensive"] = defensive
    diagnostics["joint_stress"] = severe
    return combined, diagnostics


def isolated(data, targets, execution, guard, gross_guard_cap, cost, days):
    end = data.close.index[-1]
    start = end - pd.Timedelta(days=int(days))
    d = slice_data(data, start, end)
    t = targets.reindex(index=d.close.index, columns=d.close.columns).fillna(0.0)
    return stats(run_exact(d, t, execution, guard, gross_guard_cap, cost).equity)


def main() -> None:
    v15_candidate, data, v15_targets, v15_result, _, quarantined, metadata = build_v15()
    v16_candidate = json.loads(V16_CONFIG.read_text(encoding="utf-8"))
    v16_data, v16_targets, v16_result, _, _ = build_v16(v16_candidate)

    common_end = min(data.close.index[-1], v16_data.close.index[-1])
    data = slice_data(data, data.close.index[0], common_end)
    v15_targets = v15_targets.reindex(index=data.close.index, columns=data.close.columns).fillna(0.0)
    v15_equity = v15_result.equity.reindex(data.close.index).ffill()
    v16_targets = v16_targets.reindex(index=data.close.index, columns=data.close.columns).fillna(0.0)
    v16_equity = v16_result.equity.reindex(data.close.index).ffill()

    v14 = json.loads((PROJECT / "config" / v15_candidate["parent_candidate_config"]).read_text())
    finalist = json.loads((PROJECT / "config" / v14["frozen_core_config"]).read_text())
    base = json.loads((PROJECT / "config" / finalist["base_candidate_config"]).read_text())
    execution = base["execution"]
    guard = v14["circuit_breaker"]
    max_target_gross = float(v14["allocation"]["maximum_portfolio_gross"])
    gross_guard_cap = float(v14["allocation"]["gross_drift_guard_cap"])
    features = source_features(v15_equity, v16_equity)

    # Re-run the V15 benchmark on the exact same clipped dataset used by R19.
    v15_benchmark = run_exact(
        data, v15_targets, execution, guard, gross_guard_cap,
        execution["base_cost_per_side"]
    )
    v15_severe = run_exact(
        data, v15_targets, execution, guard, gross_guard_cap,
        execution["severe_cost_per_side"]
    )
    v15_full = stats(v15_benchmark.equity)
    v15_severe_stats = stats(v15_severe.equity)
    v15_isolated = {
        str(d): isolated(data, v15_targets, execution, guard, gross_guard_cap,
                         execution["base_cost_per_side"], d)
        for d in HORIZONS
    }

    rows = []
    cache = {}
    for dd_threshold in (0.04, 0.07, 0.10):
        for lead_votes in (1, 2):
            for v16_weight in (0.50, 1.00):
                for persistence in (24, 72, 168):
                    for joint_scale in (0.50, 1.00):
                        targets, diag = meta_targets(
                            v15_targets, v16_targets, features,
                            dd_threshold=dd_threshold,
                            lead_votes_required=lead_votes,
                            v16_weight=v16_weight,
                            persistence_hours=persistence,
                            joint_stress_scale=joint_scale,
                            max_target_gross=max_target_gross,
                        )
                        key = (
                            f"dd{dd_threshold:.2f}_votes{lead_votes}_"
                            f"w{v16_weight:.2f}_p{persistence}_cash{joint_scale:.2f}"
                        )
                        result = run_exact(
                            data, targets, execution, guard, gross_guard_cap,
                            execution["base_cost_per_side"]
                        )
                        s = stats(result.equity)
                        wealth_ratio = (1.0 + s["return"]) / max(1e-12, 1.0 + v15_full["return"])
                        dd_ratio = abs(s["max_drawdown"]) / max(1e-12, abs(v15_full["max_drawdown"]))
                        worst_ratio = abs(s["worst_day"]) / max(1e-12, abs(v15_full["worst_day"]))
                        trailing = {str(d): trailing_stats(result.equity, d) for d in HORIZONS}
                        v15_trailing = {str(d): trailing_stats(v15_benchmark.equity, d) for d in HORIZONS}
                        trailing_wins = sum(
                            trailing[str(d)]["return"] >= v15_trailing[str(d)]["return"]
                            for d in HORIZONS
                        )
                        score = (
                            5.0 * np.log(max(wealth_ratio, 1e-12))
                            + 0.18 * trailing_wins
                            + 1.6 * max(0.0, 1.0 - dd_ratio)
                            - 2.4 * max(0.0, dd_ratio - 1.0)
                            - 1.5 * max(0.0, worst_ratio - 1.0)
                        )
                        row = {
                            "key": key,
                            "params": {
                                "dd_threshold": dd_threshold,
                                "lead_votes_required": lead_votes,
                                "v16_weight": v16_weight,
                                "persistence_hours": persistence,
                                "joint_stress_scale": joint_scale,
                            },
                            "summary": s,
                            "wealth_ratio_to_v15": float(wealth_ratio),
                            "drawdown_ratio_to_v15": float(dd_ratio),
                            "worst_day_ratio_to_v15": float(worst_ratio),
                            "trailing_horizon_wins_vs_v15": int(trailing_wins),
                            "defensive_fraction": float(diag["defensive"].mean()),
                            "joint_stress_fraction": float(diag["joint_stress"].mean()),
                            "average_v16_weight": float(diag["v16_weight"].mean()),
                            "score": float(score),
                        }
                        rows.append(row)
                        cache[key] = targets

    ranking = sorted(rows, key=lambda r: r["score"], reverse=True)
    finalists = []
    for row in ranking[:10]:
        targets = cache[row["key"]]
        iso = {
            str(d): isolated(data, targets, execution, guard, gross_guard_cap,
                             execution["base_cost_per_side"], d)
            for d in HORIZONS
        }
        wins = {
            str(d): bool(iso[str(d)]["return"] >= v15_isolated[str(d)]["return"])
            for d in HORIZONS
        }
        dd_ok = {
            str(d): bool(abs(iso[str(d)]["max_drawdown"]) <= abs(v15_isolated[str(d)]["max_drawdown"]) + 1e-12)
            for d in HORIZONS
        }
        severe = stats(run_exact(
            data, targets, execution, guard, gross_guard_cap,
            execution["severe_cost_per_side"]
        ).equity)
        severe_ratio = (1.0 + severe["return"]) / max(1e-12, 1.0 + v15_severe_stats["return"])
        gate = bool(
            all(wins.values())
            and row["wealth_ratio_to_v15"] >= 1.0
            and row["drawdown_ratio_to_v15"] <= 1.0
            and row["worst_day_ratio_to_v15"] <= 1.0
            and severe_ratio >= 1.0
        )
        finalists.append({
            **row,
            "isolated": iso,
            "isolated_wins_vs_v15": wins,
            "isolated_drawdown_improved_or_equal": dd_ok,
            "severe_cost": severe,
            "severe_wealth_ratio_to_v15": float(severe_ratio),
            "superior_gate_passed": gate,
        })

    finalists.sort(key=lambda r: (
        r["superior_gate_passed"],
        sum(r["isolated_wins_vs_v15"].values()),
        r["wealth_ratio_to_v15"],
        -r["drawdown_ratio_to_v15"],
    ), reverse=True)
    selected = finalists[0] if finalists else None

    report = {
        "study": "V99 R19 meta-engine V15 growth / V16 defense rotation",
        "status": "RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER",
        "objective": "beat V15 without adding gross leverage by rotating causally into V16 defense and reducing exposure only in joint stress",
        "architecture": "V15 default growth engine; conditional V16 rotation; optional joint-stress de-risk; no additive satellite gross",
        "selection_disclosure": "Historical research screen, not a pristine holdout. Source equity histories are causal but researched. Any winner must pass random-window/calendar-year/parameter-neighborhood validation before a new forward boundary.",
        "data_latest": data.close.index[-1].isoformat(),
        "grid_size": len(rows),
        "target_gross_cap": max_target_gross,
        "v15": {
            "summary": v15_full,
            "isolated": v15_isolated,
            "severe_cost": v15_severe_stats,
        },
        "selected": selected,
        "finalists": finalists,
        "screening_ranking": ranking,
        "promotion_rule": {
            "beat_v15_isolated_7_30_90_180_365": True,
            "full_terminal_wealth_at_least_v15": True,
            "full_max_drawdown_no_worse_than_v15": True,
            "full_worst_day_no_worse_than_v15": True,
            "severe_cost_terminal_wealth_at_least_v15": True,
            "next_if_passed": "R20 anti-overfit validation, then freeze a NEW V99 revision and start a new independent paper boundary",
        },
        "funding_quarantined_symbols": quarantined,
        "v15_metadata": metadata,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "study": report["study"],
        "grid_size": report["grid_size"],
        "v15": report["v15"],
        "selected": selected,
    }, indent=2))


if __name__ == "__main__":
    main()
