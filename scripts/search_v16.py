from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.allocator import (
    convex_equity_overlay,
    multihorizon_two_sleeve_targets,
)
from cryptoai_v13.data import point_in_time_liquid_view
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from cryptoai_v13.signals import StrategySpec, build_targets
from cryptoai_v13.v16 import (
    _cap_gross,
    AdaptiveTrendSpec,
    ConvexCaptureSpec,
    CrossSectionalMomentumSpec,
    FundingCarrySpec,
    RegimeSwitchSpec,
    adaptive_equity_shield,
    adaptive_trend_targets,
    combine_convex_with_core,
    convex_capture_targets,
    cross_sectional_momentum_targets,
    funding_carry_targets,
    performance_gated_alpha_targets,
    drawdown_regime_reentry_targets,
    regime_switch_targets,
    regime_hedged_targets,
    rolling_loss_limiter_targets,
    three_regime_sleeve_targets,
    volatility_managed_targets,
)
from paper_once_v13 import cap_targets
from run_final_candidate import build_candidate


REPORT_PATH = PROJECT / "reports" / "v16_research_gate.json"
START = "2021-01-01"


def maximum_drawdown(equity: pd.Series) -> float:
    equity = equity.dropna()
    return float(equity.div(equity.cummax()).sub(1.0).min()) if len(equity) else 0.0


def period_metrics(equity: pd.Series, start: str, end: str | None = None) -> dict:
    start_at = pd.Timestamp(start)
    start_at = (
        start_at.tz_localize("UTC")
        if start_at.tzinfo is None
        else start_at.tz_convert("UTC")
    )
    end_at = None
    if end is not None:
        end_at = pd.Timestamp(end)
        end_at = (
            end_at.tz_localize("UTC")
            if end_at.tzinfo is None
            else end_at.tz_convert("UTC")
        )
    selected = equity.loc[
        (equity.index >= start_at)
        & (True if end_at is None else equity.index <= end_at)
    ].dropna()
    if len(selected) < 2:
        return {"return": 0.0, "cagr": 0.0, "max_drawdown": 0.0}
    selected = selected / selected.iloc[0]
    hours = max((selected.index[-1] - selected.index[0]).total_seconds() / 3600, 1.0)
    total = float(selected.iloc[-1] - 1.0)
    cagr = float(selected.iloc[-1] ** ((365.25 * 24) / hours) - 1.0)
    daily = selected.resample("D").last().pct_change().dropna()
    monthly = selected.resample("ME").last().pct_change().dropna()
    positive = daily.clip(lower=0.0)
    best = daily.nlargest(min(3, len(daily)))
    without_best = daily.drop(index=best.index[:1])
    rolling_90 = selected.resample("ME").last().pct_change(3).dropna()
    return {
        "return": total,
        "cagr": cagr,
        "max_drawdown": maximum_drawdown(selected),
        "positive_month_ratio": float((monthly > 0.0).mean()) if len(monthly) else 0.0,
        "positive_rolling_90d_ratio": float((rolling_90 > 0.0).mean()) if len(rolling_90) else 0.0,
        "without_best_day_return": float((1.0 + without_best).prod() - 1.0),
        "top3_positive_day_share": (
            float(best.clip(lower=0.0).sum() / positive.sum())
            if positive.sum() > 0.0 else 1.0
        ),
        "days_over_3pct": int((daily >= 0.03).sum()),
        "days_over_5pct": int((daily >= 0.05).sum()),
        "days_over_8pct": int((daily >= 0.08).sum()),
        "best_day": float(daily.max()) if len(daily) else 0.0,
        "worst_day": float(daily.min()) if len(daily) else 0.0,
        "days": int(len(daily)),
    }


def profile(equity: pd.Series, latest: pd.Timestamp) -> dict:
    end = latest.isoformat()
    return {
        "full": period_metrics(equity, START, end),
        "old": period_metrics(equity, "2021-01-01", "2023-12-31 23:00"),
        "validation": period_metrics(equity, "2024-01-01", "2024-12-31 23:00"),
        "recent": period_metrics(equity, "2025-01-01", end),
        "current": period_metrics(equity, "2026-01-01", end),
    }


def robustness_gate(row: dict, benchmark_recent_cagr: float) -> dict[str, bool]:
    p = row["profile"]
    return {
        "positive_old_market_regimes": p["old"]["return"] > 0.0,
        "positive_2024_validation": p["validation"]["return"] > 0.0,
        "positive_2025_plus_recent": p["recent"]["return"] > 0.0,
        "positive_2026_recent": p["current"]["return"] > 0.0,
        "recent_cagr_beats_existing_benchmark": p["recent"]["cagr"] > benchmark_recent_cagr,
        "full_drawdown_no_worse_than_30pct": p["full"]["max_drawdown"] >= -0.30,
        "recent_drawdown_no_worse_than_20pct": p["recent"]["max_drawdown"] >= -0.20,
        "current_drawdown_no_worse_than_15pct": p["current"]["max_drawdown"] >= -0.15,
        "recent_profitable_without_best_day": p["recent"]["without_best_day_return"] > 0.0,
        "current_profitable_without_best_day": p["current"]["without_best_day_return"] > 0.0,
        "recent_top3_days_below_55pct_of_positive_pnl": p["recent"]["top3_positive_day_share"] < 0.55,
        "recent_majority_positive_rolling_90d": p["recent"]["positive_rolling_90d_ratio"] >= 0.55,
        "recent_majority_positive_months": p["recent"]["positive_month_ratio"] >= 0.55,
    }


def score_row(row: dict) -> float:
    p = row["profile"]
    recent, current, full = p["recent"], p["current"], p["full"]
    large_day_score = (
        current["days_over_3pct"]
        + 2.0 * current["days_over_5pct"]
        + 4.0 * current["days_over_8pct"]
    ) / max(current["days"], 1)
    return float(
        0.42 * recent["cagr"]
        + 0.38 * current["cagr"]
        + 0.20 * full["cagr"]
        + 2.0 * large_day_score
        - 0.30 * abs(recent["max_drawdown"])
        - 0.20 * recent["top3_positive_day_share"]
    )


