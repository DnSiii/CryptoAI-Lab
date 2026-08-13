from __future__ import annotations

import glob
import itertools
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.allocator import trailing_stop_overlay
from cryptoai_v13.backtest import screen
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary
from cryptoai_v13.signals import StrategySpec, build_targets
from build_walk_forward import scale_portfolio


ENSEMBLES = {
    "broad8": (1461, 1434, 1264, 1217, 1443, 1705, 1593, 1540),
    "top5_development": (1461, 1434, 1264, 1217, 1443),
    "stable5_development": (1434, 1443, 1705, 1593, 1323),
    "conservative5_development": (1434, 1443, 1323, 1422, 1718),
}


def load_rows() -> dict[int, dict]:
    rows = {}
    for pattern in ("reports/core2_coarse_*.json", "reports/core2_regime_*.json"):
        for path in glob.glob(str(PROJECT / pattern)):
            for row in json.loads(Path(path).read_text())["rows"]:
                rows[row["index"]] = row
    if len(rows) != 1800:
        raise ValueError(len(rows))
    return rows


def metric(result, start: str, end: str) -> dict:
    return slice_summary(result.equity, result.turnover, result.gross_exposure,
                         start, end)


def main() -> None:
    data = load_data(PROJECT, "research_core2.json")
    rows = load_rows()
    bases = {
        name: sum(build_targets(data, StrategySpec(**rows[index]["spec"]))
                  for index in ids) / len(ids)
        for name, ids in ENSEMBLES.items()
    }
    stopped = {}
    for name, base in bases.items():
        for stop, cooldown in itertools.product(
                (0.04, 0.06, 0.08, 0.12, 0.16, 0.20, 0.24),
                (6, 24, 72, 168, 336)):
            stopped[name, stop, cooldown] = trailing_stop_overlay(
                base, data.close, stop, cooldown)
    print(f"{len(stopped)} overlays de posição", flush=True)

    rows_out = []
    for (name, stop, cooldown), base in stopped.items():
        for target_vol, max_gross in itertools.product(
                (0.30, 0.40, 0.50, 0.60, 0.70, 0.80),
                (1.00, 1.25, 1.50, 1.75, 2.00)):
            targets = scale_portfolio(data, base, target_vol, max_gross,
                                      lookback=24 * 60, rebalance=24)
            result = screen(data, targets, 0.0007)
            training = metric(result, "2020-01-01", "2024-12-31 23:00")
            annual = training["annual_returns"]
            rows_out.append({
                "params": {"ensemble": name, "ids": ENSEMBLES[name],
                           "stop_fraction": stop, "cooldown_hours": cooldown,
                           "target_volatility": target_vol,
                           "maximum_target_gross_leverage": max_gross,
                           "volatility_lookback_hours": 24 * 60},
                "metric_2020_2024": training,
                "eligible": training["max_drawdown"] >= -0.35
                            and len(annual) == 5 and min(annual.values()) > 0,
            })
            if len(rows_out) % 500 == 0:
                print(f"{len(rows_out)}/{len(stopped) * 30}", flush=True)
    eligible = [row for row in rows_out if row["eligible"]]
    if not eligible:
        raise RuntimeError("nenhum trailing stop elegível")
    selected = max(eligible, key=lambda row: (
        row["metric_2020_2024"]["cagr"], row["metric_2020_2024"]["calmar"]))
    p = selected["params"]
    base = stopped[p["ensemble"], p["stop_fraction"], p["cooldown_hours"]]
    targets = scale_portfolio(data, base, p["target_volatility"],
                              p["maximum_target_gross_leverage"],
                              lookback=p["volatility_lookback_hours"], rebalance=24)
    base_result = screen(data, targets, 0.0007)
    severe_result = screen(data, targets, 0.0012)
    holdout = metric(base_result, "2025-01-01", "2026-07-31 23:00")
    severe = metric(severe_result, "2025-01-01", "2026-07-31 23:00")
    report = {
        "research_status": "post-holdout research; requires new forward paper data",
        "configuration_count": len(rows_out), "eligible_count": len(eligible),
        "selected": selected, "holdout_screen": holdout,
        "holdout_severe_screen": severe, "rows": rows_out,
    }
    (PROJECT / "reports" / "core_trailing_search.json").write_text(
        json.dumps(report, indent=2) + "\n")
    targets.to_csv(PROJECT / "reports" / "core_trailing_targets.csv",
                   index_label="timestamp")
    print(json.dumps({"selected": selected, "holdout": holdout,
                      "severe": severe}, indent=2))


if __name__ == "__main__":
    main()
