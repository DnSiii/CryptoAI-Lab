from __future__ import annotations

import glob
import itertools
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.allocator import convex_equity_overlay
from cryptoai_v13.backtest import screen
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary
from cryptoai_v13.signals import StrategySpec, build_targets
from build_walk_forward import scale_portfolio


CORE_IDS = (1461, 1434, 1264, 1217, 1443, 1705, 1593, 1540)


def load_core_rows() -> dict[int, dict]:
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
    rows = load_core_rows()
    base = sum(build_targets(data, StrategySpec(**rows[index]["spec"]))
               for index in CORE_IDS) / len(CORE_IDS)
    cost = 0.0007
    proxy = screen(data, base, cost).equity
    factors = []
    for (short_days, long_days), dd_days, threshold, winner, loser, dd_mult in itertools.product(
        ((14, 60), (30, 90), (60, 180)),
        (60, 180), (0.08, 0.12, 0.16), (1.15, 1.30), (0.25, 0.50), (0.25, 0.50),
    ):
        params = {
            "short_hours": short_days * 24, "long_hours": long_days * 24,
            "drawdown_hours": dd_days * 24, "drawdown_threshold": threshold,
            "winner_multiplier": winner, "loser_multiplier": loser,
            "drawdown_multiplier": dd_mult,
        }
        factors.append(params)

    rows_out = []
    target_cache = {}
    total = len(factors) * 16
    for target_vol, max_gross in itertools.product(
        (0.40, 0.50, 0.60, 0.70), (1.00, 1.25, 1.50, 1.75),
    ):
        scaled = scale_portfolio(data, base, target_vol, max_gross,
                                 lookback=24 * 60, rebalance=24)
        for factor_params in factors:
            targets = convex_equity_overlay(
                scaled, proxy, **factor_params, rebalance_hours=24,
                maximum_gross=max_gross)
            result = screen(data, targets, cost)
            training = metric(result, "2020-01-01", "2024-12-31 23:00")
            annual = training["annual_returns"]
            params = {"target_volatility": target_vol,
                      "maximum_target_gross_leverage": max_gross,
                      "volatility_lookback_hours": 24 * 60,
                      **factor_params}
            rows_out.append({
                "params": params,
                "metric_2020_2024": training,
                "eligible": training["max_drawdown"] >= -0.35
                            and len(annual) == 5 and min(annual.values()) > 0,
            })
            if len(rows_out) % 250 == 0:
                print(f"{len(rows_out)}/{total}", flush=True)
    eligible = [row for row in rows_out if row["eligible"]]
    if not eligible:
        raise RuntimeError("nenhum overlay convexo elegível")
    selected = max(eligible, key=lambda row: (
        row["metric_2020_2024"]["cagr"], row["metric_2020_2024"]["calmar"]))
    p = selected["params"]
    scaled = scale_portfolio(data, base, p["target_volatility"],
                             p["maximum_target_gross_leverage"],
                             lookback=p["volatility_lookback_hours"], rebalance=24)
    keys = ("short_hours", "long_hours", "drawdown_hours", "drawdown_threshold",
            "winner_multiplier", "loser_multiplier", "drawdown_multiplier")
    targets = convex_equity_overlay(
        scaled, proxy, **{key: p[key] for key in keys}, rebalance_hours=24,
        maximum_gross=p["maximum_target_gross_leverage"])
    holdout_result = screen(data, targets, cost)
    holdout = metric(holdout_result, "2025-01-01", "2026-07-31 23:00")
    output = {
        "research_status": "post-PIT48-holdout research; not a new pristine holdout",
        "core_ids": CORE_IDS,
        "configuration_count": len(rows_out),
        "eligible_count": len(eligible),
        "selected": selected,
        "holdout_screen": holdout,
        "rows": rows_out,
    }
    (PROJECT / "reports" / "core_convex_search.json").write_text(
        json.dumps(output, indent=2) + "\n")
    targets.to_csv(PROJECT / "reports" / "core_convex_targets.csv",
                   index_label="timestamp")
    print(json.dumps({"selected": selected, "holdout": holdout}, indent=2))


if __name__ == "__main__":
    main()
