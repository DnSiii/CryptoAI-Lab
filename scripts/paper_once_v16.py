from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.allocator import convex_equity_overlay, multihorizon_two_sleeve_targets
from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.data import point_in_time_liquid_view
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from cryptoai_v13.signals import StrategySpec, build_targets
from cryptoai_v13.v16 import trailing_profit_lock_targets
from paper_once_opportunity_v1 import empty_ledger, track_payload, write_json
from paper_once_v13 import apply_funding_quarantine, build_ledger, cap_targets
from run_final_candidate import build_candidate


CONFIG_PATH = PROJECT / "config" / "candidate_v16_experimental_balanced_relaxed.json"
STATE_PATH = PROJECT / "state" / "paper_v16_state.json"
SNAPSHOT_PATH = PROJECT / "reports" / "paper_v16_snapshot.json"
LEDGER_PATH = PROJECT / "reports" / "paper_v16_ledger.json"


def load_state(candidate: dict) -> dict | None:
    if not STATE_PATH.exists():
        return None
    value = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if value.get("candidate_version") != candidate["version"]:
        return None
    return value


def build_v16(candidate: dict):
    finalist = json.loads(
        (PROJECT / "config" / candidate["frozen_core_config"]).read_text(encoding="utf-8")
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text(encoding="utf-8")
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
    attack = json.loads(
        (PROJECT / "config" / candidate["frozen_attack_config"]).read_text(encoding="utf-8")
    )
    raw_attack = build_targets(
        signal_data, StrategySpec(**attack["opportunity"]["spec"])
    )
    attack_allocation = attack["allocation"]
    attack_targets, _ = additive_opportunity_targets(
        core_targets,
        raw_attack,
        OpportunityBudget(
            attack_allocation["maximum_overlay_gross"],
            attack_allocation["maximum_portfolio_gross"],
        ),
    )

    cost = base_config["execution"]["base_cost_per_side"]
    core_returns = screen(data, core_targets, cost).equity.pct_change().fillna(0.0)
    attack_returns = screen(data, attack_targets, cost).equity.pct_change().fillna(0.0)
    allocator = candidate["allocator"]
    mixed = multihorizon_two_sleeve_targets(
        core_targets,
        attack_targets,
        core_returns,
        attack_returns,
        windows_days=tuple(allocator["windows_days"]),
        funding_weight_when_leading=allocator["core_weight_when_leading"],
        funding_weight_when_lagging=allocator["core_weight_when_lagging"],
        rebalance_hours=allocator["rebalance_hours"],
    )
    mixed_proxy = screen(data, mixed, cost).equity
    convex = convex_equity_overlay(
        mixed,
        mixed_proxy,
        **candidate["convex_overlay"],
    )
    convex_proxy = screen(data, convex, cost).equity
    targets, diagnostics = trailing_profit_lock_targets(
        convex,
        convex_proxy,
        **candidate["profit_lock"],
    )
    data, targets, quarantined = apply_funding_quarantine(data, targets)
    execution = base_config["execution"]
    guard = candidate["circuit_breaker"]
    result = exact_fast(
        data,
        targets,
        cost_per_side=execution["base_cost_per_side"],
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=guard["gross_drift_guard_cap"],
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )
    return data, targets, result, diagnostics, quarantined


def main() -> None:
    candidate = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if candidate.get("real_orders") or candidate.get("mode") != "PAPER_ONLY":
        raise RuntimeError("V16 must remain PAPER_ONLY")
    if candidate.get("strict_research_gate") != "REJECTED":
        raise RuntimeError("V16 experimental disclosure was removed")

    data, targets, result, diagnostics, quarantined = build_v16(candidate)
    latest = data.close.index[-1]
    previous = load_state(candidate)
    initialized_at = (
        pd.Timestamp(previous["initialized_at_utc"])
        if previous
        else pd.Timestamp.now(tz="UTC")
    )
    paper_start = (
        pd.Timestamp(previous["paper_start_after_timestamp"])
        if previous
        else latest
    )
    snapshot = track_payload(
        "v16",
        candidate["name"],
        targets,
        result,
        initialized_at,
        paper_start,
        latest,
    )
    snapshot["disclosure"] = candidate["disclosure"]
    snapshot["experimental"] = True
    snapshot["strict_research_gate"] = candidate["strict_research_gate"]
    if latest < paper_start:
        ledger = empty_ledger("v16", candidate["name"], paper_start, latest)
    else:
        ledger = build_ledger(data, targets, result, paper_start, candidate["name"])
        ledger["track"] = "v16"
        ledger["status"] = snapshot["status"]
    ledger["experimental"] = True
    ledger["strict_research_gate"] = candidate["strict_research_gate"]
    latest_diagnostics = diagnostics.iloc[-1]
    state = {
        **snapshot,
        "candidate_version": candidate["version"],
        "frozen_revision": "balanced_relaxed",
        "funding_quarantined_symbols": quarantined,
        "risk_factor": float(latest_diagnostics["risk_factor"]),
        "profit_lock_active": bool(latest_diagnostics["profit_lock"]),
        "shock_brake_active": bool(latest_diagnostics["shock"]),
        "objective": "maximum compounded wealth under an experimental forward paper boundary",
    }
    write_json(STATE_PATH, state)
    write_json(SNAPSHOT_PATH, state)
    write_json(LEDGER_PATH, ledger)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
