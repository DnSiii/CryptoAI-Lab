from __future__ import annotations

import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((PROJECT / relative).read_text(encoding="utf-8"))


def main() -> None:
    config = load("config/candidate_v16_experimental_balanced_relaxed.json")
    state = load("state/paper_v16_state.json")
    snapshot = load("reports/paper_v16_snapshot.json")
    ledger = load("reports/paper_v16_ledger.json")
    for value in (config, state, snapshot, ledger):
        if value.get("real_orders") or value.get("real_orders_enabled"):
            raise RuntimeError("V16 real-order lock failed")
    if config["mode"] != "PAPER_ONLY" or state["mode"] != "PAPER_ONLY":
        raise RuntimeError("V16 left PAPER_ONLY")
    if config["strict_research_gate"] != "REJECTED":
        raise RuntimeError("V16 experimental status was misrepresented")
    if not state.get("experimental") or not ledger.get("experimental"):
        raise RuntimeError("V16 experimental disclosure missing")
    if state["candidate_version"] != config["version"]:
        raise RuntimeError("V16 state/config version mismatch")
    if state["paper_start_after_timestamp"] != ledger["paper_start_after_timestamp"]:
        raise RuntimeError("V16 paper boundaries differ")
    if ledger.get("track") != "v16" or ledger.get("schema_version") != 4:
        raise RuntimeError("V16 ledger invalid")
    summary = ledger["summary"]
    expected = config["paper"]["initial_capital_brl"] + float(summary["net_result_brl"])
    if abs(float(summary["current_capital_brl"]) - expected) > 0.05:
        raise RuntimeError("V16 capital does not reconcile")
    if config["paper"]["preserve_existing_tracks"] != ["v13", "v14", "v15"]:
        raise RuntimeError("V16 must preserve all existing robot tracks")
    print(json.dumps({"status": state["status"], "candidate": config["name"]}, indent=2))


if __name__ == "__main__":
    main()
