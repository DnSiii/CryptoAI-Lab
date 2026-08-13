from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

from cryptoai.execution import scheduled_hold
from cryptoai.gates import PromotionGates
from cryptoai.metrics import block_bootstrap_ruin_probability, decisions_per_month, performance
from cryptoai.replay import (
    CandidateSpec,
    ReplayData,
    _core_signal,
    _trend_confirmation_multiplier,
    _volatility_shock_multiplier,
    load_universe,
)
from cryptoai.splits import ResearchSplit
from cryptoai.universe import select_discovery_universe


INTERVALS = (24, 12, 8)
L1_BANDS = (0.025, 0.05, 0.10, 0.15)
RISK_PROFILES = (
    {"target_volatility": 0.60, "max_gross_leverage": 2.25, "max_single_weight": 0.75},
    {"target_volatility": 0.62, "max_gross_leverage": 2.30, "max_single_weight": 0.78},
    {"target_volatility": 0.64, "max_gross_leverage": 2.38, "max_single_weight": 0.80},
)
CONFLICT_SCALES = (0.40, 0.50)


def _execution_weights(
    data: ReplayData,
    spec: CandidateSpec,
    *,
    interval_hours: int,
    l1_band: float,
    anchor_hour: int,
) -> pd.DataFrame:
    close = data.close
    asset_returns = close.pct_change(fill_method=None)

    # Signals are evaluated only from information available at each timestamp;
    # actual portfolio changes occur only on the fixed execution schedule below.
    target = _core_signal(
        close,
        spec.horizons_days,
        spec.core_model,
        spec.core_scope,
        spec.cross_section_quantile,
    )

    raw_ret = (target.shift(1).fillna(0.0) * asset_returns.fillna(0.0)).sum(axis=1)
    rolling_vol = raw_ret.rolling(spec.vol_lookback_days * 24, min_periods=14 * 24).std() * np.sqrt(365.25 * 24)
    scale = (spec.target_volatility / rolling_vol.replace(0.0, np.nan)).clip(upper=spec.max_gross_leverage).fillna(0.0)
    target = target.mul(scale, axis=0)

    gross = target.abs().sum(axis=1)
    gross_scale = (spec.max_gross_leverage / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    target = target.mul(gross_scale, axis=0).clip(-spec.max_single_weight, spec.max_single_weight)
    gross = target.abs().sum(axis=1)
    gross_scale = (spec.max_gross_leverage / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(1.0)
    target = target.mul(gross_scale, axis=0)

    target = target.mul(_trend_confirmation_multiplier(close, spec))
    target = target.mul(_volatility_shock_multiplier(close, spec))

    weights = scheduled_hold(
        target,
        close,
        interval_hours=interval_hours,
        anchor_hour=anchor_hour,
        l1_band=l1_band,
    )
    if spec.execution_delay_hours:
        weights = weights.shift(spec.execution_delay_hours).fillna(0.0)
    return weights


def run_execution(
    data: ReplayData,
    spec: CandidateSpec,
    *,
    interval_hours: int,
    l1_band: float,
    anchor_hour: int = 0,
    cost_multiplier: float = 1.0,
    funding_adverse: bool = False,
) -> dict[str, object]:
    weights = _execution_weights(
        data,
        spec,
        interval_hours=interval_hours,
        l1_band=l1_band,
        anchor_hour=anchor_hour,
    )
    close = data.close
    asset_returns = close.pct_change(fill_method=None)
    funding = data.funding.reindex_like(close).fillna(0.0)
    held = weights.shift(1).fillna(0.0)
    price_pnl = (held * asset_returns.fillna(0.0)).sum(axis=1)

    signed_funding_pnl = -held * funding
    if funding_adverse:
        funding_effect = signed_funding_pnl.where(
            signed_funding_pnl < 0,
            signed_funding_pnl * 0.5,
        ).where(
            signed_funding_pnl >= 0,
            signed_funding_pnl * 1.5,
        )
        funding_pnl = funding_effect.sum(axis=1)
    else:
        funding_pnl = signed_funding_pnl.sum(axis=1)

    turnover = weights.fillna(0.0).diff().abs().sum(axis=1).fillna(weights.abs().sum(axis=1))
    costs = turnover * (spec.one_way_cost_bps * cost_multiplier / 10000.0)
    returns = price_pnl + funding_pnl - costs
    return {
        "returns": returns,
        "weights": weights,
        "performance": performance(returns).to_dict(),
        "decisions_per_month": decisions_per_month(weights),
        "liquidated": bool((returns <= -1.0).any()),
        "average_monthly_turnover": float(turnover.groupby([turnover.index.year, turnover.index.month]).sum().mean()),
    }


def phase_sweep_execution(
    data: ReplayData,
    spec: CandidateSpec,
    *,
    interval_hours: int,
    l1_band: float,
) -> dict[str, float]:
    out: dict[str, float] = {}
    for anchor in range(24):
        result = run_execution(
            data,
            spec,
            interval_hours=interval_hours,
            l1_band=l1_band,
            anchor_hour=anchor,
        )
        out[str(anchor)] = float(result["performance"]["cagr"])
    return out


def period_metrics(split: ResearchSplit, returns: pd.Series) -> dict[str, dict[str, float | int]]:
    return {
        "discovery": performance(split.discovery_slice(returns)).to_dict(),
        "validation_2023": performance(split.validation_1_slice(returns)).to_dict(),
        "validation_2024": performance(split.validation_2_slice(returns)).to_dict(),
        "pre_holdout": performance(split.pre_holdout_slice(returns)).to_dict(),
    }


def robust_score(periods: dict[str, dict], decisions: float, monthly_turnover: float) -> float:
    cagrs = [
        float(periods["discovery"]["cagr"]),
        float(periods["validation_2023"]["cagr"]),
        float(periods["validation_2024"]["cagr"]),
    ]
    pre = periods["pre_holdout"]
    return (
        0.40 * min(cagrs)
        + 0.20 * (sum(cagrs) / 3.0)
        + 0.40 * float(pre["cagr"])
        - max(0.0, abs(float(pre["max_drawdown"])) - 0.35) * 6.0
        - sum(max(0.0, -x) for x in cagrs) * 6.0
        - max(0.0, 10.0 - decisions) * 0.02
        - max(0.0, monthly_turnover - 8.0) * 0.003
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max-symbols", type=int, default=12)
    p.add_argument("--cache-dir", default=".cache/cryptoai")
    p.add_argument("--bootstrap-samples", type=int, default=2000)
    p.add_argument("--report", default="reports/execution_hysteresis.json")
    args = p.parse_args()

    split = ResearchSplit()
    symbols, universe_meta = select_discovery_universe(args.max_symbols, existed_by="2021-01")
    data = load_universe(symbols, split.discovery_start, "2024-12-31", Path(args.cache_dir))

    rows: list[dict[str, object]] = []
    for risk in RISK_PROFILES:
        for conflict_scale in CONFLICT_SCALES:
            for interval_hours in INTERVALS:
                for l1_band in L1_BANDS:
                    spec = CandidateSpec(
                        core_model="momentum",
                        core_scope="btc_eth",
                        horizons_days=(90, 120, 180),
                        trend_filter_mode="agreement",
                        trend_fast_horizons_days=(20, 40, 60),
                        trend_conflict_scale=conflict_scale,
                        volatility_shock_mode="ratio",
                        volatility_shock_short_days=14,
                        volatility_shock_long_days=60,
                        volatility_shock_threshold=1.25,
                        volatility_shock_scale=0.50,
                        carry_base_allocation=0.0,
                        carry_dominant_allocation=0.0,
                        target_volatility=risk["target_volatility"],
                        max_gross_leverage=risk["max_gross_leverage"],
                        max_single_weight=risk["max_single_weight"],
                    )
                    result = run_execution(
                        data,
                        spec,
                        interval_hours=interval_hours,
                        l1_band=l1_band,
                    )
                    split.assert_selection_index_is_pre_holdout(result["returns"].index)
                    periods = period_metrics(split, result["returns"])
                    decisions = float(result["decisions_per_month"])
                    turnover = float(result["average_monthly_turnover"])
                    selection_cagrs = [
                        float(periods["discovery"]["cagr"]),
                        float(periods["validation_2023"]["cagr"]),
                        float(periods["validation_2024"]["cagr"]),
                    ]
                    rows.append({
                        "spec": asdict(spec),
                        "interval_hours": interval_hours,
                        "l1_band": l1_band,
                        "score": robust_score(periods, decisions, turnover),
                        "positive_all_selection_periods": all(x > 0.0 for x in selection_cagrs),
                        "decisions_per_month": decisions,
                        "average_monthly_turnover": turnover,
                        "periods": periods,
                    })

    rows.sort(key=lambda x: float(x["score"]), reverse=True)

    stress_rows: list[dict[str, object]] = []
    for row in rows[:18]:
        spec = CandidateSpec(**row["spec"])
        interval = int(row["interval_hours"])
        band = float(row["l1_band"])
        base = run_execution(data, spec, interval_hours=interval, l1_band=band)
        severe = run_execution(data, spec, interval_hours=interval, l1_band=band, cost_multiplier=3.0)
        delayed = run_execution(data, replace(spec, execution_delay_hours=3), interval_hours=interval, l1_band=band)
        adverse = run_execution(data, spec, interval_hours=interval, l1_band=band, funding_adverse=True)
        base_pre = performance(split.pre_holdout_slice(base["returns"])).to_dict()
        severe_pre = performance(split.pre_holdout_slice(severe["returns"])).to_dict()
        delayed_pre = performance(split.pre_holdout_slice(delayed["returns"])).to_dict()
        adverse_pre = performance(split.pre_holdout_slice(adverse["returns"])).to_dict()
        liquidated = bool(base["liquidated"] or severe["liquidated"] or delayed["liquidated"] or adverse["liquidated"])
        worst_cagr = min(
            float(base_pre["cagr"]), float(severe_pre["cagr"]),
            float(delayed_pre["cagr"]), float(adverse_pre["cagr"]),
        )
        worst_dd = min(
            float(base_pre["max_drawdown"]), float(severe_pre["max_drawdown"]),
            float(delayed_pre["max_drawdown"]), float(adverse_pre["max_drawdown"]),
        )
        stage2 = (
            row["positive_all_selection_periods"]
            and float(base_pre["cagr"]) >= 0.49
            and float(base_pre["max_drawdown"]) >= -0.36
            and float(severe_pre["cagr"]) >= 0.34
            and float(delayed_pre["cagr"]) >= 0.40
            and float(adverse_pre["cagr"]) >= 0.35
            and float(row["decisions_per_month"]) >= 9.5
            and not liquidated
        )
        stress_rows.append({
            **row,
            "base_pre_holdout": base_pre,
            "severe_cost_pre_holdout": severe_pre,
            "delay_3h_pre_holdout": delayed_pre,
            "adverse_funding_pre_holdout": adverse_pre,
            "worst_stress_cagr": worst_cagr,
            "worst_stress_drawdown": worst_dd,
            "stage2_screen_passed": stage2,
            "stress_score": worst_cagr - max(0.0, abs(worst_dd) - 0.35) * 3.0,
            "liquidated": liquidated,
        })

    stress_rows.sort(key=lambda x: float(x["stress_score"]), reverse=True)
    finalists = [x for x in stress_rows if x["stage2_screen_passed"]][:4]
    if not finalists and stress_rows:
        finalists = stress_rows[:3]

    finalist_reports: list[dict[str, object]] = []
    for row in finalists:
        spec = CandidateSpec(**row["spec"])
        interval = int(row["interval_hours"])
        band = float(row["l1_band"])
        base = run_execution(data, spec, interval_hours=interval, l1_band=band)
        phases = phase_sweep_execution(data, spec, interval_hours=interval, l1_band=band)
        phase_min = min(phases.values()) if phases else -1.0
        ruin = block_bootstrap_ruin_probability(
            split.pre_holdout_slice(base["returns"]),
            samples=args.bootstrap_samples,
        )
        gate_inputs = {
            "base_cagr": row["base_pre_holdout"]["cagr"],
            "max_drawdown": row["base_pre_holdout"]["max_drawdown"],
            "severe_cost_cagr": row["severe_cost_pre_holdout"]["cagr"],
            "delay_3h_cagr": row["delay_3h_pre_holdout"]["cagr"],
            "decisions_per_month": row["decisions_per_month"],
            "bootstrap_ruin_probability": ruin,
            "phase_min_cagr": phase_min,
            "liquidated": row["liquidated"],
        }
        finalist_reports.append({
            **row,
            "phase_cagrs": phases,
            "phase_min_cagr": phase_min,
            "bootstrap_ruin_probability": ruin,
            "frozen_gate_shape_pre_holdout_only": PromotionGates().report(gate_inputs),
            "promotion_allowed": False,
            "promotion_note": "Pre-holdout only. Maintenance-margin and independent survivorship stresses remain before holdout.",
        })

    report = {
        "status": "EXECUTION_HYSTERESIS_PRE_HOLDOUT_ONLY",
        "selection_boundary": "No data from 2025-01-01 onward was loaded or used.",
        "hypothesis": "Evaluate the same slow-trend edge more frequently while using causal L1 hysteresis to reject micro-rebalances and improve return per unit turnover.",
        "universe_selection": {
            "cutoff": "2021-01",
            "selection_fields_used": ["first_month", "symbol"],
            "future_status_metadata_used_for_selection": False,
            "requested_max_symbols": args.max_symbols,
            "loaded_symbols": list(data.close.columns),
            "metadata_for_audit_only": universe_meta,
        },
        "tested_candidates": len(rows),
        "top_selection_candidates": rows[:24],
        "stress_candidates": stress_rows,
        "finalists_pre_holdout": finalist_reports,
    }

    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    best = stress_rows[0] if stress_rows else None
    print(json.dumps({
        "status": report["status"],
        "tested_candidates": len(rows),
        "best_interval_hours": best["interval_hours"] if best else None,
        "best_l1_band": best["l1_band"] if best else None,
        "best_base_cagr": best["base_pre_holdout"]["cagr"] if best else None,
        "best_base_max_drawdown": best["base_pre_holdout"]["max_drawdown"] if best else None,
        "best_severe_cost_cagr": best["severe_cost_pre_holdout"]["cagr"] if best else None,
        "best_delay_3h_cagr": best["delay_3h_pre_holdout"]["cagr"] if best else None,
        "best_decisions_per_month": best["decisions_per_month"] if best else None,
        "best_monthly_turnover": best["average_monthly_turnover"] if best else None,
        "stage2_passers": sum(1 for x in stress_rows if x["stage2_screen_passed"]),
        "report": str(path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