def main() -> None:
    finalist = json.loads(
        (PROJECT / "config" / "candidate_v13_circuit_breaker.json").read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    data, core_targets, _, _ = build_candidate(base_config)
    core_targets = cap_targets(core_targets, finalist["target_cap"])
    universe = base_config["point_in_time_universe"]
    signal_data, _ = point_in_time_liquid_view(
        data,
        top_n=universe["top_n"],
        lookback_hours=universe["quote_volume_lookback_hours"],
        minimum_history_hours=universe["minimum_history_hours"],
    )
    execution = base_config["execution"]
    latest = data.close.index[-1]

    core_result = screen(data, core_targets, execution["base_cost_per_side"])
    v14_config = json.loads(
        (PROJECT / "config" / "candidate_v14_max_capture.json").read_text()
    )
    v14_raw = build_targets(
        signal_data, StrategySpec(**v14_config["opportunity"]["spec"])
    )
    v14_targets, _ = additive_opportunity_targets(
        core_targets,
        v14_raw,
        OpportunityBudget(
            v14_config["allocation"]["maximum_overlay_gross"],
            v14_config["allocation"]["maximum_portfolio_gross"],
        ),
    )
    v14_result = screen(data, v14_targets, execution["base_cost_per_side"])
    benchmarks = {
        "v13_core": profile(core_result.equity, latest),
        "v14": profile(v14_result.equity, latest),
    }
    benchmark_recent_cagr = max(
        benchmarks["v13_core"]["recent"]["cagr"],
        benchmarks["v14"]["recent"]["cagr"],
    )

    # Independent alpha family inspired by recent out-of-sample evidence for
    # intermediate-frequency crypto trend following.  We retain only the
    # structural ideas (H6, rolling quality selection, asymmetric long/short,
    # volatility-aware trailing exits) and validate them on our own PIT data.
    adaptive_trend_specs = {
        "h6_fast": AdaptiveTrendSpec(
            momentum_bars=4,
            entry_threshold=0.025,
            atr_multiplier=2.0,
            long_count=4,
            short_count=2,
            long_sharpe_threshold=0.4,
            short_sharpe_threshold=0.7,
            maximum_gross=1.90,
        ),
        "h6_balanced": AdaptiveTrendSpec(),
        "h6_selective": AdaptiveTrendSpec(
            momentum_bars=8,
            entry_threshold=0.045,
            atr_multiplier=2.5,
            long_count=3,
            short_count=2,
            long_sharpe_threshold=1.0,
            short_sharpe_threshold=1.3,
            maximum_gross=1.95,
        ),
        "h6_persistent": AdaptiveTrendSpec(
            momentum_bars=20,
            entry_threshold=0.065,
            atr_multiplier=3.0,
            long_count=5,
            short_count=3,
            long_sharpe_threshold=0.5,
            short_sharpe_threshold=0.9,
            maximum_gross=1.85,
        ),
    }

    center = ConvexCaptureSpec()
    specs = {
        "balanced": center,
        "fast_selective": replace(
            center,
            fast_lookback=12,
            slow_lookback=48,
            top_n=1,
            fast_threshold=0.010,
            slow_threshold=0.020,
            fast_volume_multiple=1.75,
            slow_volume_multiple=1.40,
            fast_weight=0.55,
            slow_weight=0.30,
            trend_weight=0.15,
            fast_max_holding_hours=72,
            slow_max_holding_hours=168,
        ),
        "trend_convex": replace(
            center,
            fast_lookback=24,
            slow_lookback=168,
            fast_threshold=0.015,
            slow_threshold=0.035,
            fast_volume_multiple=1.35,
            slow_volume_multiple=1.15,
            fast_weight=0.35,
            slow_weight=0.30,
            trend_weight=0.35,
            trailing_stop=0.18,
            slow_max_holding_hours=336,
        ),
        "high_conviction": replace(
            center,
            top_n=1,
            fast_threshold=0.018,
            slow_threshold=0.035,
            fast_volume_multiple=2.0,
            slow_volume_multiple=1.5,
            aligned_multiplier=1.50,
            countertrend_multiplier=0.20,
            minimum_conviction=0.45,
            maximum_conviction=1.60,
        ),
    }
    generated = {
        name: convex_capture_targets(signal_data, spec)[0]
        for name, spec in specs.items()
    }
    rows: list[dict[str, object]] = []
    targets_by_id: dict[str, pd.DataFrame] = {}
    cross_sectional_specs = {
        "fast_relative": CrossSectionalMomentumSpec(
            lookback_hours=24 * 3,
            volatility_hours=24 * 7,
            rebalance_hours=6,
            long_count=3,
            short_count=3,
            minimum_momentum=0.025,
            maximum_gross=1.85,
        ),
        "balanced_relative": CrossSectionalMomentumSpec(),
        "persistent_relative": CrossSectionalMomentumSpec(
            lookback_hours=24 * 14,
            volatility_hours=24 * 21,
            rebalance_hours=24,
            long_count=3,
            short_count=3,
            minimum_momentum=0.07,
            maximum_gross=1.85,
        ),
        "reversal_24h": CrossSectionalMomentumSpec(
            lookback_hours=24,
            volatility_hours=24 * 7,
            rebalance_hours=3,
            long_count=3,
            short_count=3,
            minimum_momentum=0.015,
            direction="reversal",
            maximum_gross=1.35,
        ),
        "reversal_72h": CrossSectionalMomentumSpec(
            lookback_hours=72,
            volatility_hours=24 * 10,
            rebalance_hours=6,
            long_count=4,
            short_count=4,
            minimum_momentum=0.03,
            direction="reversal",
            maximum_gross=1.35,
        ),
        "reversal_168h": CrossSectionalMomentumSpec(
            lookback_hours=168,
            volatility_hours=24 * 14,
            rebalance_hours=12,
            long_count=3,
            short_count=3,
            minimum_momentum=0.05,
            direction="reversal",
            maximum_gross=1.35,
        ),
    }
    cross_sectional_targets: dict[str, pd.DataFrame] = {}
    for name, cross_spec in cross_sectional_specs.items():
        targets, diagnostics = cross_sectional_momentum_targets(
            signal_data, cross_spec
        )
        candidate_id = f"cross_sectional:{name}"
        cross_sectional_targets[name] = targets
        targets_by_id[candidate_id] = targets
        result = screen(data, targets, execution["base_cost_per_side"])
        row = {
            "candidate_id": candidate_id,
            "family": (
                "cross_sectional_reversal"
                if cross_spec.direction == "reversal"
                else "cross_sectional_long_short"
            ),
            "name": name,
            "spec": cross_spec.to_dict(),
            "maximum_portfolio_gross": cross_spec.maximum_gross,
            "average_gross": float(diagnostics["gross"].mean()),
            "average_long_positions": float(
                diagnostics["long_positions"].mean()
            ),
            "average_short_positions": float(
                diagnostics["short_positions"].mean()
            ),
            "profile": profile(result.equity, latest),
        }
        row["gate"] = robustness_gate(row, benchmark_recent_cagr)
        row["screen_gate_passed"] = all(row["gate"].values())
        row["score"] = score_row(row)
        rows.append(row)
    funding_specs = {
        "carry_3d": FundingCarrySpec(
            funding_lookback_hours=24 * 3,
            volatility_hours=24 * 7,
            trend_hours=24,
            rebalance_hours=8,
            long_count=3,
            short_count=3,
            minimum_absolute_funding=0.0005,
            maximum_adverse_trend=0.08,
            maximum_gross=1.25,
        ),
        "carry_7d": FundingCarrySpec(),
        "carry_14d": FundingCarrySpec(
            funding_lookback_hours=24 * 14,
            volatility_hours=24 * 21,
            trend_hours=24 * 7,
            rebalance_hours=24,
            long_count=3,
            short_count=3,
            minimum_absolute_funding=0.002,
            maximum_adverse_trend=0.15,
            maximum_gross=1.25,
        ),
        "confirmed_carry_3d": FundingCarrySpec(
            funding_lookback_hours=24 * 3,
            volatility_hours=24 * 10,
            trend_hours=24 * 3,
            rebalance_hours=8,
            long_count=3,
            short_count=3,
            minimum_absolute_funding=0.0005,
            minimum_trend=0.02,
            signal_mode="confirmed_carry",
            maximum_gross=1.35,
        ),
        "confirmed_carry_7d": FundingCarrySpec(
            funding_lookback_hours=24 * 7,
            volatility_hours=24 * 14,
            trend_hours=24 * 7,
            rebalance_hours=8,
            long_count=3,
            short_count=3,
            minimum_absolute_funding=0.001,
            minimum_trend=0.04,
            signal_mode="confirmed_carry",
            maximum_gross=1.35,
        ),
        "pressure_3d": FundingCarrySpec(
            funding_lookback_hours=24 * 3,
            volatility_hours=24 * 10,
            trend_hours=24 * 3,
            rebalance_hours=8,
            long_count=3,
            short_count=3,
            minimum_absolute_funding=0.0005,
            minimum_trend=0.03,
            signal_mode="pressure_momentum",
            maximum_gross=1.50,
        ),
        "pressure_7d": FundingCarrySpec(
            funding_lookback_hours=24 * 7,
            volatility_hours=24 * 14,
            trend_hours=24 * 7,
            rebalance_hours=8,
            long_count=3,
            short_count=3,
            minimum_absolute_funding=0.001,
            minimum_trend=0.05,
            signal_mode="pressure_momentum",
            maximum_gross=1.50,
        ),
    }
    funding_targets_by_name: dict[str, pd.DataFrame] = {}
    for name, carry_spec in funding_specs.items():
        targets, diagnostics = funding_carry_targets(signal_data, carry_spec)
        candidate_id = f"funding:{name}"
        funding_targets_by_name[name] = targets
        targets_by_id[candidate_id] = targets
        result = screen(data, targets, execution["base_cost_per_side"])
        row = {
            "candidate_id": candidate_id,
            "family": (
                "market_neutral_funding_carry"
                if carry_spec.signal_mode == "carry"
                else "funding_price_confirmation"
            ),
            "name": name,
            "spec": carry_spec.to_dict(),
            "maximum_portfolio_gross": carry_spec.maximum_gross,
            "average_gross": float(diagnostics["gross"].mean()),
            "average_long_positions": float(diagnostics["long_positions"].mean()),
            "average_short_positions": float(diagnostics["short_positions"].mean()),
            "profile": profile(result.equity, latest),
        }
        row["gate"] = robustness_gate(row, benchmark_recent_cagr)
        row["screen_gate_passed"] = all(row["gate"].values())
        row["score"] = score_row(row)
        rows.append(row)
    for name, spec in adaptive_trend_specs.items():
        targets, diagnostics = adaptive_trend_targets(signal_data, spec)
        candidate_id = f"adaptive_trend:{name}"
        targets_by_id[candidate_id] = targets
        result = screen(data, targets, execution["base_cost_per_side"])
        row = {
            "candidate_id": candidate_id,
            "family": "adaptive_h6_trend",
            "name": name,
            "spec": spec.to_dict(),
            "maximum_portfolio_gross": spec.maximum_gross,
            "average_gross": float(diagnostics["gross"].mean()),
            "average_long_positions": float(diagnostics["long_positions"].mean()),
            "average_short_positions": float(diagnostics["short_positions"].mean()),
            "profile": profile(result.equity, latest),
        }
        row["gate"] = robustness_gate(row, benchmark_recent_cagr)
        row["screen_gate_passed"] = all(row["gate"].values())
        row["score"] = score_row(row)
        rows.append(row)
    for name, spec in specs.items():
        for core_fraction in (0.15, 0.30, 0.45):
            for maximum_gross in (1.35, 1.60, 1.85):
                targets, allocated = combine_convex_with_core(
                    core_targets,
                    generated[name],
                    core_fraction=core_fraction,
                    maximum_portfolio_gross=maximum_gross,
                )
                result = screen(data, targets, execution["base_cost_per_side"])
                candidate_id = f"convex:{name}:{core_fraction}:{maximum_gross}"
                targets_by_id[candidate_id] = targets
                row = {
                    "candidate_id": candidate_id,
                    "family": "multi_speed_convex_capture",
                    "name": name,
                    "spec": spec.to_dict(),
                    "core_fraction": core_fraction,
                    "maximum_portfolio_gross": maximum_gross,
                    "allocated_opportunity_average_gross": float(
                        allocated.abs().sum(axis=1).mean()
                    ),
                    "profile": profile(result.equity, latest),
                }
                row["gate"] = robustness_gate(row, benchmark_recent_cagr)
                row["screen_gate_passed"] = all(row["gate"].values())
                row["score"] = score_row(row)
                rows.append(row)

    # The second V16 family treats V13 as the defensive champion and V14 as
    # the aggressive champion.  It allocates only from their already-realized,
    # closed hourly returns.  This retains V14's large-day engine while moving
    # capital back to V13 when V14 stops leading across several horizons.
    core_returns = core_result.equity.pct_change().fillna(0.0)
    v14_returns = v14_result.equity.pct_change().fillna(0.0)
    champion_windows = (
        (21, 45, 90),
        (30, 60, 120),
        (45, 90, 180),
    )
    champion_weights = (
        (0.80, 0.20),
        (0.70, 0.10),
        (0.90, 0.35),
    )
    convex_overlays = (
        {
            "name": "measured",
            "winner": 1.15,
            "loser": 0.60,
            "drawdown": 0.35,
            "threshold": 0.10,
            "maximum_gross": 1.65,
        },
        {
            "name": "attack",
            "winner": 1.30,
            "loser": 0.50,
            "drawdown": 0.30,
            "threshold": 0.12,
            "maximum_gross": 1.85,
        },
    )
    for windows in champion_windows:
        for core_leading, core_lagging in champion_weights:
            mixed = multihorizon_two_sleeve_targets(
                core_targets,
                v14_targets,
                core_returns,
                v14_returns,
                windows_days=windows,
                funding_weight_when_leading=core_leading,
                funding_weight_when_lagging=core_lagging,
                rebalance_hours=24,
            )
            proxy = screen(data, mixed, execution["base_cost_per_side"])
            for overlay in convex_overlays:
                targets = convex_equity_overlay(
                    mixed,
                    proxy.equity,
                    short_hours=72,
                    long_hours=24 * 30,
                    drawdown_hours=24 * 30,
                    drawdown_threshold=overlay["threshold"],
                    winner_multiplier=overlay["winner"],
                    loser_multiplier=overlay["loser"],
                    drawdown_multiplier=overlay["drawdown"],
                    rebalance_hours=24,
                    maximum_gross=overlay["maximum_gross"],
                )
                candidate_id = (
                    f"champion:{'-'.join(map(str, windows))}:"
                    f"{core_leading}:{core_lagging}:{overlay['name']}"
                )
                targets_by_id[candidate_id] = targets
                result = screen(data, targets, execution["base_cost_per_side"])
                row = {
                    "candidate_id": candidate_id,
                    "family": "adaptive_v13_v14_champion",
                    "name": overlay["name"],
                    "windows_days": list(windows),
                    "core_weight_when_leading": core_leading,
                    "core_weight_when_lagging": core_lagging,
                    "convex_overlay": overlay,
                    "maximum_portfolio_gross": overlay["maximum_gross"],
                    "profile": profile(result.equity, latest),
                }
                row["gate"] = robustness_gate(row, benchmark_recent_cagr)
                row["screen_gate_passed"] = all(row["gate"].values())
                row["score"] = score_row(row)
                rows.append(row)

    # A regime allocator addresses the specific failure seen in V14/V15:
    # attack exposure remained high when the broad market stopped supporting
    # it.  This family keeps the proven large-day sleeve intact in confirmed
    # bull regimes, blends toward V13 in neutral markets, and defends after a
    # broad downtrend or a fast BTC shock.  Only a small structural grid is
    # tested; recent periods still have no special-case dates or overrides.
    regime_specs = {
        "responsive": RegimeSwitchSpec(
            momentum_hours=24 * 30,
            bull_momentum=0.05,
            bear_momentum=-0.06,
            bull_breadth=0.54,
            bear_breadth=0.46,
            shock_return=-0.08,
            neutral_attack=0.80,
            bear_attack=0.25,
            neutral_core=0.45,
        ),
        "balanced": RegimeSwitchSpec(),
        "selective": RegimeSwitchSpec(
            momentum_hours=24 * 60,
            bull_momentum=0.12,
            bear_momentum=-0.10,
            bull_breadth=0.58,
            bear_breadth=0.42,
            shock_return=-0.12,
            neutral_attack=0.60,
            bear_attack=0.10,
            neutral_core=0.70,
        ),
    }
    regime_sources = (
        "champion:45-90-180:0.7:0.1:attack",
        "champion:45-90-180:0.8:0.2:attack",
    )
    regime_diagnostics_by_id: dict[str, pd.DataFrame] = {}
    for source_id in regime_sources:
        for name, regime_spec in regime_specs.items():
            targets, diagnostics = regime_switch_targets(
                core_targets,
                targets_by_id[source_id],
                signal_data.close,
                regime_spec,
            )
            candidate_id = f"regime:{source_id}:{name}"
            targets_by_id[candidate_id] = targets
            regime_diagnostics_by_id[candidate_id] = diagnostics
            result = screen(data, targets, execution["base_cost_per_side"])
            counts = diagnostics["regime"].value_counts(normalize=True)
            row = {
                "candidate_id": candidate_id,
                "family": "regime_switched_champion",
                "name": name,
                "source_candidate_id": source_id,
                "regime_spec": regime_spec.to_dict(),
                "maximum_portfolio_gross": regime_spec.maximum_gross,
                "regime_share": {
                    key: float(counts.get(key, 0.0))
                    for key in ("bull", "neutral", "bear")
                },
                "profile": profile(result.equity, latest),
            }
            row["gate"] = robustness_gate(row, benchmark_recent_cagr)
            row["screen_gate_passed"] = all(row["gate"].values())
            row["score"] = score_row(row)
            rows.append(row)

    # Re-entry-aware protection keeps the large-day regime allocator intact
    # until its own closed proxy loses a controlled amount.  It then remains
    # defensive until both market regime and proxy recovery confirm a return
    # to attack.  This avoids the permanent low-exposure trap observed in the
    # equity-recovery-only family.
    reentry_profiles = (
        {
            "name": "fast_reentry",
            "drawdown_threshold": 0.07,
            "defensive_multiplier": 0.20,
            "reentry_return_hours": 24 * 7,
            "reentry_return": 0.02,
            "minimum_defensive_hours": 24 * 5,
            "rebalance_hours": 24,
            "maximum_gross": 1.85,
        },
        {
            "name": "balanced_reentry",
            "drawdown_threshold": 0.08,
            "defensive_multiplier": 0.25,
            "reentry_return_hours": 24 * 14,
            "reentry_return": 0.03,
            "minimum_defensive_hours": 24 * 7,
            "rebalance_hours": 24,
            "maximum_gross": 1.85,
        },
        {
            "name": "patient_reentry",
            "drawdown_threshold": 0.10,
            "defensive_multiplier": 0.35,
            "reentry_return_hours": 24 * 21,
            "reentry_return": 0.04,
            "minimum_defensive_hours": 24 * 10,
            "rebalance_hours": 24,
            "maximum_gross": 1.85,
        },
    )
    reentry_sources = (
        "regime:champion:45-90-180:0.7:0.1:attack:balanced",
        "regime:champion:45-90-180:0.8:0.2:attack:balanced",
    )
    for source_id in reentry_sources:
        proxy = screen(
            data,
            targets_by_id[source_id],
            execution["base_cost_per_side"],
        )
        source_regime = regime_diagnostics_by_id[source_id]["regime"]
        for shield in reentry_profiles:
            targets, diagnostics = drawdown_regime_reentry_targets(
                targets_by_id[source_id],
                proxy.equity,
                source_regime,
                **{key: value for key, value in shield.items() if key != "name"},
            )
            candidate_id = f"reentry:{source_id}:{shield['name']}"
            targets_by_id[candidate_id] = targets
            result = screen(data, targets, execution["base_cost_per_side"])
            row = {
                "candidate_id": candidate_id,
                "family": "regime_reentry_champion",
                "name": shield["name"],
                "source_candidate_id": source_id,
                "reentry_shield": shield,
                "maximum_portfolio_gross": shield["maximum_gross"],
                "defensive_share": float(
                    diagnostics["risk_state"].eq("defensive").mean()
                ),
                "risk_guard": {
                    "name": "targets_own_state",
                    "threshold": 0.99,
                    "multiplier": 1.0,
                    "recovery": None,
                    "cooldown_hours": 1,
                },
                "profile": profile(result.equity, latest),
            }
            row["gate"] = robustness_gate(row, benchmark_recent_cagr)
            row["screen_gate_passed"] = all(row["gate"].values())
            row["score"] = score_row(row)
            rows.append(row)

    # The first re-entry family stayed defensive for most of the history.
    # This refinement applies the same causal state machine directly to the
    # unblended attack sleeve, reacts at intraday cadence, and permits a new
    # attack cycle after a short but confirmed bull recovery.
    rapid_reentry_profiles = (
        {
            "name": "intraday_4pct",
            "drawdown_threshold": 0.04,
            "defensive_multiplier": 0.05,
            "reentry_return_hours": 24,
            "reentry_return": 0.005,
            "minimum_defensive_hours": 24,
            "rebalance_hours": 3,
            "maximum_gross": 1.85,
            "require_bull_regime": False,
        },
        {
            "name": "fast_5pct",
            "drawdown_threshold": 0.05,
            "defensive_multiplier": 0.10,
            "reentry_return_hours": 72,
            "reentry_return": 0.010,
            "minimum_defensive_hours": 36,
            "rebalance_hours": 3,
            "maximum_gross": 1.85,
            "require_bull_regime": False,
        },
        {
            "name": "weekly_6pct",
            "drawdown_threshold": 0.06,
            "defensive_multiplier": 0.15,
            "reentry_return_hours": 24 * 7,
            "reentry_return": 0.015,
            "minimum_defensive_hours": 72,
            "rebalance_hours": 6,
            "maximum_gross": 1.85,
            "require_bull_regime": False,
        },
    )
    for source_id in regime_sources:
        proxy = screen(
            data,
            targets_by_id[source_id],
            execution["base_cost_per_side"],
        )
        source_regime = regime_diagnostics_by_id[
            f"regime:{source_id}:balanced"
        ]["regime"]
        for shield in rapid_reentry_profiles:
            targets, diagnostics = drawdown_regime_reentry_targets(
                targets_by_id[source_id],
                proxy.equity,
                source_regime,
                **{key: value for key, value in shield.items() if key != "name"},
            )
            candidate_id = f"rapid_reentry:{source_id}:{shield['name']}"
            targets_by_id[candidate_id] = targets
            result = screen(data, targets, execution["base_cost_per_side"])
            row = {
                "candidate_id": candidate_id,
                "family": "rapid_reentry_attack",
                "name": shield["name"],
                "source_candidate_id": source_id,
                "reentry_shield": shield,
                "maximum_portfolio_gross": shield["maximum_gross"],
                "defensive_share": float(
                    diagnostics["risk_state"].eq("defensive").mean()
                ),
                "risk_guard": {
                    "name": "targets_own_state",
                    "threshold": 0.99,
                    "multiplier": 1.0,
                    "recovery": None,
                    "cooldown_hours": 1,
                },
                "profile": profile(result.equity, latest),
            }
            row["gate"] = robustness_gate(row, benchmark_recent_cagr)
            row["screen_gate_passed"] = all(row["gate"].values())
            row["score"] = score_row(row)
            rows.append(row)

    # Fast rolling loss containment is intentionally separate from a
    # high-water drawdown lock.  It preserves normal and winning exposure,
    # cuts only while the last day/week remains unusually weak, and restores
    # the sleeve automatically as those closed windows recover.
    rolling_limiters = (
        {
            "name": "rapid",
            "short_hours": 24,
            "medium_hours": 24 * 7,
            "short_loss": 0.03,
            "medium_loss": 0.07,
            "short_multiplier": 0.10,
            "medium_multiplier": 0.25,
            "rebalance_hours": 3,
            "maximum_gross": 1.85,
        },
        {
            "name": "balanced",
            "short_hours": 24,
            "medium_hours": 24 * 7,
            "short_loss": 0.04,
            "medium_loss": 0.09,
            "short_multiplier": 0.15,
            "medium_multiplier": 0.35,
            "rebalance_hours": 3,
            "maximum_gross": 1.85,
        },
        {
            "name": "tolerant",
            "short_hours": 24,
            "medium_hours": 24 * 7,
            "short_loss": 0.05,
            "medium_loss": 0.11,
            "short_multiplier": 0.25,
            "medium_multiplier": 0.45,
            "rebalance_hours": 3,
            "maximum_gross": 1.85,
        },
    )
    limiter_sources = (
        "champion:45-90-180:0.7:0.1:attack",
        "champion:45-90-180:0.8:0.2:attack",
    )
    for source_id in limiter_sources:
        proxy = screen(
            data,
            targets_by_id[source_id],
            execution["base_cost_per_side"],
        )
        for limiter in rolling_limiters:
            targets, diagnostics = rolling_loss_limiter_targets(
                targets_by_id[source_id],
                proxy.equity,
                **{key: value for key, value in limiter.items() if key != "name"},
            )
            candidate_id = f"loss_limiter:{source_id}:{limiter['name']}"
            targets_by_id[candidate_id] = targets
            result = screen(data, targets, execution["base_cost_per_side"])
            row = {
                "candidate_id": candidate_id,
                "family": "rolling_loss_limited_champion",
                "name": limiter["name"],
                "source_candidate_id": source_id,
                "loss_limiter": limiter,
                "maximum_portfolio_gross": limiter["maximum_gross"],
                "reduced_exposure_share": float(
                    diagnostics["risk_factor"].lt(1.0).mean()
                ),
                "risk_guard": {
                    "name": "targets_own_state",
                    "threshold": 0.99,
                    "multiplier": 1.0,
                    "recovery": None,
                    "cooldown_hours": 1,
                },
                "profile": profile(result.equity, latest),
            }
            row["gate"] = robustness_gate(row, benchmark_recent_cagr)
            row["screen_gate_passed"] = all(row["gate"].values())
            row["score"] = score_row(row)
            rows.append(row)

    # The prior shields could only reduce a long-heavy book.  This family
    # uses the same causal broad-market regime to add a liquid BTC/ETH hedge,
    # allowing V16 to preserve bull capture while earning or neutralizing risk
    # during confirmed bear regimes.
    hedge_profiles = (
        {"name": "neutralize", "neutral_net_cap": 1.00, "bear_net_target": 0.00},
        {"name": "balanced_short", "neutral_net_cap": 0.75, "bear_net_target": -0.35},
        {"name": "strong_short", "neutral_net_cap": 0.50, "bear_net_target": -0.65},
    )
    hedge_sources = (
        "champion:45-90-180:0.7:0.1:attack",
        "champion:45-90-180:0.8:0.2:attack",
    )
    for source_id in hedge_sources:
        # Use the balanced regime definition, not its already blended targets.
        regime_id = f"regime:{source_id}:balanced"
        source_regime = regime_diagnostics_by_id[regime_id]["regime"]
        for hedge in hedge_profiles:
            targets, diagnostics = regime_hedged_targets(
                targets_by_id[source_id],
                source_regime,
                maximum_gross=1.85,
                **{key: value for key, value in hedge.items() if key != "name"},
            )
            candidate_id = f"hedge:{source_id}:{hedge['name']}"
            targets_by_id[candidate_id] = targets
            result = screen(data, targets, execution["base_cost_per_side"])
            row = {
                "candidate_id": candidate_id,
                "family": "regime_hedged_champion",
                "name": hedge["name"],
                "source_candidate_id": source_id,
                "hedge": hedge,
                "maximum_portfolio_gross": 1.85,
                "average_hedge_gross": float(diagnostics["hedge_gross"].mean()),
                "risk_guard": {
                    "name": "targets_own_state",
                    "threshold": 0.99,
                    "multiplier": 1.0,
                    "recovery": None,
                    "cooldown_hours": 1,
                },
                "profile": profile(result.equity, latest),
            }
            row["gate"] = robustness_gate(row, benchmark_recent_cagr)
            row["screen_gate_passed"] = all(row["gate"].values())
            row["score"] = score_row(row)
            rows.append(row)

    # Blend the independent market-neutral sleeve with the strongest attack
    # candidate.  Gross is capped after combination, so diversification must
    # improve the return path rather than merely add leverage.
    ensemble_profiles = (
        {"name": "relative_30", "attack_weight": 0.85, "relative_weight": 0.45},
        {"name": "relative_45", "attack_weight": 0.75, "relative_weight": 0.65},
    )
    for source_id in hedge_sources:
        for relative_name, relative_targets in cross_sectional_targets.items():
            for ensemble in ensemble_profiles:
                targets = _cap_gross(
                    targets_by_id[source_id] * ensemble["attack_weight"]
                    + relative_targets.reindex_like(core_targets).fillna(0.0)
                    * ensemble["relative_weight"],
                    1.85,
                )
                candidate_id = (
                    f"ensemble:{source_id}:{relative_name}:{ensemble['name']}"
                )
                targets_by_id[candidate_id] = targets
                result = screen(data, targets, execution["base_cost_per_side"])
                row = {
                    "candidate_id": candidate_id,
                    "family": (
                        "attack_reversal_ensemble"
                        if cross_sectional_specs[relative_name].direction == "reversal"
                        else "attack_relative_ensemble"
                    ),
                    "name": ensemble["name"],
                    "source_candidate_id": source_id,
                    "relative_name": relative_name,
                    "ensemble": ensemble,
                    "maximum_portfolio_gross": 1.85,
                    "risk_guard": {
                        "name": "targets_own_state",
                        "threshold": 0.99,
                        "multiplier": 1.0,
                        "recovery": None,
                        "cooldown_hours": 1,
                    },
                    "profile": profile(result.equity, latest),
                }
                row["gate"] = robustness_gate(row, benchmark_recent_cagr)
                row["screen_gate_passed"] = all(row["gate"].values())
                row["score"] = score_row(row)
                rows.append(row)

    gated_alpha_profiles = (
        {
            "name": "fast_gate",
            "short_hours": 24 * 14,
            "long_hours": 24 * 60,
            "peak_hours": 24 * 180,
            "warning_drawdown": 0.08,
            "hard_drawdown": 0.14,
            "strong_base_multiplier": 1.10,
            "normal_base_multiplier": 0.90,
            "weak_base_multiplier": 0.60,
            "hard_base_multiplier": 0.20,
            "strong_alpha_multiplier": 0.55,
            "normal_alpha_multiplier": 0.20,
            "rebalance_hours": 24,
            "maximum_gross": 1.95,
        },
        {
            "name": "balanced_gate",
            "short_hours": 24 * 30,
            "long_hours": 24 * 90,
            "peak_hours": 24 * 240,
            "warning_drawdown": 0.10,
            "hard_drawdown": 0.16,
            "strong_base_multiplier": 1.15,
            "normal_base_multiplier": 0.90,
            "weak_base_multiplier": 0.65,
            "hard_base_multiplier": 0.25,
            "strong_alpha_multiplier": 0.65,
            "normal_alpha_multiplier": 0.25,
            "rebalance_hours": 24,
            "maximum_gross": 2.00,
        },
        {
            "name": "convex_gate",
            "short_hours": 24 * 21,
            "long_hours": 24 * 120,
            "peak_hours": 24 * 240,
            "warning_drawdown": 0.12,
            "hard_drawdown": 0.18,
            "strong_base_multiplier": 1.25,
            "normal_base_multiplier": 0.95,
            "weak_base_multiplier": 0.70,
            "hard_base_multiplier": 0.30,
            "strong_alpha_multiplier": 0.75,
            "normal_alpha_multiplier": 0.30,
            "rebalance_hours": 24,
            "maximum_gross": 2.10,
        },
    )
    gated_alpha_sources = ("confirmed_carry_3d", "pressure_7d")
    for source_id in hedge_sources:
        for alpha_name in gated_alpha_sources:
            alpha_targets = funding_targets_by_name[alpha_name]
            alpha_proxy = screen(
                data, alpha_targets, execution["base_cost_per_side"]
            )
            for gate_spec in gated_alpha_profiles:
                targets, diagnostics = performance_gated_alpha_targets(
                    targets_by_id[source_id],
                    alpha_targets,
                    alpha_proxy.equity,
                    **{key: value for key, value in gate_spec.items() if key != "name"},
                )
                candidate_id = (
                    f"gated_alpha:{source_id}:{alpha_name}:{gate_spec['name']}"
                )
                targets_by_id[candidate_id] = targets
                result = screen(data, targets, execution["base_cost_per_side"])
                row = {
                    "candidate_id": candidate_id,
                    "family": "performance_gated_funding_alpha",
                    "name": gate_spec["name"],
                    "source_candidate_id": source_id,
                    "alpha_name": alpha_name,
                    "performance_gate": gate_spec,
                    "maximum_portfolio_gross": gate_spec["maximum_gross"],
                    "alpha_active_share": float(
                        diagnostics["alpha_factor"].gt(0.0).mean()
                    ),
                    "risk_guard": {
                        "name": "targets_own_state",
                        "threshold": 0.99,
                        "multiplier": 1.0,
                        "recovery": None,
                        "cooldown_hours": 1,
                    },
                    "profile": profile(result.equity, latest),
                }
                row["gate"] = robustness_gate(row, benchmark_recent_cagr)
                row["screen_gate_passed"] = all(row["gate"].values())
                row["score"] = score_row(row)
                rows.append(row)

    carry_ensemble_profiles = (
        {"name": "carry_25", "attack_weight": 0.90, "carry_weight": 0.35},
        {"name": "carry_40", "attack_weight": 0.80, "carry_weight": 0.55},
    )
    for source_id in hedge_sources:
        for carry_name, carry_targets in funding_targets_by_name.items():
            for ensemble in carry_ensemble_profiles:
                targets = _cap_gross(
                    targets_by_id[source_id] * ensemble["attack_weight"]
                    + carry_targets.reindex_like(core_targets).fillna(0.0)
                    * ensemble["carry_weight"],
                    1.85,
                )
                candidate_id = (
                    f"carry_ensemble:{source_id}:{carry_name}:{ensemble['name']}"
                )
                targets_by_id[candidate_id] = targets
                result = screen(data, targets, execution["base_cost_per_side"])
                row = {
                    "candidate_id": candidate_id,
                    "family": (
                        "attack_funding_carry_ensemble"
                        if funding_specs[carry_name].signal_mode == "carry"
                        else "attack_funding_signal_ensemble"
                    ),
                    "name": ensemble["name"],
                    "source_candidate_id": source_id,
                    "carry_name": carry_name,
                    "ensemble": ensemble,
                    "maximum_portfolio_gross": 1.85,
                    "risk_guard": {
                        "name": "targets_own_state",
                        "threshold": 0.99,
                        "multiplier": 1.0,
                        "recovery": None,
                        "cooldown_hours": 1,
                    },
                    "profile": profile(result.equity, latest),
                }
                row["gate"] = robustness_gate(row, benchmark_recent_cagr)
                row["screen_gate_passed"] = all(row["gate"].values())
                row["score"] = score_row(row)
                rows.append(row)

    # Volatility management cuts exposure from the attack sleeve only while
    # its own closed realized volatility is elevated.  Stable confirmed bull
    # periods can retain or slightly increase gross; neutral/bear regimes have
    # lower ceilings and one-day shocks force an immediate temporary cut.
    volatility_profiles = (
        {
            "name": "balanced_vol",
            "volatility_hours": 24 * 14,
            "annual_volatility_target": 0.80,
            "minimum_multiplier": 0.20,
            "bull_maximum_multiplier": 1.10,
            "neutral_maximum_multiplier": 0.80,
            "bear_maximum_multiplier": 0.40,
            "one_day_shock": 0.05,
            "shock_multiplier": 0.15,
            "rebalance_hours": 6,
            "maximum_gross": 2.00,
        },
        {
            "name": "responsive_vol",
            "volatility_hours": 24 * 7,
            "annual_volatility_target": 0.65,
            "minimum_multiplier": 0.15,
            "bull_maximum_multiplier": 1.20,
            "neutral_maximum_multiplier": 0.70,
            "bear_maximum_multiplier": 0.30,
            "one_day_shock": 0.04,
            "shock_multiplier": 0.10,
            "rebalance_hours": 3,
            "maximum_gross": 2.00,
        },
        {
            "name": "tolerant_vol",
            "volatility_hours": 24 * 21,
            "annual_volatility_target": 0.95,
            "minimum_multiplier": 0.30,
            "bull_maximum_multiplier": 1.05,
            "neutral_maximum_multiplier": 0.90,
            "bear_maximum_multiplier": 0.55,
            "one_day_shock": 0.06,
            "shock_multiplier": 0.25,
            "rebalance_hours": 6,
            "maximum_gross": 1.95,
        },
        {
            "name": "convex_stable",
            "volatility_hours": 24 * 14,
            "annual_volatility_target": 0.90,
            "minimum_multiplier": 0.15,
            "bull_maximum_multiplier": 1.60,
            "neutral_maximum_multiplier": 0.80,
            "bear_maximum_multiplier": 0.25,
            "one_day_shock": 0.045,
            "shock_multiplier": 0.10,
            "rebalance_hours": 3,
            "maximum_gross": 2.40,
        },
        {
            "name": "convex_attack",
            "volatility_hours": 24 * 10,
            "annual_volatility_target": 1.05,
            "minimum_multiplier": 0.15,
            "bull_maximum_multiplier": 1.80,
            "neutral_maximum_multiplier": 0.90,
            "bear_maximum_multiplier": 0.20,
            "one_day_shock": 0.040,
            "shock_multiplier": 0.08,
            "rebalance_hours": 3,
            "maximum_gross": 2.50,
        },
        {
            "name": "convex_selective",
            "volatility_hours": 24 * 7,
            "annual_volatility_target": 0.75,
            "minimum_multiplier": 0.10,
            "bull_maximum_multiplier": 2.00,
            "neutral_maximum_multiplier": 0.65,
            "bear_maximum_multiplier": 0.15,
            "one_day_shock": 0.035,
            "shock_multiplier": 0.05,
            "rebalance_hours": 3,
            "maximum_gross": 2.50,
        },
    )
    for source_id in hedge_sources:
        proxy = screen(
            data,
            targets_by_id[source_id],
            execution["base_cost_per_side"],
        )
        regime_id = f"regime:{source_id}:balanced"
        source_regime = regime_diagnostics_by_id[regime_id]["regime"]
        for vol_spec in volatility_profiles:
            targets, diagnostics = volatility_managed_targets(
                targets_by_id[source_id],
                proxy.equity,
                source_regime,
                **{key: value for key, value in vol_spec.items() if key != "name"},
            )
            candidate_id = f"volatility:{source_id}:{vol_spec['name']}"
            targets_by_id[candidate_id] = targets
            result = screen(data, targets, execution["base_cost_per_side"])
            row = {
                "candidate_id": candidate_id,
                "family": (
                    "convex_volatility_managed_champion"
                    if vol_spec["name"].startswith("convex_")
                    else "volatility_managed_champion"
                ),
                "name": vol_spec["name"],
                "source_candidate_id": source_id,
                "volatility_management": vol_spec,
                "maximum_portfolio_gross": vol_spec["maximum_gross"],
                "average_risk_factor": float(diagnostics["risk_factor"].mean()),
                "risk_guard": {
                    "name": "targets_own_state",
                    "threshold": 0.99,
                    "multiplier": 1.0,
                    "recovery": None,
                    "cooldown_hours": 1,
                },
                "profile": profile(result.equity, latest),
            }
            row["gate"] = robustness_gate(row, benchmark_recent_cagr)
            row["screen_gate_passed"] = all(row["gate"].values())
            row["score"] = score_row(row)
            rows.append(row)

    # Replace blunt index hedging with the opportunity engine's own short
    # signals.  Bull keeps the high-capture sleeve, neutral blends with V13,
    # and bear can only short assets that independently met V14's causal
    # impulse criteria.
    bear_sleeve_profiles = (
        {
            "name": "defensive_short",
            "bull_attack": 1.00,
            "bull_core": 0.10,
            "neutral_attack": 0.55,
            "neutral_core": 0.65,
            "bear_short": 0.80,
            "bear_core": 0.35,
            "maximum_gross": 1.85,
        },
        {
            "name": "balanced_short",
            "bull_attack": 1.00,
            "bull_core": 0.10,
            "neutral_attack": 0.70,
            "neutral_core": 0.45,
            "bear_short": 1.10,
            "bear_core": 0.15,
            "maximum_gross": 1.85,
        },
        {
            "name": "attack_short",
            "bull_attack": 1.00,
            "bull_core": 0.05,
            "neutral_attack": 0.80,
            "neutral_core": 0.30,
            "bear_short": 1.40,
            "bear_core": 0.00,
            "maximum_gross": 1.85,
        },
    )
    for source_id in hedge_sources:
        regime_id = f"regime:{source_id}:balanced"
        source_regime = regime_diagnostics_by_id[regime_id]["regime"]
        for sleeve in bear_sleeve_profiles:
            targets, diagnostics = three_regime_sleeve_targets(
                core_targets,
                targets_by_id[source_id],
                v14_raw,
                source_regime,
                **{key: value for key, value in sleeve.items() if key != "name"},
            )
            candidate_id = f"bear_sleeve:{source_id}:{sleeve['name']}"
            targets_by_id[candidate_id] = targets
            result = screen(data, targets, execution["base_cost_per_side"])
            row = {
                "candidate_id": candidate_id,
                "family": "three_regime_signal_sleeves",
                "name": sleeve["name"],
                "source_candidate_id": source_id,
                "sleeve": sleeve,
                "maximum_portfolio_gross": sleeve["maximum_gross"],
                "average_bear_short_signal_gross": float(
                    diagnostics.loc[
                        diagnostics["regime"].eq("bear"), "short_signal_gross"
                    ].mean()
                ),
                "risk_guard": {
                    "name": "targets_own_state",
                    "threshold": 0.99,
                    "multiplier": 1.0,
                    "recovery": None,
                    "cooldown_hours": 1,
                },
                "profile": profile(result.equity, latest),
            }
            row["gate"] = robustness_gate(row, benchmark_recent_cagr)
            row["screen_gate_passed"] = all(row["gate"].values())
            row["score"] = score_row(row)
            rows.append(row)

    # Third family: preserve the strongest recent champion allocator, but add
    # a faster causal shield.  It attacks only while short and long closed
    # equity trends agree, and cuts exposure on drawdown or a one-day shock.
    # The grid is intentionally small and structural to limit overfitting.
    shield_profiles = (
        {
            "name": "guarded_attack",
            "short_hours": 48,
            "long_hours": 24 * 21,
            "peak_hours": 24 * 120,
            "warning_drawdown": 0.06,
            "hard_drawdown": 0.10,
            "attack_multiplier": 1.45,
            "neutral_multiplier": 0.70,
            "weak_multiplier": 0.25,
            "hard_multiplier": 0.05,
            "shock_return": 0.045,
            "rebalance_hours": 6,
            "maximum_gross": 1.85,
        },
        {
            "name": "balanced_attack",
            "short_hours": 72,
            "long_hours": 24 * 30,
            "peak_hours": 24 * 180,
            "warning_drawdown": 0.08,
            "hard_drawdown": 0.13,
            "attack_multiplier": 1.55,
            "neutral_multiplier": 0.80,
            "weak_multiplier": 0.35,
            "hard_multiplier": 0.10,
            "shock_return": 0.055,
            "rebalance_hours": 6,
            "maximum_gross": 1.95,
        },
        {
            "name": "convex_attack",
            "short_hours": 72,
            "long_hours": 24 * 30,
            "peak_hours": 24 * 180,
            "warning_drawdown": 0.10,
            "hard_drawdown": 0.16,
            "attack_multiplier": 1.70,
            "neutral_multiplier": 0.90,
            "weak_multiplier": 0.45,
            "hard_multiplier": 0.15,
            "shock_return": 0.065,
            "rebalance_hours": 12,
            "maximum_gross": 2.00,
        },
    )
    shield_windows = ((30, 60, 120), (45, 90, 180))
    for windows in shield_windows:
        mixed = multihorizon_two_sleeve_targets(
            core_targets,
            v14_targets,
            core_returns,
            v14_returns,
            windows_days=windows,
            funding_weight_when_leading=0.70,
            funding_weight_when_lagging=0.10,
            rebalance_hours=24,
        )
        proxy = screen(data, mixed, execution["base_cost_per_side"])
        for shield in shield_profiles:
            targets, diagnostics = adaptive_equity_shield(
                mixed,
                proxy.equity,
                **{key: value for key, value in shield.items() if key != "name"},
            )
            candidate_id = f"shield:{'-'.join(map(str, windows))}:{shield['name']}"
            targets_by_id[candidate_id] = targets
            result = screen(data, targets, execution["base_cost_per_side"])
            row = {
                "candidate_id": candidate_id,
                "family": "protected_adaptive_champion",
                "name": shield["name"],
                "windows_days": list(windows),
                "core_weight_when_leading": 0.70,
                "core_weight_when_lagging": 0.10,
                "shield": shield,
                "maximum_portfolio_gross": shield["maximum_gross"],
                "average_risk_factor": float(diagnostics["risk_factor"].mean()),
                "profile": profile(result.equity, latest),
            }
            row["gate"] = robustness_gate(row, benchmark_recent_cagr)
            row["screen_gate_passed"] = all(row["gate"].values())
            row["score"] = score_row(row)
            rows.append(row)

    # Final structural check: do not replace the profitable champion state.
    # Layer a one-way brake on the already convex champion so healthy periods
    # remain unchanged and only deteriorating/underwater states are reduced.
    brake_profiles = (
        {
            "name": "early_brake",
            "warning_drawdown": 0.055,
            "hard_drawdown": 0.09,
            "weak_multiplier": 0.35,
            "hard_multiplier": 0.05,
            "shock_return": 0.045,
        },
        {
            "name": "balanced_brake",
            "warning_drawdown": 0.075,
            "hard_drawdown": 0.12,
            "weak_multiplier": 0.50,
            "hard_multiplier": 0.10,
            "shock_return": 0.055,
        },
        {
            "name": "late_brake",
            "warning_drawdown": 0.095,
            "hard_drawdown": 0.15,
            "weak_multiplier": 0.65,
            "hard_multiplier": 0.15,
            "shock_return": 0.065,
        },
    )
    for windows in shield_windows:
        mixed = multihorizon_two_sleeve_targets(
            core_targets,
            v14_targets,
            core_returns,
            v14_returns,
            windows_days=windows,
            funding_weight_when_leading=0.70,
            funding_weight_when_lagging=0.10,
            rebalance_hours=24,
        )
        mixed_proxy = screen(data, mixed, execution["base_cost_per_side"])
        convex = convex_equity_overlay(
            mixed,
            mixed_proxy.equity,
            short_hours=72,
            long_hours=24 * 30,
            drawdown_hours=24 * 30,
            drawdown_threshold=0.12,
            winner_multiplier=1.30,
            loser_multiplier=0.50,
            drawdown_multiplier=0.30,
            rebalance_hours=24,
            maximum_gross=1.85,
        )
        convex_proxy = screen(data, convex, execution["base_cost_per_side"])
        for brake in brake_profiles:
            targets, diagnostics = adaptive_equity_shield(
                convex,
                convex_proxy.equity,
                short_hours=48,
                long_hours=24 * 21,
                peak_hours=24 * 180,
                attack_multiplier=1.0,
                neutral_multiplier=1.0,
                rebalance_hours=6,
                maximum_gross=1.85,
                **{key: value for key, value in brake.items() if key != "name"},
            )
            candidate_id = f"brake:{'-'.join(map(str, windows))}:{brake['name']}"
            targets_by_id[candidate_id] = targets
            result = screen(data, targets, execution["base_cost_per_side"])
            row = {
                "candidate_id": candidate_id,
                "family": "braked_convex_champion",
                "name": brake["name"],
                "windows_days": list(windows),
                "core_weight_when_leading": 0.70,
                "core_weight_when_lagging": 0.10,
                "brake": brake,
                "maximum_portfolio_gross": 1.85,
                "average_risk_factor": float(diagnostics["risk_factor"].mean()),
                "profile": profile(result.equity, latest),
            }
            row["gate"] = robustness_gate(row, benchmark_recent_cagr)
            row["screen_gate_passed"] = all(row["gate"].values())
            row["score"] = score_row(row)
            rows.append(row)

    ranked = sorted(rows, key=lambda item: item["score"], reverse=True)
    exact_rows: list[dict[str, object]] = []
    protected = [
        row for row in ranked
        if row["family"] in {
            "protected_adaptive_champion",
            "braked_convex_champion",
        }
    ]
    structural = [row for row in ranked if row["family"] == "adaptive_h6_trend"]
    regime_switched = [
        row for row in ranked if row["family"] == "regime_switched_champion"
    ]
    regime_reentry = [
        row for row in ranked if row["family"] == "regime_reentry_champion"
    ]
    loss_limited = [
        row for row in ranked if row["family"] == "rolling_loss_limited_champion"
    ]
    regime_hedged = [
        row for row in ranked if row["family"] == "regime_hedged_champion"
    ]
    three_regime = [
        row for row in ranked if row["family"] == "three_regime_signal_sleeves"
    ]
    volatility_managed = [
        row for row in ranked if row["family"] == "volatility_managed_champion"
    ]
    cross_sectional = [
        row for row in ranked if row["family"] == "cross_sectional_long_short"
    ]
    cross_sectional_reversal = [
        row for row in ranked if row["family"] == "cross_sectional_reversal"
    ]
    relative_ensemble = [
        row for row in ranked if row["family"] == "attack_relative_ensemble"
    ]
    reversal_ensemble = [
        row for row in ranked if row["family"] == "attack_reversal_ensemble"
    ]
    funding_carry = [
        row for row in ranked if row["family"] == "market_neutral_funding_carry"
    ]
    carry_ensemble = [
        row for row in ranked if row["family"] == "attack_funding_carry_ensemble"
    ]
    funding_confirmation = [
        row for row in ranked if row["family"] == "funding_price_confirmation"
    ]
    funding_signal_ensemble = [
        row for row in ranked if row["family"] == "attack_funding_signal_ensemble"
    ]
    gated_funding_alpha = [
        row for row in ranked if row["family"] == "performance_gated_funding_alpha"
    ]
    rapid_reentry_attack = [
        row for row in ranked if row["family"] == "rapid_reentry_attack"
    ]
    convex_volatility = [
        row for row in ranked
        if row["family"] == "convex_volatility_managed_champion"
    ]
    exact_pool = []
    seen_ids: set[str] = set()
    for row in [
        *ranked[:2],
        *convex_volatility[:6],
    ]:
        candidate_id = str(row["candidate_id"])
        if candidate_id not in seen_ids:
            exact_pool.append(row)
            seen_ids.add(candidate_id)
    risk_guard_specs = (
        {
            "name": "guard_5pct",
            "threshold": 0.05,
            "multiplier": 0.08,
            "cooldown_hours": 24 * 30,
        },
        {
            "name": "guard_7pct",
            "threshold": 0.07,
            "multiplier": 0.15,
            "cooldown_hours": 24 * 21,
        },
        {
            "name": "guard_9pct",
            "threshold": 0.09,
            "multiplier": 0.20,
            "cooldown_hours": 24 * 14,
        },
        {
            "name": "recovery_6pct",
            "threshold": 0.06,
            "multiplier": 0.25,
            "recovery": 0.025,
            "cooldown_hours": None,
        },
        {
            "name": "recovery_8pct",
            "threshold": 0.08,
            "multiplier": 0.35,
            "recovery": 0.03,
            "cooldown_hours": None,
        },
        {
            "name": "recovery_10pct",
            "threshold": 0.10,
            "multiplier": 0.45,
            "recovery": 0.04,
            "cooldown_hours": None,
        },
    )
    aggressive_champions = [
        row for row in ranked
        if row["family"] == "adaptive_v13_v14_champion"
        and row["name"] == "attack"
    ][:2]
    for row in aggressive_champions:
        for guard in risk_guard_specs:
            exact_pool.append({
                **row,
                "candidate_id": f"{row['candidate_id']}:{guard['name']}",
                "target_candidate_id": row["candidate_id"],
                "risk_guard": guard,
            })
    for row in exact_pool:
        targets = targets_by_id[str(row.get("target_candidate_id", row["candidate_id"]))]
        risk_guard = row.get("risk_guard", {
            "name": "default",
            "threshold": 0.12,
            "multiplier": 0.35,
            "recovery": None,
            "cooldown_hours": 168,
        })
        exact_base = exact_fast(
            data,
            targets,
            cost_per_side=execution["base_cost_per_side"],
            maintenance_equity_fraction=execution["maintenance_equity_fraction"],
            gross_guard_cap=float(row["maximum_portfolio_gross"]) + 0.15,
            drawdown_guard_threshold=risk_guard["threshold"],
            drawdown_guard_multiplier=risk_guard["multiplier"],
            drawdown_guard_recovery=risk_guard.get("recovery"),
            drawdown_guard_cooldown_hours=risk_guard["cooldown_hours"],
        )
        severe = exact_fast(
            data,
            targets,
            cost_per_side=execution["severe_cost_per_side"],
            maintenance_equity_fraction=execution["maintenance_equity_fraction"],
            gross_guard_cap=float(row["maximum_portfolio_gross"]) + 0.15,
            drawdown_guard_threshold=risk_guard["threshold"],
            drawdown_guard_multiplier=risk_guard["multiplier"],
            drawdown_guard_recovery=risk_guard.get("recovery"),
            drawdown_guard_cooldown_hours=risk_guard["cooldown_hours"],
        )
        delayed = exact_fast(
            data,
            targets.shift(2).fillna(0.0),
            cost_per_side=execution["base_cost_per_side"],
            maintenance_equity_fraction=execution["maintenance_equity_fraction"],
            gross_guard_cap=float(row["maximum_portfolio_gross"]) + 0.15,
            drawdown_guard_threshold=risk_guard["threshold"],
            drawdown_guard_multiplier=risk_guard["multiplier"],
            drawdown_guard_recovery=risk_guard.get("recovery"),
            drawdown_guard_cooldown_hours=risk_guard["cooldown_hours"],
        )
        checked = {**row, "profile": profile(exact_base.equity, latest)}
        checked["gate"] = robustness_gate(checked, benchmark_recent_cagr)
        checked["stress"] = {
            "severe_cost": profile(severe.equity, latest),
            "delay_3h": profile(delayed.equity, latest),
        }
        checked["exact_gate"] = {
            **checked["gate"],
            "severe_cost_recent_positive": checked["stress"]["severe_cost"]["recent"]["return"] > 0.0,
            "severe_cost_current_positive": checked["stress"]["severe_cost"]["current"]["return"] > 0.0,
            "delay_3h_recent_positive": checked["stress"]["delay_3h"]["recent"]["return"] > 0.0,
            "delay_3h_current_positive": checked["stress"]["delay_3h"]["current"]["return"] > 0.0,
            "no_ruin": not (exact_base.ruin or severe.ruin or delayed.ruin),
        }
        checked["exact_gate_passed"] = all(checked["exact_gate"].values())
        checked["score"] = score_row(checked)
        exact_rows.append(checked)

    exact_ranked = sorted(exact_rows, key=lambda item: item["score"], reverse=True)
    promoted = next((row for row in exact_ranked if row["exact_gate_passed"]), None)
    report = {
        "status": "promoted" if promoted else "rejected",
        "objective": "maximize recent-weighted compounded ROI and frequency of large days without dependence on the best day",
        "latest_data_timestamp": latest.isoformat(),
        "data_priority": "2025+ and 2026 receive the largest score weight; 2021-2024 are robustness regimes",
        "anti_overfit_rule": "paper promotion is forbidden unless exact, cost-stress and delay gates pass and recent returns remain positive after deleting the best day",
        "benchmarks": benchmarks,
        "tested_configurations": len(rows) + len(aggressive_champions) * len(risk_guard_specs),
        "screen_passed": sum(bool(row["screen_gate_passed"]) for row in rows),
        "promoted": promoted,
        "exact_finalists": exact_ranked,
        "screen_leaderboard": ranked[:12],
        "real_orders": False,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "latest_data_timestamp": report["latest_data_timestamp"],
        "tested_configurations": report["tested_configurations"],
        "screen_passed": report["screen_passed"],
        "promoted": promoted,
    }, indent=2))


if __name__ == "__main__":
    main()
