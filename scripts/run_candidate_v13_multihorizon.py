from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.allocator import multihorizon_two_sleeve_targets
from cryptoai_v13.backtest import exact, screen
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary
from cryptoai_v13.signals import StrategySpec, build_targets
from build_walk_forward import load_rows, scale_portfolio


def build_candidate(data, rows, config, phase: int | None = None):
    funding_id = config["funding_component_id"]
    regime_ids = config["regime_component_ids"]
    cost = config["execution"]["base_cost_per_side"]
    funding_targets = build_targets(data, StrategySpec(**rows[funding_id]["spec"]))
    regime_parts = [build_targets(data, StrategySpec(**rows[index]["spec"])) for index in regime_ids]
    regime_targets = sum(regime_parts) / len(regime_parts)
    funding_returns = screen(data, funding_targets, cost).equity.pct_change(fill_method=None).fillna(0.0)
    regime_returns = screen(data, regime_targets, cost).equity.pct_change(fill_method=None).fillna(0.0)
    allocator = config["allocator"]
    selected_phase = allocator["phase_utc_hour"] if phase is None else phase
    base = multihorizon_two_sleeve_targets(
        funding_targets, regime_targets, funding_returns, regime_returns,
        tuple(allocator["windows_days"]), allocator["funding_weight_when_leading"],
        allocator["funding_weight_when_lagging"], allocator["rebalance_hours"], selected_phase)
    risk = config["risk_overlay"]
    return scale_portfolio(
        data, base, risk["target_volatility"], risk["maximum_target_gross_leverage"],
        risk["volatility_lookback_hours"], risk["rebalance_hours"], selected_phase)


def metric(result):
    return slice_summary(result.equity, result.turnover, result.gross_exposure,
                         "2021-01-01", "2026-07-31 23:00")


if __name__ == "__main__":
    config = json.loads((PROJECT / "config" / "candidate_v13_multihorizon.json").read_text())
    rows = {row["index"]: row for row in load_rows()}
    data = load_data(PROJECT)
    targets = build_candidate(data, rows, config)
    base = exact(data, targets, config["execution"]["base_cost_per_side"])
    severe = exact(data, targets, config["execution"]["severe_cost_per_side"])
    delay = exact(data, targets.shift(2).fillna(0.0), config["execution"]["base_cost_per_side"])
    report = {
        "config": config,
        "components": {
            str(index): rows[index]["spec"]
            for index in [config["funding_component_id"], *config["regime_component_ids"]]
        },
        "exact_base": metric(base),
        "exact_severe_cost": metric(severe),
        "exact_delay_3h": metric(delay),
        "ruin": {"base": base.ruin, "severe": severe.ruin, "delay_3h": delay.ruin},
    }
    output = PROJECT / "reports" / "candidate_v13_multihorizon_exact.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    targets.loc["2021-01-01":"2026-07-31 23:00"].to_csv(
        PROJECT / "reports" / "candidate_v13_multihorizon_targets.csv", index_label="timestamp")
    base.equity.loc["2021-01-01":"2026-07-31 23:00"].rename("equity").to_csv(
        PROJECT / "reports" / "candidate_v13_multihorizon_equity.csv", index_label="timestamp")
    print(json.dumps(report, indent=2))
