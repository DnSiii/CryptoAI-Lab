from __future__ import annotations

import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((PROJECT / relative).read_text())


def main() -> None:
    config = load("config/candidate_v14_max_capture.json")
    state = load("state/paper_v14_state.json")
    snapshot = load("reports/paper_v14_snapshot.json")
    ledger = load("reports/paper_v14_ledger.json")
    for value in (config, state, snapshot, ledger):
        if value.get("real_orders") or value.get("real_orders_enabled"):
            raise RuntimeError("V14 real-order lock failed")
    if config["mode"] != "PAPER_ONLY" or state["mode"] != "PAPER_ONLY":
        raise RuntimeError("V14 left PAPER_ONLY")
    if state["candidate_version"] != config["version"]:
        raise RuntimeError("V14 state/config version mismatch")
    if state["paper_start_after_timestamp"] != ledger["paper_start_after_timestamp"]:
        raise RuntimeError("V14 paper boundaries differ")
    if ledger.get("track") != "v14" or ledger.get("schema_version") != 4:
        raise RuntimeError("V14 ledger invalid")
    summary = ledger["summary"]
    if abs(float(summary["current_capital_brl"]) - (10_000 + float(summary["net_result_brl"]))) > 0.05:
        raise RuntimeError("V14 capital does not reconcile")
    print(json.dumps({"status": state["status"], "candidate": config["name"]}, indent=2))


if __name__ == "__main__":
    main()
