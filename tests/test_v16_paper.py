from __future__ import annotations

import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def test_v16_paper_is_independent_experimental_and_orderless() -> None:
    config = json.loads(
        (PROJECT / "config" / "candidate_v16_experimental_balanced_relaxed.json").read_text()
    )
    runner = (PROJECT / "scripts" / "paper_once_v16.py").read_text()
    assert config["mode"] == "PAPER_ONLY"
    assert config["real_orders"] is False
    assert config["strict_research_gate"] == "REJECTED"
    assert config["paper"]["independent_forward_boundary"] is True
    assert config["paper"]["preserve_existing_tracks"] == ["v13", "v14", "v15"]
    for forbidden in ("create_order", "apiKey", "api_secret", "client_secret"):
        assert forbidden not in runner


def test_v16_paper_freezes_the_balanced_relaxed_candidate() -> None:
    config = json.loads(
        (PROJECT / "config" / "candidate_v16_experimental_balanced_relaxed.json").read_text()
    )
    assert config["allocator"]["windows_days"] == [45, 90, 180]
    assert config["allocator"]["core_weight_when_leading"] == 0.7
    assert config["allocator"]["core_weight_when_lagging"] == 0.1
    assert config["profit_lock"]["profit_pullback"] == 0.0275
    assert config["circuit_breaker"]["drawdown_threshold"] == 0.058


def test_workflow_runs_and_publishes_v16_without_removing_existing_tracks() -> None:
    workflow = (PROJECT / ".github" / "workflows" / "v13-paper.yml").read_text()
    for required in (
        "paper_once_v13.py",
        "paper_once_v14.py",
        "paper_once_v15.py",
        "paper_once_v16.py",
        "verify_v16_cycle.py",
        "paper_v16_state.json",
        "paper_v16_ledger.json",
    ):
        assert required in workflow
