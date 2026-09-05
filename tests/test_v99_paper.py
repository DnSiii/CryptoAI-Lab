from __future__ import annotations

import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def test_v99_is_independent_experimental_and_orderless() -> None:
    config = json.loads(
        (PROJECT / "config" / "candidate_v99_asymmetric.json").read_text()
    )
    runner = (PROJECT / "scripts" / "paper_once_v99.py").read_text()
    assert config["mode"] == "PAPER_ONLY"
    assert config["real_orders"] is False
    assert config["strict_research_gate"] == "UNVALIDATED"
    assert config["paper"]["independent_forward_boundary"] is True
    assert config["paper"]["preserve_existing_tracks"] == [
        "v13",
        "v14",
        "v15",
        "v16",
    ]
    for forbidden in ("create_order", "apiKey", "api_secret", "client_secret"):
        assert forbidden not in runner


def test_v99_gate_demands_both_tail_improvement_and_winner_capture() -> None:
    config = json.loads(
        (PROJECT / "config" / "candidate_v99_asymmetric.json").read_text()
    )
    gate = config["research_gate"]
    assert gate["all_required_horizons_positive"] is True
    assert gate["full_return_must_beat_parent"] is True
    assert gate["max_drawdown_improvement_fraction"] >= 0.15
    assert gate["worst_day_loss_improvement_fraction"] >= 0.20
    assert gate["top_winner_capture_minimum"] >= 0.85


def test_v99_research_workflow_runs_the_strict_runner() -> None:
    workflow = (PROJECT / ".github" / "workflows" / "v99-research.yml").read_text()
    assert "pull_request:" in workflow
    assert "python -m pytest" in workflow
    assert "python scripts/run_candidate_v99.py" in workflow


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
