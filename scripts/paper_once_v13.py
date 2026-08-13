from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from run_canonical_risk_stress import cap_targets
from run_final_candidate import build_candidate


STATE_PATH = PROJECT / "state" / "paper_v13_state.json"
SNAPSHOT_PATH = PROJECT / "reports" / "paper_v13_snapshot.json"


def load_state() -> dict | None:
    if not STATE_PATH.exists():
        return None
    return json.loads(STATE_PATH.read_text())


def checkpoint(payload: dict) -> None:
    STATE_PATH.parent.mkdir(exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    SNAPSHOT_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    finalist = json.loads(
        (PROJECT / "config" / "candidate_v13_circuit_breaker.json").read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    data, targets, _, _ = build_candidate(base_config)
    targets = cap_targets(targets, finalist["target_cap"])
    execution = base_config["execution"]
    guard = finalist["circuit_breaker"]
    result = exact_fast(
        data,
        targets,
        execution["base_cost_per_side"],
        execution["maintenance_equity_fraction"],
        gross_guard_cap=finalist["gross_guard_cap"],
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
    honest_forward_boundary = max(latest, initialized_at.floor("h"))
    if previous:
        previous_boundary = pd.Timestamp(previous["paper_start_after_timestamp"])
        paper_start = (
            max(previous_boundary, honest_forward_boundary)
            if int(previous.get("new_forward_hours", 0)) == 0
            else previous_boundary
        )
    else:
        paper_start = honest_forward_boundary
    forward_equity = result.equity.loc[paper_start:]
    if len(forward_equity):
        forward_equity = forward_equity / forward_equity.iloc[0]
    new_hours = int((data.close.index > paper_start).sum())
    nonzero_positions = {
        symbol: round(float(weight), 8)
        for symbol, weight in result.positions.iloc[-1].items()
        if abs(float(weight)) > 1e-8
    }
    next_target = {
        symbol: round(float(weight), 8)
        for symbol, weight in targets.iloc[-1].items()
        if abs(float(weight)) > 1e-8
    }
    payload = {
        "mode": "PAPER_ONLY",
        "real_orders_enabled": False,
        "candidate": finalist["name"],
        "initialized_at_utc": initialized_at.isoformat(),
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "new_forward_hours": new_hours,
        "status": "tracking" if new_hours > 0 else "waiting_for_new_data",
        "forward_equity_multiple": (
            round(float(forward_equity.iloc[-1]), 10)
            if len(forward_equity)
            else 1.0
        ),
        "current_simulated_positions": nonzero_positions,
        "target_for_next_open": next_target,
        "gross_exposure": round(float(result.gross_exposure.iloc[-1]), 8),
        "disclosure": (
            "No exchange order method exists in this runner. The paper ledger "
            "only counts timestamps strictly newer than the model-freeze hour; "
            "later backfills from before that hour are excluded."
        ),
    }
    checkpoint(payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
