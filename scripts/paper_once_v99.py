from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.v99 import V99AsymmetricSpec
from cryptoai_v13.v99_r2 import V99R2ControlSpec, asymmetric_v99_targets_r2
from paper_once_opportunity_v1 import empty_ledger, track_payload, write_json
from paper_once_v13 import build_ledger
from paper_once_v16 import build_v16


CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
STATE_PATH = PROJECT / "state" / "paper_v99_state.json"
SNAPSHOT_PATH = PROJECT / "reports" / "paper_v99_snapshot.json"
LEDGER_PATH = PROJECT / "reports" / "paper_v99_ledger.json"


def load_state(candidate: dict) -> dict | None:
    if not STATE_PATH.exists():
        return None
    value = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if value.get("candidate_version") != candidate["version"]:
        return None
    return value


def load_execution(parent: dict) -> dict:
    finalist = json.loads(
        (PROJECT / "config" / parent["frozen_core_config"]).read_text(encoding="utf-8")
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text(encoding="utf-8")
    )
    return base_config["execution"]


def build_v99(candidate: dict):
    parent = json.loads(
        (PROJECT / "config" / candidate["parent_candidate_config"]).read_text(
            encoding="utf-8"
        )
    )
    data, parent_targets, _, _, quarantined = build_v16(parent)
    execution = load_execution(parent)
    proxy_equity = screen(
        data,
        parent_targets,
        execution["base_cost_per_side"],
    ).equity
    targets, diagnostics = asymmetric_v99_targets_r2(
        data,
        parent_targets,
        proxy_equity,
        V99AsymmetricSpec(**candidate["asymmetric_overlay"]),
        V99R2ControlSpec(**candidate["r2_control"]),
    )
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
    return data, targets, result, diagnostics, quarantined, parent


def main() -> None:
    candidate = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if candidate.get("real_orders") or candidate.get("mode") != "PAPER_ONLY":
        raise RuntimeError("V99 must remain PAPER_ONLY")
    if candidate.get("strict_research_gate") != "UNVALIDATED":
        raise RuntimeError("V99 must remain explicitly unvalidated until research passes")

    data, targets, result, diagnostics, quarantined, parent = build_v99(candidate)
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
        "v99",
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
    snapshot["parent_candidate"] = parent["name"]

    if latest < paper_start:
        ledger = empty_ledger("v99", candidate["name"], paper_start, latest)
    else:
        ledger = build_ledger(data, targets, result, paper_start, candidate["name"])
        ledger["track"] = "v99"
        ledger["status"] = snapshot["status"]
    ledger["experimental"] = True
    ledger["strict_research_gate"] = candidate["strict_research_gate"]
    ledger["parent_candidate"] = parent["name"]

    latest_diagnostics = diagnostics.iloc[-1]
    opportunity_factor = (
        float(candidate["asymmetric_overlay"]["clean_trend_boost"])
        if bool(latest_diagnostics["boost_ready"])
        else 1.0
    )
    state = {
        **snapshot,
        "candidate_version": candidate["version"],
        "parent_candidate": parent["name"],
        "funding_quarantined_symbols": quarantined,
        "stress_score": int(latest_diagnostics["stress_score"]),
        "stress_factor": float(latest_diagnostics["stress_factor"]),
        "chop_active": bool(latest_diagnostics["chop_active"]),
        "chop_blocked_count": int(latest_diagnostics["chop_blocked_count"]),
        "damage_state": str(latest_diagnostics["damage_state"]),
        "smoothed_loss_fraction": float(latest_diagnostics["smoothed_loss_fraction"]),
        "extension_blocked_count": int(latest_diagnostics["extension_blocked_count"]),
        "risk_factor": float(latest_diagnostics["risk_factor"]),
        "opportunity_factor": opportunity_factor,
        "clean_trend": bool(latest_diagnostics["clean_trend"]),
        "objective": candidate["objective"],
    }
    write_json(STATE_PATH, state)
    write_json(SNAPSHOT_PATH, state)
    write_json(LEDGER_PATH, ledger)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
