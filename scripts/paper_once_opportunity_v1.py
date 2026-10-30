from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import point_in_time_liquid_view
from cryptoai_v13.opportunity import (
    OpportunityBudget,
    additive_opportunity_targets,
)
from cryptoai_v13.signals import StrategySpec, build_targets
from paper_once_v13 import (
    PAPER_CAPITAL_BRL,
    apply_funding_quarantine,
    build_ledger,
    cap_targets,
    resolve_paper_start,
)
from run_final_candidate import build_candidate


STATE_PATH = PROJECT / "state" / "paper_opportunity_v1_state.json"
CORE_SNAPSHOT_PATH = PROJECT / "reports" / "paper_core_comparison_v1_snapshot.json"
OPPORTUNITY_SNAPSHOT_PATH = PROJECT / "reports" / "paper_opportunity_v1_snapshot.json"
COMBINED_SNAPSHOT_PATH = PROJECT / "reports" / "paper_combined_v1_snapshot.json"
CORE_LEDGER_PATH = PROJECT / "reports" / "paper_core_comparison_v1_ledger.json"
OPPORTUNITY_LEDGER_PATH = PROJECT / "reports" / "paper_opportunity_v1_ledger.json"
COMBINED_LEDGER_PATH = PROJECT / "reports" / "paper_combined_v1_ledger.json"
COMPARISON_PATH = PROJECT / "reports" / "paper_comparison_v1.json"


def load_state() -> dict | None:
    if not STATE_PATH.exists():
        return None
    return json.loads(STATE_PATH.read_text())


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def empty_breakdown() -> dict:
    return {
        "gross_result_brl": 0.0,
        "fees_brl": 0.0,
        "funding_result_brl": 0.0,
        "total_cost_brl": 0.0,
        "net_result_brl": 0.0,
    }


def empty_ledger(
    track: str,
    candidate: str,
    paper_start: pd.Timestamp,
    latest: pd.Timestamp,
) -> dict:
    return {
        "schema_version": 4,
        "mode": "PAPER_ONLY",
        "track": track,
        "candidate": candidate,
        "base_capital_brl": PAPER_CAPITAL_BRL,
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "status": "waiting_for_boundary",
        "summary": {
            "decision_events": 0,
            "position_adjustments": 0,
            "positioned_hours": 0,
            "positive_hours": 0,
            "negative_hours": 0,
            **empty_breakdown(),
            "current_capital_brl": PAPER_CAPITAL_BRL,
            "highest_capital_brl": PAPER_CAPITAL_BRL,
            "lowest_capital_brl": PAPER_CAPITAL_BRL,
        },
        "assets": {},
        "opening_snapshot": {
            "timestamp": paper_start.isoformat(),
            "positions": {},
            "explanation": "Aguardando o mercado ultrapassar a nova fronteira forward.",
        },
        "equity_curve": [],
        "candles": {},
        "decisions": [],
        "explanation": {
            "gross": "Resultado dos movimentos de preço antes de taxas e funding.",
            "cost": "Taxas mais funding pago, descontando funding recebido.",
            "net": "O que sobrou: bruto menos custos.",
            "open_positions": "Nenhuma posição forward é contada antes da nova fronteira.",
        },
    }


def track_payload(
    track: str,
    candidate: str,
    targets: pd.DataFrame,
    result,
    initialized_at: pd.Timestamp,
    paper_start: pd.Timestamp,
    latest: pd.Timestamp,
) -> dict:
    ready = latest >= paper_start
    if ready:
        forward = result.equity.loc[paper_start:]
        forward = forward / forward.iloc[0]
        new_hours = int((targets.index > paper_start).sum())
    else:
        forward = pd.Series(dtype=float)
        new_hours = 0
    positions = (
        {
            symbol: round(float(weight), 8)
            for symbol, weight in result.positions.iloc[-1].items()
            if abs(float(weight)) > 1e-8
        }
        if ready
        else {}
    )
    next_target = (
        {
            symbol: round(float(weight), 8)
            for symbol, weight in targets.iloc[-1].items()
            if abs(float(weight)) > 1e-8
        }
        if ready
        else {}
    )
    return {
        "mode": "PAPER_ONLY",
        "real_orders_enabled": False,
        "track": track,
        "candidate": candidate,
        "initialized_at_utc": initialized_at.isoformat(),
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "new_forward_hours": new_hours,
        "status": (
            "tracking"
            if ready and new_hours > 0
            else "waiting_for_new_data"
            if ready
            else "waiting_for_boundary"
        ),
        "forward_equity_multiple": (
            round(float(forward.iloc[-1]), 10) if len(forward) else 1.0
        ),
        "current_simulated_positions": positions,
        "target_for_next_open": next_target,
        "gross_exposure": (
            round(float(result.gross_exposure.iloc[-1]), 8) if ready else 0.0
        ),
        "disclosure": (
            "This track shares one new forward boundary with the other comparison "
            "tracks. It has no exchange credentials or order methods."
        ),
    }


def build_track_ledger(
    track: str,
    candidate: str,
    data,
    targets: pd.DataFrame,
    result,
    paper_start: pd.Timestamp,
    latest: pd.Timestamp,
) -> dict:
    if latest < paper_start:
        return empty_ledger(track, candidate, paper_start, latest)
    ledger = build_ledger(data, targets, result, paper_start, candidate)
    ledger["track"] = track
    ledger["status"] = (
        "tracking" if int((data.close.index > paper_start).sum()) > 0 else "waiting_for_new_data"
    )
    return ledger


