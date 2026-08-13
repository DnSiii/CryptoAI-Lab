from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact, screen
from cryptoai_v13.data import load_data, point_in_time_liquid_view
from cryptoai_v13.metrics import slice_summary
from cryptoai_v13.signals import StrategySpec, build_targets
from build_walk_forward import scale_portfolio


def rows(patterns: tuple[str, ...]) -> dict[int, dict]:
    result = {}
    for pattern in patterns:
        for path in glob.glob(str(PROJECT / pattern)):
            for row in json.loads(Path(path).read_text())["rows"]:
                result[row["index"]] = row
    return result


def build_candidate(config: dict, phase: int = 0):
    raw = load_data(PROJECT, config["data_config"])
    u = config["point_in_time_universe"]
    signal_data, membership = point_in_time_liquid_view(
        raw, u["top_n"], u["quote_volume_lookback_hours"],
        u["minimum_history_hours"])
    core_data = load_data(PROJECT, "research_core2.json")
    core_rows = rows(("reports/core2_coarse_*.json", "reports/core2_regime_*.json"))
    pit_rows = rows(("reports/pit48_coarse_*.json", "reports/pit48_regime_*.json"))
    core_ids = config["core"]["component_ids"]
    core = sum(build_targets(core_data, StrategySpec(**core_rows[index]["spec"]))
               for index in core_ids) / len(core_ids)
    core = core.reindex(index=raw.close.index, columns=raw.close.columns).fillna(0.0)
    funding_id = config["funding_carry"]["component_id"]
    funding = build_targets(signal_data, StrategySpec(**pit_rows[funding_id]["spec"]))
    normal = config["sleeve_normalization"]
    core = scale_portfolio(raw, core, normal["target_volatility"],
                           normal["maximum_target_gross_leverage"],
                           normal["volatility_lookback_hours"],
                           normal["rebalance_hours"], phase)
    funding = scale_portfolio(raw, funding, normal["target_volatility"],
                              normal["maximum_target_gross_leverage"],
                              normal["volatility_lookback_hours"],
                              normal["rebalance_hours"], phase)
    base = (core * config["core"]["weight"]
            + funding * config["funding_carry"]["weight"])
    risk = config["risk_overlay"]
    targets = scale_portfolio(raw, base, risk["target_volatility"],
                              risk["maximum_target_gross_leverage"],
                              risk["volatility_lookback_hours"],
                              risk["rebalance_hours"], phase)
    components = {str(index): core_rows[index]["spec"] for index in core_ids}
    components[str(funding_id)] = pit_rows[funding_id]["spec"]
    return raw, targets, components, membership


def metric(result, start="2021-01-01", end="2026-07-31 23:00") -> dict:
    return slice_summary(result.equity, result.turnover, result.gross_exposure,
                         start, end)


def main() -> None:
    config = json.loads((PROJECT / "config" / "candidate_v13_pit_carry_core.json").read_text())
    raw, targets, components, membership = build_candidate(config)
    execution = config["execution"]
    print("iniciando exact base", flush=True)
    base = exact(raw, targets, execution["base_cost_per_side"],
                 execution["maintenance_equity_fraction"])
    print("iniciando exact severo", flush=True)
    severe = exact(raw, targets, execution["severe_cost_per_side"],
                   execution["maintenance_equity_fraction"])
    print("iniciando exact atraso", flush=True)
    delayed = exact(raw, targets.shift(2).fillna(0.0),
                    execution["base_cost_per_side"],
                    execution["maintenance_equity_fraction"])
    phase_screen = {}
    for phase in range(24):
        phase_raw, phase_targets, _, _ = build_candidate(config, phase)
        phase_screen[str(phase)] = metric(screen(
            phase_raw, phase_targets, execution["base_cost_per_side"]))
    base_metric, severe_metric, delayed_metric = metric(base), metric(severe), metric(delayed)
    gate = {
        "base_cagr_at_least_50pct": base_metric["cagr"] >= 0.50,
        "base_drawdown_no_worse_than_35pct": base_metric["max_drawdown"] >= -0.35,
        "all_calendar_periods_positive": min(base_metric["annual_returns"].values()) > 0,
        "severe_cost_cagr_at_least_35pct": severe_metric["cagr"] >= 0.35,
        "delay_3h_cagr_at_least_40pct": delayed_metric["cagr"] >= 0.40,
        "no_exact_ruin": not (base.ruin or severe.ruin or delayed.ruin),
        "all_phase_screen_cagr_at_least_50pct": min(
            item["cagr"] for item in phase_screen.values()) >= 0.50,
        "all_phase_screen_drawdown_no_worse_than_35pct": min(
            item["max_drawdown"] for item in phase_screen.values()) >= -0.35,
    }
    report = {
        "config": config,
        "components": components,
        "universe_average_members": float(membership.sum(axis=1).mean()),
        "historical_validation_disclosure": (
            "The historical interval has been used iteratively for research. "
            "These are robustness results, not a pristine untouched holdout. "
            "Forward paper trading is mandatory before capital."),
        "exact_base": base_metric,
        "exact_severe_cost": severe_metric,
        "exact_delay_3h": delayed_metric,
        "phase_screen": phase_screen,
        "gate": gate,
        "historical_gate_passed": all(gate.values()),
    }
    (PROJECT / "reports" / "candidate_v13_pit_carry_core_exact.json").write_text(
        json.dumps(report, indent=2) + "\n")
    targets.loc["2021-01-01":"2026-07-31 23:00"].to_csv(
        PROJECT / "reports" / "candidate_v13_pit_carry_core_targets.csv",
        index_label="timestamp")
    base.equity.loc["2021-01-01":"2026-07-31 23:00"].rename("equity").to_csv(
        PROJECT / "reports" / "candidate_v13_pit_carry_core_equity.csv",
        index_label="timestamp")
    print(json.dumps({"base": base_metric, "severe": severe_metric,
                      "delay": delayed_metric, "gate": gate}, indent=2))


if __name__ == "__main__":
    main()
