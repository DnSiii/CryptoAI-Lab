from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((PROJECT / relative).read_text(encoding="utf-8"))


def main() -> None:
    config = load("config/candidate_v99_asymmetric.json")
    state = load("state/paper_v99_state.json")
    snapshot = load("reports/paper_v99_snapshot.json")
    ledger = load("reports/paper_v99_ledger.json")
    for value in (config, state, snapshot, ledger):
        if value.get("real_orders") or value.get("real_orders_enabled"):
            raise RuntimeError("V99 real-order lock failed")
    if config["mode"] != "PAPER_ONLY" or state["mode"] != "PAPER_ONLY":
        raise RuntimeError("V99 left PAPER_ONLY")
    if config["strict_research_gate"] != "BACKTEST_VALIDATED_FORWARD_PENDING":
        raise RuntimeError("V99 frozen validation status was misrepresented")
    if not state.get("experimental"):
        raise RuntimeError("V99 frozen disclosure missing")
    if state["candidate_version"] != config["version"]:
        raise RuntimeError("V99 state/config version mismatch")
    if state["paper_start_after_timestamp"] != ledger["paper_start_after_timestamp"]:
        raise RuntimeError("V99 paper boundaries differ")
    if ledger.get("track") != "v99" or ledger.get("schema_version") != 5:
        raise RuntimeError("V99 frozen composite ledger invalid")
    if ledger.get("candidate_version") != config["version"]:
        raise RuntimeError("V99 ledger/config version mismatch")
    summary = ledger["summary"]
    expected = config["paper"]["initial_capital_brl"] + float(summary["net_result_brl"])
    if abs(float(summary["current_capital_brl"]) - expected) > 0.05:
        raise RuntimeError("V99 capital does not reconcile")
    composite = ledger.get("composite", {})
    maximum = float(config["frozen_composite"]["maximum_satellite_weight"])
    if float(composite.get("satellite_realized_weight", 0.0)) > maximum + 0.01:
        raise RuntimeError("V99 satellite exceeded frozen allocation cap")
    if config["paper"]["preserve_existing_tracks"] != ["v13", "v14", "v15", "v16"]:
        raise RuntimeError("V99 must preserve every existing robot track")
    print(
        json.dumps(
            {
                "status": state["status"],
                "candidate": config["name"],
                "forward_validation": state["forward_validation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
