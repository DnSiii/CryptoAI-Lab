from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact, screen
from cryptoai_v13.data import load_data, validate_data
from cryptoai_v13.metrics import slice_summary
from build_walk_forward import load_rows
from run_candidate_v13_multihorizon import build_candidate


def metric(result):
    return slice_summary(result.equity, result.turnover, result.gross_exposure,
                         "2021-01-01", "2026-07-31 23:00")


if __name__ == "__main__":
    config = json.loads((PROJECT / "config" / "candidate_v13_multihorizon.json").read_text())
    rows = {row["index"]: row for row in load_rows()}
    data = load_data(PROJECT, "research_expanded.json")
    validation = validate_data(data)
    if validation["errors"]:
        raise RuntimeError(validation["errors"])
    targets = build_candidate(data, rows, config)
    fast = screen(data, targets, config["execution"]["base_cost_per_side"])
    screen_metric = metric(fast)
    print("screen", screen_metric["cagr"], screen_metric["max_drawdown"], flush=True)
    rigorous = exact(data, targets, config["execution"]["base_cost_per_side"])
    report = {
        "universe": list(data.symbols),
        "survivorship_stress": "adds six contracts present by early 2020, including EOS which later ceased trading",
        "screen": screen_metric,
        "exact": metric(rigorous),
        "ruin": rigorous.ruin,
    }
    output = PROJECT / "reports" / "candidate_v13_multihorizon_expanded_universe.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
