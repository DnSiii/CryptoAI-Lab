from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import FuturesData, load_data, point_in_time_liquid_view
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from cryptoai_v13.signals import StrategySpec, build_targets
from cryptoai_v13.v15 import (
    DirectionAllocatorSpec,
    adaptive_directional_targets,
    apply_eligibility_boundaries,
)
from paper_once_opportunity_v1 import empty_ledger, track_payload, write_json
from paper_once_v13 import apply_funding_quarantine, build_ledger, cap_targets
from run_final_candidate import build_candidate


CONFIG_PATH = PROJECT / "config" / "candidate_v15_adaptive_capture.json"
RUNTIME_CONFIG_PATH = PROJECT / "config" / "research_v15_runtime.json"
UNIVERSE_STATE_PATH = PROJECT / "state" / "paper_v15_universe.json"
SYNC_REPORT_PATH = PROJECT / "reports" / "paper_data_sync_v15.json"
STATE_PATH = PROJECT / "state" / "paper_v15_state.json"
SNAPSHOT_PATH = PROJECT / "reports" / "paper_v15_snapshot.json"
LEDGER_PATH = PROJECT / "reports" / "paper_v15_ledger.json"


def load_state(candidate_version: str) -> dict | None:
    if not STATE_PATH.exists():
        return None
    value = json.loads(STATE_PATH.read_text())
    return value if value.get("candidate_version") == candidate_version else None


def trim_data(data: FuturesData, latest: pd.Timestamp) -> FuturesData:
    frames = {name: frame.loc[:latest].copy() for name, frame in data.frames.items()}
    return FuturesData(
        frames=frames,
        funding=data.funding.loc[:latest].copy(),
        symbols=data.symbols,
    )


def build_v15() -> tuple[
    dict,
    FuturesData,
    pd.DataFrame,
    object,
    pd.Series,
    list[str],
    dict,
]:
    candidate = json.loads(CONFIG_PATH.read_text())
    if candidate.get("real_orders") or candidate.get("mode") != "PAPER_ONLY":
        raise RuntimeError("V15 must remain PAPER_ONLY")
    if not RUNTIME_CONFIG_PATH.exists() or not UNIVERSE_STATE_PATH.exists():
        raise RuntimeError("V15 dynamic universe was not prepared")
    parent = json.loads(
        (PROJECT / "config" / candidate["parent_candidate_config"]).read_text()
    )
    finalist = json.loads(
        (PROJECT / "config" / parent["frozen_core_config"]).read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    _, core_targets, _, _ = build_candidate(base_config)
    data = load_data(PROJECT, RUNTIME_CONFIG_PATH.name)
    sync = json.loads(SYNC_REPORT_PATH.read_text())
    latest = pd.Timestamp(sync["expected_latest_closed_hour"])
    data = trim_data(data, latest)

    core_targets = cap_targets(core_targets, finalist["target_cap"])
    core_targets = core_targets.reindex(
        index=data.close.index,
        columns=data.close.columns,
    ).fillna(0.0)
    universe = candidate["dynamic_universe"]
    signal_data, _ = point_in_time_liquid_view(
        data,
        top_n=int(universe["point_in_time_liquid_top_n"]),
        lookback_hours=int(universe["quote_volume_lookback_hours"]),
        minimum_history_hours=int(universe["minimum_history_hours"]),
    )
    opportunity_spec = dict(parent["opportunity"]["spec"])
    opportunity_spec["long_short_balance"] = float(
        candidate["direction_allocator"]["base_long_short_balance"]
    )
    raw_opportunity = build_targets(
        signal_data, StrategySpec(**opportunity_spec)
    )
    universe_state = json.loads(UNIVERSE_STATE_PATH.read_text())
    eligible_after = {
        symbol: item["eligible_after_timestamp"]
        for symbol, item in universe_state["symbols"].items()
        if "eligible_after_timestamp" in item
    }
    raw_opportunity = apply_eligibility_boundaries(
        raw_opportunity, eligible_after
    )
    direction_values = dict(candidate["direction_allocator"])
    direction_values.pop("base_long_short_balance", None)
    direction_spec = DirectionAllocatorSpec(**direction_values)
    adaptive_opportunity, regime = adaptive_directional_targets(
        raw_opportunity,
        data.close[direction_spec.market_symbol],
        direction_spec,
    )
    allocation = parent["allocation"]
    combined_targets, allocated = additive_opportunity_targets(
        core_targets,
        adaptive_opportunity,
        OpportunityBudget(
            allocation["maximum_overlay_gross"],
            allocation["maximum_portfolio_gross"],
        ),
    )
    data, combined_targets, quarantined = apply_funding_quarantine(
        data,
        combined_targets,
        report_path=SYNC_REPORT_PATH,
    )
    guard = parent["circuit_breaker"]
    execution = base_config["execution"]
    result = exact_fast(
        data,
        combined_targets,
        cost_per_side=execution["base_cost_per_side"],
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=allocation["gross_drift_guard_cap"],
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )
    metadata = {
        "parent_candidate": parent["name"],
        "persistent_universe_size": len(universe_state["symbols"]),
        "ready_universe_size": len(data.symbols),
        "liquid_top_n": universe["point_in_time_liquid_top_n"],
        "latest_direction_regime": str(regime.loc[latest]),
        "allocated_opportunity_gross": round(
            float(allocated.loc[latest].abs().sum()), 8
        ),
    }
    return candidate, data, combined_targets, result, regime, quarantined, metadata


def main() -> None:
    candidate, data, targets, result, _, quarantined, metadata = build_v15()
    latest = data.close.index[-1]
    previous = load_state(candidate["version"])
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
        "v15",
        candidate["name"],
        targets,
        result,
        initialized_at,
        paper_start,
        latest,
    )
    snapshot["disclosure"] = (
        "V15 is a V14-derived challenger with its own forward boundary. "
        "It has no exchange credentials or real-order methods."
    )
    if latest < paper_start:
        ledger = empty_ledger("v15", candidate["name"], paper_start, latest)
    else:
        ledger = build_ledger(
            data, targets, result, paper_start, candidate["name"]
        )
        ledger["track"] = "v15"
        ledger["status"] = snapshot["status"]
        ledger["v15_metadata"] = metadata
    state = {
        **snapshot,
        "candidate_version": candidate["version"],
        "parent_candidate": metadata["parent_candidate"],
        "funding_quarantined_symbols": quarantined,
        "objective": "maximum compounded wealth without a return ceiling",
        "v15_metadata": metadata,
    }
    write_json(STATE_PATH, state)
    write_json(SNAPSHOT_PATH, state)
    write_json(LEDGER_PATH, ledger)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
