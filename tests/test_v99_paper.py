from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def test_v99_is_frozen_forward_only_and_orderless() -> None:
    config = json.loads((PROJECT / "config" / "candidate_v99_asymmetric.json").read_text())
    runner = (PROJECT / "scripts" / "paper_once_v99.py").read_text()
    assert config["mode"] == "PAPER_ONLY"
    assert config["real_orders"] is False
    assert config["strict_research_gate"] == "BACKTEST_VALIDATED_FORWARD_PENDING"
    assert config["frozen_composite"]["freeze_gate"] == "R16_PASS"
    assert config["frozen_composite"]["maximum_satellite_weight"] == 0.10
    assert config["frozen_composite"]["rebalance_hours"] == 720
    assert config["paper"]["independent_forward_boundary"] is True
    assert config["paper"]["historical_results_count_as_paper_profit"] is False
    assert config["paper"]["preserve_existing_tracks"] == ["v13", "v14", "v15", "v16"]
    for forbidden in ("create_order", "apiKey", "api_secret", "client_secret"):
        assert forbidden not in runner


def test_v99_frozen_gate_keeps_required_and_anti_overfit_horizons() -> None:
    config = json.loads((PROJECT / "config" / "candidate_v99_asymmetric.json").read_text())
    gate = config["research_gate"]
    assert gate["required_horizons_days"] == [7, 30, 90, 180, 365]
    assert set(gate["anti_overfit_horizons_days"]) >= {14, 21, 45, 60, 120, 240, 540}
    assert gate["required_horizon_drawdown_ratio_max"] <= 1.03
    assert gate["top_winner_capture_minimum"] >= 0.99
    assert gate["severe_cost_must_beat_parent"] is True


def test_v99_frozen_module_has_consensus_and_persistence_contract() -> None:
    frozen = (PROJECT / "src" / "cryptoai_v13" / "v99_frozen.py").read_text()
    assert "VOTE_WINDOWS_DAYS = (45, 60, 90, 120, 180, 240)" in frozen
    assert "FROZEN_MAX_SATELLITE = 0.10" in frozen
    assert "FROZEN_REBALANCE_HOURS = 24 * 30" in frozen
    assert "FROZEN_ROUTINE_PERSISTENCE_HOURS = 4" in frozen
    assert "_sparse_side_shock" in frozen


def test_paper_workflow_runs_and_publishes_v99_without_removing_existing_tracks() -> None:
    workflow = (PROJECT / ".github" / "workflows" / "v13-paper.yml").read_text()
    for required in (
        "paper_once_v13.py",
        "paper_once_v14.py",
        "paper_once_v15.py",
        "paper_once_v16.py",
        "paper_once_v99.py",
        "verify_v99_cycle.py",
        "paper_v99_state.json",
        "paper_v99_ledger.json",
    ):
        assert required in workflow


def test_dashboard_has_live_paper_and_historical_simulator() -> None:
    html = (PROJECT / "dashboard" / "index.html").read_text()
    app = (PROJECT / "dashboard" / "app_v2.js").read_text()
    workflow = (PROJECT / ".github" / "workflows" / "cryptoai-dashboard.yml").read_text()
    assert "Backtest Simulator" in html
    assert "V99 FROZEN" in html
    assert "paper-results/dashboard/dashboard_data.json" in app
    assert "build_cryptoai_dashboard.py" in workflow
