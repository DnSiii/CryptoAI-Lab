from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.v99 import V99AsymmetricSpec
from cryptoai_v13.v99_frozen import build_frozen_v99
from cryptoai_v13.v99_r4 import V99R4ControlSpec
from paper_once_opportunity_v1 import write_json
from paper_once_v16 import build_v16

CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
STATE_PATH = PROJECT / "state" / "paper_v99_state.json"
SNAPSHOT_PATH = PROJECT / "reports" / "paper_v99_snapshot.json"
LEDGER_PATH = PROJECT / "reports" / "paper_v99_ledger.json"


def load_state(candidate: dict) -> dict | None:
    if not STATE_PATH.exists():
        return None
    value = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return value if value.get("candidate_version") == candidate["version"] else None


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
    data, parent_targets, parent_result, _, quarantined = build_v16(parent)
    execution = load_execution(parent)
    frozen = build_frozen_v99(
        data,
        parent_targets,
        parent_result,
        execution,
        V99AsymmetricSpec(**candidate["asymmetric_overlay"]),
        V99R4ControlSpec(**candidate["r4_control"]),
    )
    return data, frozen, parent, quarantined


def _positions_payload(row: pd.Series, capital_brl: float) -> dict[str, dict]:
    output = {}
    for symbol, value in row.items():
        weight = float(value)
        if abs(weight) <= 1e-8:
            continue
        output[symbol] = {
            "direction": "buy" if weight > 0 else "sell",
            "current_weight": round(weight, 8),
            "position_value_brl": round(abs(weight) * capital_brl, 2),
        }
    return output


def _ledger(candidate: dict, frozen, paper_start: pd.Timestamp, latest: pd.Timestamp) -> dict:
    initial_capital = float(candidate["paper"]["initial_capital_brl"])
    base_equity = float(frozen.equity.loc[paper_start])
    window = frozen.equity.loc[paper_start:latest]
    normalized = window.div(base_equity)
    curve = []
    previous_capital = initial_capital
    for timestamp, multiple in normalized.items():
        capital = initial_capital * float(multiple)
        hour_result = capital - previous_capital if curve else 0.0
        curve.append(
            {
                "timestamp": timestamp.isoformat(),
                "equity_multiple": round(float(multiple), 10),
                "capital_brl": round(capital, 2),
                "hour_result_brl": round(hour_result, 2),
            }
        )
        previous_capital = capital
    current = initial_capital * float(normalized.iloc[-1])
    positions = _positions_payload(frozen.positions.loc[latest], current)
    return {
        "schema_version": 5,
        "mode": "PAPER_ONLY",
        "track": "v99",
        "candidate": candidate["name"],
        "candidate_version": candidate["version"],
        "base_capital_brl": initial_capital,
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "summary": {
            "new_forward_hours": max(0, len(window) - 1),
            "net_result_brl": round(current - initial_capital, 2),
            "current_capital_brl": round(current, 2),
            "highest_capital_brl": round(initial_capital * float(normalized.max()), 2),
            "lowest_capital_brl": round(initial_capital * float(normalized.min()), 2),
            "forward_return_pct": round((float(normalized.iloc[-1]) - 1.0) * 100.0, 6),
        },
        "assets": positions,
        "equity_curve": curve,
        "composite": {
            "architecture": candidate["frozen_composite"]["architecture"],
            "satellite_realized_weight": round(float(frozen.satellite_weight.loc[latest]), 8),
            "satellite_target_weight": round(float(frozen.target_satellite_weight.loc[latest]), 8),
            "consensus_vote_fraction": round(float(frozen.vote_fraction.loc[latest]), 8),
            "maximum_satellite_weight": candidate["frozen_composite"]["maximum_satellite_weight"],
            "rebalance_hours": candidate["frozen_composite"]["rebalance_hours"],
            "note": "Core and alpha sleeves retain independent backtest state; transfer costs are embedded in the composite equity curve.",
        },
        "strict_research_gate": candidate["strict_research_gate"],
        "real_orders_enabled": False,
    }


def main() -> None:
    candidate = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if candidate.get("real_orders") or candidate.get("mode") != "PAPER_ONLY":
        raise RuntimeError("V99 must remain PAPER_ONLY")
    if candidate.get("strict_research_gate") != "BACKTEST_VALIDATED_FORWARD_PENDING":
        raise RuntimeError("V99 frozen forward status is inconsistent")

    data, frozen, parent, quarantined = build_v99(candidate)
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
    ledger = _ledger(candidate, frozen, paper_start, latest)
    current_multiple = ledger["summary"]["current_capital_brl"] / float(
        candidate["paper"]["initial_capital_brl"]
    )
    current_positions = {
        symbol: item["current_weight"] for symbol, item in ledger["assets"].items()
    }
    state = {
        "mode": "PAPER_ONLY",
        "real_orders_enabled": False,
        "track": "v99",
        "candidate": candidate["name"],
        "candidate_version": candidate["version"],
        "initialized_at_utc": initialized_at.isoformat(),
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "new_forward_hours": ledger["summary"]["new_forward_hours"],
        "status": "tracking" if latest > paper_start else "initialized",
        "forward_equity_multiple": round(float(current_multiple), 10),
        "current_simulated_positions": current_positions,
        "gross_exposure": round(sum(abs(v) for v in current_positions.values()), 8),
        "parent_candidate": parent["name"],
        "architecture": candidate["frozen_composite"]["architecture"],
        "satellite_realized_weight": ledger["composite"]["satellite_realized_weight"],
        "satellite_target_weight": ledger["composite"]["satellite_target_weight"],
        "consensus_vote_fraction": ledger["composite"]["consensus_vote_fraction"],
        "funding_quarantined_symbols": quarantined,
        "strict_research_gate": candidate["strict_research_gate"],
        "forward_validation": "PENDING_INDEPENDENT_DATA",
        "objective": candidate["objective"],
        "disclosure": candidate["disclosure"],
        "experimental": True,
    }
    write_json(STATE_PATH, state)
    write_json(SNAPSHOT_PATH, state)
    write_json(LEDGER_PATH, ledger)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
