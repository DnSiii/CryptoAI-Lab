from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.data import FuturesData, point_in_time_liquid_view
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from cryptoai_v13.signals import StrategySpec, build_targets
from cryptoai_v13.v99 import V99AsymmetricSpec, _cap_gross
from cryptoai_v13.v99_frozen import (
    FAST_GUARD,
    FROZEN_REBALANCE_HOURS,
    FROZEN_ROUTINE_PERSISTENCE_HOURS,
    combine_dynamic_results,
    desired_satellite_weight,
    trailing_vote,
)
from cryptoai_v13.v99_r4 import V99R4ControlSpec, _sparse_side_shock
from cryptoai_v13.v99_r5 import asymmetric_v99_targets_r5
from paper_once_v13 import apply_funding_quarantine, cap_targets
from paper_once_v15 import build_v15
from paper_once_v16 import build_v16
from paper_once_v99 import load_execution
from run_final_candidate import build_candidate

REPORT_PATH = PROJECT / "reports" / "isolated_horizon_audit.json"
HORIZONS = (7, 30, 90, 180, 365)
INITIAL_CAPITAL = 10_000.0


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def slice_data(data: FuturesData, start: pd.Timestamp, end: pd.Timestamp) -> FuturesData:
    frames = {name: frame.loc[start:end].copy() for name, frame in data.frames.items()}
    funding = data.funding.loc[start:end].copy()
    return FuturesData(frames=frames, funding=funding, symbols=data.symbols)


def metrics(equity: pd.Series) -> dict:
    eq = equity.dropna()
    if len(eq) < 2:
        return {
            "return_pct": 0.0,
            "final_capital_brl": INITIAL_CAPITAL,
            "max_drawdown_pct": 0.0,
            "best_day_pct": 0.0,
            "worst_day_pct": 0.0,
        }
    normalized = eq / float(eq.iloc[0])
    daily = normalized.resample("1D").last().dropna()
    daily_r = daily.pct_change(fill_method=None).dropna()
    dd = normalized / normalized.cummax() - 1.0
    multiple = float(normalized.iloc[-1])
    return {
        "return_pct": round((multiple - 1.0) * 100.0, 6),
        "final_capital_brl": round(INITIAL_CAPITAL * multiple, 2),
        "max_drawdown_pct": round(float(dd.min()) * 100.0, 6),
        "best_day_pct": round(float(daily_r.max()) * 100.0, 6) if len(daily_r) else 0.0,
        "worst_day_pct": round(float(daily_r.min()) * 100.0, 6) if len(daily_r) else 0.0,
    }


