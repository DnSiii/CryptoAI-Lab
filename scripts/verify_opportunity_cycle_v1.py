from __future__ import annotations

import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((PROJECT / path).read_text())


def main() -> None:
    state = load("state/paper_opportunity_v1_state.json")
    comparison = load("reports/paper_comparison_v1.json")
    snapshots = {
        "core": load("reports/paper_core_comparison_v1_snapshot.json"),
        "opportunity": load("reports/paper_opportunity_v1_snapshot.json"),
        "combined": load("reports/paper_combined_v1_snapshot.json"),
    }
    ledgers = {
        "core": load("reports/paper_core_comparison_v1_ledger.json"),
        "opportunity": load("reports/paper_opportunity_v1_ledger.json"),
        "combined": load("reports/paper_combined_v1_ledger.json"),
    }
    if state.get("mode") != "PAPER_ONLY" or state.get("real_orders_enabled"):
        raise RuntimeError("comparison state left PAPER_ONLY mode")
    if comparison.get("mode") != "PAPER_ONLY" or comparison.get("real_orders_enabled"):
        raise RuntimeError("comparison report left PAPER_ONLY mode")
    boundary = state["paper_start_after_timestamp"]
    latest = state["latest_data_timestamp"]
    if comparison["paper_start_after_timestamp"] != boundary:
        raise RuntimeError("comparison and state boundaries differ")
    for track in ("core", "opportunity", "combined"):
        snapshot = snapshots[track]
        ledger = ledgers[track]
        if snapshot.get("real_orders_enabled") or snapshot.get("mode") != "PAPER_ONLY":
            raise RuntimeError(f"{track} snapshot is not PAPER_ONLY")
        if ledger.get("mode") != "PAPER_ONLY" or ledger.get("schema_version") != 4:
            raise RuntimeError(f"{track} ledger is invalid")
        if snapshot.get("track") != track or ledger.get("track") != track:
            raise RuntimeError(f"{track} identity mismatch")
        if snapshot["paper_start_after_timestamp"] != boundary:
            raise RuntimeError(f"{track} snapshot boundary mismatch")
        if ledger["paper_start_after_timestamp"] != boundary:
            raise RuntimeError(f"{track} ledger boundary mismatch")
        if snapshot["latest_data_timestamp"] != latest:
            raise RuntimeError(f"{track} latest timestamp mismatch")
        summary = ledger["summary"]
        if abs(
            float(summary["current_capital_brl"])
            - (10_000.0 + float(summary["net_result_brl"]))
        ) > 0.05:
            raise RuntimeError(f"{track} capital does not reconcile")
        asset_net = sum(
            float(asset["net_result_brl"])
            for asset in ledger.get("assets", {}).values()
        )
        if abs(asset_net - float(summary["net_result_brl"])) > 0.05:
            raise RuntimeError(f"{track} asset attribution does not reconcile")
        if snapshot["status"] == "waiting_for_boundary":
            if ledger["equity_curve"] or ledger["decisions"]:
                raise RuntimeError(f"{track} counted results before its boundary")
        elif ledger.get("status") not in {"tracking", "waiting_for_new_data"}:
            raise RuntimeError(f"{track} tracking status is invalid")
    if set(comparison.get("tracks", {})) != {"core", "opportunity", "combined"}:
        raise RuntimeError("comparison report does not contain all three tracks")
    print(json.dumps({
        "status": state["status"],
        "paper_start_after_timestamp": boundary,
        "latest_data_timestamp": latest,
        "tracks": list(ledgers),
    }, indent=2))


if __name__ == "__main__":
    main()
