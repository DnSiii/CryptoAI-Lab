from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping


@dataclass(frozen=True)
class PromotionGates:
    """Frozen promotion gates recovered from the 2026-08-12 checkpoint."""

    min_base_cagr: float = 0.50
    max_drawdown_abs: float = 0.35
    min_severe_cost_cagr: float = 0.35
    min_delay_3h_cagr: float = 0.40
    min_decisions_per_month: float = 10.0
    max_bootstrap_ruin_probability: float = 0.01
    require_all_24_phases_positive: bool = True
    require_no_liquidation: bool = True

    def evaluate(self, metrics: Mapping[str, float | bool]) -> dict[str, bool]:
        phase_min = float(metrics.get("phase_min_cagr", float("-inf")))
        checks = {
            "base_cagr": float(metrics.get("base_cagr", float("-inf"))) > self.min_base_cagr,
            "drawdown": abs(float(metrics.get("max_drawdown", float("inf")))) <= self.max_drawdown_abs,
            "severe_cost_cagr": float(metrics.get("severe_cost_cagr", float("-inf"))) > self.min_severe_cost_cagr,
            "delay_3h_cagr": float(metrics.get("delay_3h_cagr", float("-inf"))) > self.min_delay_3h_cagr,
            "activity": float(metrics.get("decisions_per_month", 0.0)) >= self.min_decisions_per_month,
            "bootstrap_ruin": float(metrics.get("bootstrap_ruin_probability", 1.0)) < self.max_bootstrap_ruin_probability,
            "24_phases": (phase_min > 0.0) if self.require_all_24_phases_positive else True,
            "no_liquidation": (not bool(metrics.get("liquidated", True))) if self.require_no_liquidation else True,
        }
        return checks

    def report(self, metrics: Mapping[str, float | bool]) -> dict[str, object]:
        checks = self.evaluate(metrics)
        return {"gates": asdict(self), "checks": checks, "passed": all(checks.values())}
