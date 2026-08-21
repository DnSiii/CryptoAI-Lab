from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import point_in_time_liquid_view
from cryptoai_v13.opportunity import OpportunityBudget, additive_opportunity_targets
from cryptoai_v13.signals import StrategySpec, build_targets
from paper_once_opportunity_v1 import empty_ledger, track_payload, write_json
from paper_once_v13 import apply_funding_quarantine, build_ledger, cap_targets
from run_final_candidate import build_candidate


CONFIG_PATH = PROJECT / "config" / "candidate_v14_max_capture.json"
STATE_PATH = PROJECT / "state" / "paper_v14_state.json"
SNAPSHOT_PATH = PROJECT / "reports" / "paper_v14_snapshot.json"
LEDGER_PATH = PROJECT / "reports" / "paper_v14_ledger.json"


def load_state() -> dict | None:
    if not STATE_PATH.exists():
        return None
    value = json.loads(STATE_PATH.read_text())
    candidate = json.loads(CONFIG_PATH.read_text())
    if value.get("candidate_version") != candidate["version"]:
        return None
    return value


def main() -> None:
    candidate = json.loads(CONFIG_PATH.read_text())
    if candidate.get("real_orders") or candidate.get("mode") != "PAPER_ONLY":
        raise RuntimeError("V14 must remain PAPER_ONLY")
    finalist = json.loads(
        (PROJECT / "config" / candidate["frozen_core_config"]).read_text()
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
    raw_opportunity = build_targets(
        signal_data, StrategySpec(**candidate["opportunity"]["spec"])
    )
    allocation = candidate["allocation"]
    combined_targets, _ = additive_opportunity_targets(
        core_targets,
        raw_opportunity,
        OpportunityBudget(
            allocation["maximum_overlay_gross"],
            allocation["maximum_portfolio_gross"],
        ),
    )
    data, combined_targets, quarantined = apply_funding_quarantine(
        data, combined_targets
    )
    guard = candidate["circuit_breaker"]
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
    latest = data.close.index[-1]
    previous = load_state()
    initialized_at = (
        pd.Timestamp(previous["initialized_at_utc"])
        if previous
        else pd.Timestamp.now(tz="UTC")
    )
    # Freeze at the newest verified market candle, not at wall-clock time.  The
    # public daily archive can lag the clock; using "now" would keep a correct
    # new paper at zero longer than necessary.
    paper_start = (
        pd.Timestamp(previous["paper_start_after_timestamp"])
        if previous
        else latest
    )
    snapshot = track_payload(
        "v14",
        candidate["name"],
        combined_targets,
        result,
        initialized_at,
        paper_start,
        latest,
    )
    snapshot["disclosure"] = (
        "V14 uses its own new forward boundary. It has no exchange credentials "
        "or order methods, and no historical result is counted as paper profit."
    )
    if latest < paper_start:
        ledger = empty_ledger("v14", candidate["name"], paper_start, latest)
    else:
        ledger = build_ledger(
            data, combined_targets, result, paper_start, candidate["name"]
        )
        ledger["track"] = "v14"
        ledger["status"] = snapshot["status"]
    state = {
        **snapshot,
        "candidate_version": candidate["version"],
        "funding_quarantined_symbols": quarantined,
        "objective": "maximum compounded wealth without a return ceiling",
    }
    write_json(STATE_PATH, state)
    write_json(SNAPSHOT_PATH, state)
    write_json(LEDGER_PATH, ledger)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
