from __future__ import annotations

import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((PROJECT / relative).read_text())


def main() -> None:
    config = load("config/candidate_v15_adaptive_capture.json")
    parent = load("config/candidate_v14_max_capture.json")
    state = load("state/paper_v15_state.json")
    universe = load("state/paper_v15_universe.json")
    sync = load("reports/paper_data_sync_v15.json")
    snapshot = load("reports/paper_v15_snapshot.json")
    ledger = load("reports/paper_v15_ledger.json")
    for value in (config, state, snapshot, ledger):
        if value.get("real_orders") or value.get("real_orders_enabled"):
            raise RuntimeError("V15 real-order lock failed")
    if config["mode"] != "PAPER_ONLY" or state["mode"] != "PAPER_ONLY":
        raise RuntimeError("V15 left PAPER_ONLY")
    if state["candidate_version"] != config["version"]:
        raise RuntimeError("V15 state/config version mismatch")
    if config["parent_candidate_config"] != "candidate_v14_max_capture.json":
        raise RuntimeError("V15 no longer derives from V14")
    if "allocation" in config or "circuit_breaker" in config:
        raise RuntimeError("V15 must inherit V14 allocation and circuit breaker")
    if not parent.get("allocation") or not parent.get("circuit_breaker"):
        raise RuntimeError("V14 parent risk configuration is incomplete")
    if state["paper_start_after_timestamp"] != ledger["paper_start_after_timestamp"]:
        raise RuntimeError("V15 paper boundaries differ")
    if ledger.get("track") != "v15" or ledger.get("schema_version") != 4:
        raise RuntimeError("V15 ledger invalid")
    if sync.get("private_api_used") is not False:
        raise RuntimeError("V15 data discovery is not public-only")
    if universe["candidate_version"] != config["version"]:
        raise RuntimeError("V15 universe/config version mismatch")
    if int(sync["ready_universe_size"]) < 20:
        raise RuntimeError("V15 ready universe is unexpectedly small")
    summary = ledger["summary"]
    if abs(
        float(summary["current_capital_brl"])
        - (10_000 + float(summary["net_result_brl"]))
    ) > 0.05:
        raise RuntimeError("V15 capital does not reconcile")
    print(
        json.dumps(
            {
                "status": state["status"],
                "candidate": config["name"],
                "parent": state["parent_candidate"],
                "ready_universe": sync["ready_universe_size"],
                "regime": state["v15_metadata"]["latest_direction_regime"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
