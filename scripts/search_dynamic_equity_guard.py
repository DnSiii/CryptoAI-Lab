from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary
from run_canonical_risk_stress import cap_targets


START = "2021-01-01"
END = "2026-07-31 23:00"
SEED = 1300260815
REPORT_PATH = PROJECT / "reports" / "dynamic_equity_guard_search.json"


def metric(result) -> dict:
    return slice_summary(
        result.equity, result.turnover, result.gross_exposure, START, END
    )


def dynamic_guard_bootstrap(
    equity: pd.Series,
    threshold: float,
    multiplier: float,
    recovery: float,
    paths: int = 8_000,
) -> dict:
    daily = (
        equity.loc[START:END]
        .resample("D")
        .last()
        .pct_change(fill_method=None)
        .dropna()
        .to_numpy()
    )
    block_days = 7
    horizon_days = 365 * 5
    blocks_needed = int(np.ceil(horizon_days / block_days))
    starts = np.arange(0, len(daily) - block_days + 1)
    offsets = np.arange(block_days)
    rng = np.random.default_rng(SEED)
    ruined = np.zeros(paths, dtype=bool)
    below_start = np.zeros(paths, dtype=bool)
    worst_dd = np.empty(paths)
    switch_cost = 0.0010
    batch_size = 250
    for begin in range(0, paths, batch_size):
        size = min(batch_size, paths - begin)
        chosen = rng.choice(starts, size=(size, blocks_needed), replace=True)
        sampled = np.concatenate(
            [daily[chosen[:, j, None] + offsets] for j in range(blocks_needed)],
            axis=1,
        )[:, :horizon_days]
        values = np.ones(size)
        peaks = np.ones(size)
        active = np.zeros(size, dtype=bool)
        minimum_dd = np.zeros(size)
        minimum_equity = np.ones(size)
        for day in range(horizon_days):
            drawdown = values / peaks - 1.0
            next_active = active.copy()
            next_active[active & (drawdown >= -abs(recovery))] = False
            next_active[(~active) & (drawdown <= -abs(threshold))] = True
            changed = next_active != active
            factor = np.where(next_active, multiplier, 1.0)
            net_return = factor * sampled[:, day] - changed * switch_cost
            values *= np.maximum(1.0 + net_return, 0.0)
            peaks = np.maximum(peaks, values)
            drawdown = values / peaks - 1.0
            minimum_dd = np.minimum(minimum_dd, drawdown)
            minimum_equity = np.minimum(minimum_equity, values)
            active = next_active
        ruined[begin : begin + size] = (
            (minimum_equity <= 0.10) | (minimum_dd <= -0.60)
        )
        below_start[begin : begin + size] = values < 1.0
        worst_dd[begin : begin + size] = minimum_dd
    return {
        "seed": SEED,
        "paths": paths,
        "block_days": block_days,
        "horizon_years": 5,
        "switch_cost": switch_cost,
        "estimated_ruin_probability": float(ruined.mean()),
        "probability_terminal_below_start": float(below_start.mean()),
        "drawdown_percentiles": {
            str(p): float(np.percentile(worst_dd, p))
            for p in (1, 5, 25, 50, 75, 95, 99)
        },
    }


def checkpoint(report: dict) -> None:
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")


def main() -> None:
    config = json.loads(
        (PROJECT / "config" / "candidate_v13_pit_carry_core.json").read_text()
    )
    data = load_data(PROJECT, config["data_config"])
    raw_targets = pd.read_csv(
        PROJECT / "reports" / "candidate_v13_pit_carry_core_targets.csv",
        index_col=0,
        parse_dates=True,
    )
    raw_targets.index = pd.to_datetime(raw_targets.index, utc=True)
    raw_targets = raw_targets.reindex(
        index=data.close.index, columns=data.close.columns
    ).fillna(0.0)
    targets = cap_targets(raw_targets, 1.35)
    execution = config["execution"]
    unguarded = exact_fast(
        data,
        targets,
        execution["base_cost_per_side"],
        execution["maintenance_equity_fraction"],
        gross_guard_cap=1.5,
    )
    report = {
        "status": "in_progress",
        "candidate": config["name"],
        "method": (
            "Stateful portfolio-equity guard inside exact execution. Bootstrap "
            "reapplies the same guard to every synthetic path and charges 10 bps "
            "whenever the guard switches state."
        ),
        "unguarded_metric": metric(unguarded),
        "rows": [],
    }
    checkpoint(report)
    for threshold, multiplier in itertools.product(
        (0.10, 0.15, 0.20), (0.25, 0.50)
    ):
        recovery = threshold / 2.0
        print(
            f"starting threshold={threshold:.2f} multiplier={multiplier:.2f}",
            flush=True,
        )
        result = exact_fast(
            data,
            targets,
            execution["base_cost_per_side"],
            execution["maintenance_equity_fraction"],
            gross_guard_cap=1.5,
            drawdown_guard_threshold=threshold,
            drawdown_guard_multiplier=multiplier,
            drawdown_guard_recovery=recovery,
        )
        summary = metric(result)
        risk = dynamic_guard_bootstrap(
            unguarded.equity, threshold, multiplier, recovery
        )
        row = {
            "threshold": threshold,
            "multiplier": multiplier,
            "recovery": recovery,
            "exact_metric": summary,
            "dynamic_bootstrap": risk,
            "passes": {
                "cagr_at_least_50pct": summary["cagr"] >= 0.50,
                "historical_drawdown_no_worse_than_35pct": (
                    summary["max_drawdown"] >= -0.35
                ),
                "synthetic_ruin_below_1pct": (
                    risk["estimated_ruin_probability"] < 0.01
                ),
                "no_exact_ruin": not result.ruin,
            },
        }
        row["passes_all"] = all(row["passes"].values())
        report["rows"].append(row)
        checkpoint(report)
        print(
            f"completed threshold={threshold:.2f} multiplier={multiplier:.2f}: "
            f"CAGR={summary['cagr']:.4f} DD={summary['max_drawdown']:.4f} "
            f"ruin={risk['estimated_ruin_probability']:.4f}",
            flush=True,
        )
    viable = [row for row in report["rows"] if row["passes_all"]]
    report["selected"] = (
        max(viable, key=lambda row: row["exact_metric"]["cagr"])
        if viable
        else None
    )
    report["status"] = "completed"
    checkpoint(report)
    print(json.dumps({"selected": report["selected"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