def trailing_metrics(equity: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    window = equity.loc[start:end].dropna()
    return metrics(window)


def build_v14_components():
    candidate = load_json(PROJECT / "config" / "candidate_v14_max_capture.json")
    finalist = load_json(PROJECT / "config" / candidate["frozen_core_config"])
    base_config = load_json(PROJECT / "config" / finalist["base_candidate_config"])
    data, core_targets, _, _ = build_candidate(base_config)
    core_targets = cap_targets(core_targets, finalist["target_cap"])
    universe = base_config["point_in_time_universe"]
    signal_data, _ = point_in_time_liquid_view(
        data,
        top_n=universe["top_n"],
        lookback_hours=universe["quote_volume_lookback_hours"],
        minimum_history_hours=universe["minimum_history_hours"],
    )
    raw = build_targets(signal_data, StrategySpec(**candidate["opportunity"]["spec"]))
    allocation = candidate["allocation"]
    targets, _ = additive_opportunity_targets(
        core_targets,
        raw,
        OpportunityBudget(
            allocation["maximum_overlay_gross"],
            allocation["maximum_portfolio_gross"],
        ),
    )
    data, targets, _ = apply_funding_quarantine(data, targets)
    execution = base_config["execution"]
    guard = candidate["circuit_breaker"]
    kwargs = {
        "cost_per_side": execution["base_cost_per_side"],
        "maintenance_equity_fraction": execution["maintenance_equity_fraction"],
        "gross_guard_cap": allocation["gross_drift_guard_cap"],
        "drawdown_guard_threshold": guard["drawdown_threshold"],
        "drawdown_guard_multiplier": guard["exposure_multiplier"],
        "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
    }
    full = exact_fast(data, targets, **kwargs)
    return candidate, data, targets, full, kwargs


def v15_execution_kwargs(candidate: dict) -> dict:
    parent = load_json(PROJECT / "config" / candidate["parent_candidate_config"])
    finalist = load_json(PROJECT / "config" / parent["frozen_core_config"])
    base_config = load_json(PROJECT / "config" / finalist["base_candidate_config"])
    execution = base_config["execution"]
    allocation = parent["allocation"]
    guard = parent["circuit_breaker"]
    return {
        "cost_per_side": execution["base_cost_per_side"],
        "maintenance_equity_fraction": execution["maintenance_equity_fraction"],
        "gross_guard_cap": allocation["gross_drift_guard_cap"],
        "drawdown_guard_threshold": guard["drawdown_threshold"],
        "drawdown_guard_multiplier": guard["exposure_multiplier"],
        "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
    }


def v16_execution_kwargs(candidate: dict) -> dict:
    finalist = load_json(PROJECT / "config" / candidate["frozen_core_config"])
    base_config = load_json(PROJECT / "config" / finalist["base_candidate_config"])
    execution = base_config["execution"]
    guard = candidate["circuit_breaker"]
    return {
        "cost_per_side": execution["base_cost_per_side"],
        "maintenance_equity_fraction": execution["maintenance_equity_fraction"],
        "gross_guard_cap": guard["gross_drift_guard_cap"],
        "drawdown_guard_threshold": guard["drawdown_threshold"],
        "drawdown_guard_multiplier": guard["exposure_multiplier"],
        "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
    }


def build_satellite_targets(data, parent_targets, execution, spec, control):
    proxy = screen(data, parent_targets, execution["base_cost_per_side"]).equity
    r5_targets, diagnostics = asymmetric_v99_targets_r5(
        data, parent_targets, proxy, spec, control
    )
    routine = r5_targets.shift(FROZEN_ROUTINE_PERSISTENCE_HOURS).fillna(0.0)
    shock_long, shock_short, _ = _sparse_side_shock(data.close, parent_targets, control)
    long_now = pd.concat(
        [diagnostics["long_risk_factor"].astype(float), shock_long], axis=1
    ).min(axis=1)
    short_now = pd.concat(
        [diagnostics["short_risk_factor"].astype(float), shock_short], axis=1
    ).min(axis=1)
    return _cap_gross(
        routine.clip(lower=0.0).mul(long_now, axis=0)
        + routine.clip(upper=0.0).mul(short_now, axis=0),
        spec.maximum_gross,
    )


def reset_exact(data, targets, kwargs, start, end):
    sliced = slice_data(data, start, end)
    t = targets.reindex(index=sliced.close.index, columns=sliced.close.columns).fillna(0.0)
    return exact_fast(sliced, t, **kwargs)


def main() -> None:
    # Build the exact current causal target trajectories first.  The audit then
    # resets portfolio/equity/execution state at each requested horizon while
    # retaining only causal pre-start signal context already embedded in targets.
    v14_candidate, v14_data, v14_targets, v14_full, v14_kwargs = build_v14_components()

    v15_candidate, v15_data, v15_targets, v15_full, _, _, _ = build_v15()
    v15_kwargs = v15_execution_kwargs(v15_candidate)

    v16_candidate = load_json(PROJECT / "config" / "candidate_v16_experimental_balanced_relaxed.json")
    v16_data, v16_targets, v16_full, _, _ = build_v16(v16_candidate)
    v16_kwargs = v16_execution_kwargs(v16_candidate)

    v99_candidate = load_json(PROJECT / "config" / "candidate_v99_asymmetric.json")
    v99_parent = load_json(PROJECT / "config" / v99_candidate["parent_candidate_config"])
    execution = load_execution(v99_parent)
    spec = V99AsymmetricSpec(**v99_candidate["asymmetric_overlay"])
    control = V99R4ControlSpec(**v99_candidate["r4_control"])
    satellite_targets = build_satellite_targets(v16_data, v16_targets, execution, spec, control)
    satellite_kwargs = {
        "cost_per_side": execution["base_cost_per_side"],
        "maintenance_equity_fraction": execution["maintenance_equity_fraction"],
        "gross_guard_cap": 2.0,
        "drawdown_guard_threshold": FAST_GUARD["threshold"],
        "drawdown_guard_multiplier": FAST_GUARD["multiplier"],
        "drawdown_guard_cooldown_hours": FAST_GUARD["cooldown"],
    }
    satellite_full = exact_fast(v16_data, satellite_targets, **satellite_kwargs)
    full_vote = trailing_vote(v16_full.equity, satellite_full.equity)
    full_desired = desired_satellite_weight(full_vote)
    v99_full_equity, _, _, _ = combine_dynamic_results(
        v16_full,
        satellite_full,
        full_desired,
        rebalance_hours=FROZEN_REBALANCE_HOURS,
        transfer_cost_per_side=execution["base_cost_per_side"],
    )

    common_end = min(
        v14_data.close.index[-1],
        v15_data.close.index[-1],
        v16_data.close.index[-1],
    )

    engines = {
        "v14": {
            "name": v14_candidate["name"],
            "version": v14_candidate["version"],
            "data": v14_data,
            "targets": v14_targets,
            "full_equity": v14_full.equity,
            "kwargs": v14_kwargs,
        },
        "v15": {
            "name": v15_candidate["name"],
            "version": v15_candidate["version"],
            "data": v15_data,
            "targets": v15_targets,
            "full_equity": v15_full.equity,
            "kwargs": v15_kwargs,
        },
        "v16": {
            "name": v16_candidate["name"],
            "version": v16_candidate["version"],
            "data": v16_data,
            "targets": v16_targets,
            "full_equity": v16_full.equity,
            "kwargs": v16_kwargs,
        },
    }

    results: dict[str, dict] = {key: {} for key in ("v14", "v15", "v16", "v99")}

    for days in HORIZONS:
        start = common_end - pd.Timedelta(days=days)
        for key, item in engines.items():
            reset = reset_exact(item["data"], item["targets"], item["kwargs"], start, common_end)
            results[key][str(days)] = {
                "start": reset.equity.index[0].isoformat(),
                "end": reset.equity.index[-1].isoformat(),
                "isolated_start": metrics(reset.equity),
                "old_trailing_slice": trailing_metrics(item["full_equity"], start, common_end),
                "ruin": bool(reset.ruin),
            }

        parent_reset = reset_exact(v16_data, v16_targets, v16_kwargs, start, common_end)
        satellite_reset = reset_exact(
            v16_data, satellite_targets, satellite_kwargs, start, common_end
        )
        desired_h = full_desired.reindex(parent_reset.equity.index).ffill().fillna(0.0)
        v99_eq, _, _, transfer_cost = combine_dynamic_results(
            parent_reset,
            satellite_reset,
            desired_h,
            rebalance_hours=FROZEN_REBALANCE_HOURS,
            transfer_cost_per_side=execution["base_cost_per_side"],
        )
        results["v99"][str(days)] = {
            "start": v99_eq.index[0].isoformat(),
            "end": v99_eq.index[-1].isoformat(),
            "isolated_start": metrics(v99_eq),
            "old_trailing_slice": trailing_metrics(v99_full_equity, start, common_end),
            "transfer_cost_total_equity_fraction": round(float(transfer_cost), 10),
            "ruin": bool(parent_reset.ruin or satellite_reset.ruin),
        }

    report = {
        "study": "Current CryptoAI isolated-start horizon audit",
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "common_end": common_end.isoformat(),
        "initial_capital_brl": INITIAL_CAPITAL,
        "horizons_days": list(HORIZONS),
        "methodology": {
            "portfolio_equity_reset_each_horizon": True,
            "positions_reset_each_horizon": True,
            "drawdown_circuit_breaker_reset_each_horizon": True,
            "fees_and_funding_recomputed_each_horizon": True,
            "causal_signal_warmup_retained": True,
            "no_future_data_in_targets": True,
            "note": "Targets are the current versioned causal engine trajectories, so indicators/regime/allocation signals may use data before the capital start. Prior P&L, positions and execution risk state are not carried into the isolated replay.",
        },
        "versions": {
            "v14": v14_candidate["version"],
            "v15": v15_candidate["version"],
            "v16": v16_candidate["version"],
            "v99": v99_candidate["version"],
        },
        "results": results,
    }
    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