def main() -> None:
    candidate = json.loads(
        (PROJECT / "config" / "candidate_opportunity_overlay_v1.json").read_text()
    )
    if not candidate["paper"]["active"] or candidate["real_orders"]:
        raise RuntimeError("candidate is not authorized for PAPER_ONLY tracking")
    finalist = json.loads(
        (PROJECT / "config" / candidate["frozen_core_config"]).read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    data, core_targets, _, _ = build_candidate(base_config)
    core_targets = cap_targets(core_targets, finalist["target_cap"])
    data, core_targets, quarantined = apply_funding_quarantine(data, core_targets)

    universe = base_config["point_in_time_universe"]
    signal_data, _ = point_in_time_liquid_view(
        data,
        top_n=universe["top_n"],
        lookback_hours=universe["quote_volume_lookback_hours"],
        minimum_history_hours=universe["minimum_history_hours"],
    )
    base_spec = StrategySpec(**candidate["opportunity"]["spec"])
    phases = candidate["opportunity"]["equal_weight_rebalance_phases"]
    raw_opportunity = sum(
        build_targets(signal_data, replace(base_spec, rebalance_phase=phase))
        for phase in phases
    ) / len(phases)
    allocation = candidate["allocation"]
    combined_targets, opportunity_targets = additive_opportunity_targets(
        core_targets,
        raw_opportunity,
        OpportunityBudget(
            allocation["maximum_overlay_gross"],
            allocation["maximum_portfolio_gross"],
        ),
    )

    execution = base_config["execution"]
    guard = candidate["shared_circuit_breaker"]
    replay_kwargs = {
        "cost_per_side": execution["base_cost_per_side"],
        "maintenance_equity_fraction": execution["maintenance_equity_fraction"],
        "drawdown_guard_threshold": guard["drawdown_threshold"],
        "drawdown_guard_multiplier": guard["exposure_multiplier"],
        "drawdown_guard_cooldown_hours": guard["cooldown_hours"],
    }
    core_result = exact_fast(
        data,
        core_targets,
        gross_guard_cap=finalist["gross_guard_cap"],
        **replay_kwargs,
    )
    opportunity_result = exact_fast(
        data,
        opportunity_targets,
        gross_guard_cap=(
            allocation["maximum_overlay_gross"]
            + allocation["gross_drift_guard_allowance"]
        ),
        **replay_kwargs,
    )
    combined_result = exact_fast(
        data,
        combined_targets,
        gross_guard_cap=allocation["gross_drift_guard_cap"],
        **replay_kwargs,
    )

    latest = data.close.index[-1]
    previous = load_state()
    initialized_at = (
        pd.Timestamp(previous["initialized_at_utc"])
        if previous
        else pd.Timestamp.now(tz="UTC")
    )
    paper_start = resolve_paper_start(previous, initialized_at, latest)
    definitions = (
        (
            "core",
            "Núcleo V13 — mesmo período",
            core_targets,
            core_result,
            CORE_SNAPSHOT_PATH,
            CORE_LEDGER_PATH,
        ),
        (
            "opportunity",
            "Oportunidades V1 — tamanho alocado",
            opportunity_targets,
            opportunity_result,
            OPPORTUNITY_SNAPSHOT_PATH,
            OPPORTUNITY_LEDGER_PATH,
        ),
        (
            "combined",
            candidate["name"],
            combined_targets,
            combined_result,
            COMBINED_SNAPSHOT_PATH,
            COMBINED_LEDGER_PATH,
        ),
    )

    snapshots = {}
    ledgers = {}
    for track, name, targets, result, snapshot_path, ledger_path in definitions:
        snapshot = track_payload(
            track,
            name,
            targets,
            result,
            initialized_at,
            paper_start,
            latest,
        )
        ledger = build_track_ledger(
            track,
            name,
            data,
            targets,
            result,
            paper_start,
            latest,
        )
        snapshots[track] = snapshot
        ledgers[track] = ledger
        write_json(snapshot_path, snapshot)
        write_json(ledger_path, ledger)

    control = {
        "mode": "PAPER_ONLY",
        "real_orders_enabled": False,
        "candidate": candidate["name"],
        "initialized_at_utc": initialized_at.isoformat(),
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "status": snapshots["combined"]["status"],
        "funding_quarantined_symbols": quarantined,
        "tracks": snapshots,
    }
    comparison = {
        "schema_version": 1,
        "mode": "PAPER_ONLY",
        "real_orders_enabled": False,
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "status": snapshots["combined"]["status"],
        "funding_quarantined_symbols": quarantined,
        "tracks": {
            track: {
                "candidate": ledger["candidate"],
                "summary": ledger["summary"],
                "open_positions": sum(
                    asset["status"] == "open"
                    for asset in ledger.get("assets", {}).values()
                ),
            }
            for track, ledger in ledgers.items()
        },
        "explanation": {
            "core": "A V13 sozinha, reiniciada apenas para uma comparação justa.",
            "opportunity": "Somente o turbo de oportunidades no tamanho realmente alocado.",
            "combined": "O patrimônio que teríamos usando V13 e oportunidades juntas.",
        },
    }
    write_json(STATE_PATH, control)
    write_json(COMPARISON_PATH, comparison)
    print(json.dumps(control, indent=2))


if __name__ == "__main__":
    main()
