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

from cryptoai_v13.allocator import convex_equity_overlay
from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary
from run_canonical_risk_stress import cap_targets


START = "2021-01-01"
END = "2026-07-31 23:00"
REPORT_PATH = PROJECT / "reports" / "causal_drawdown_guard_search.json"
SEED = 1300260814


def metric(result) -> dict:
    return slice_summary(
        result.equity, result.turnover, result.gross_exposure, START, END
    )


def bootstrap_single(equity: pd.Series, paths: int = 4_000) -> dict:
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
    terminal_below_start = np.zeros(paths, dtype=bool)
    batch_size = 250
    for begin in range(0, paths, batch_size):
        size = min(batch_size, paths - begin)
        chosen = rng.choice(starts, size=(size, blocks_needed), replace=True)
        sampled = np.concatenate(
            [daily[chosen[:, j, None] + offsets] for j in range(blocks_needed)],
            axis=1,
        )[:, :horizon_days]
        values = np.cumprod(1.0 + sampled, axis=1)
        peaks = np.maximum.accumulate(values, axis=1)
        drawdowns = values / peaks - 1.0
        ruined[begin : begin + size] = (
            (values.min(axis=1) <= 0.10)
            | (drawdowns.min(axis=1) <= -0.60)
        )
        terminal_below_start[begin : begin + size] = values[:, -1] < 1.0
    return {
        "paths": paths,
        "block_days": block_days,
        "horizon_years": 5,
        "estimated_ruin_probability": float(ruined.mean()),
        "probability_terminal_below_start": float(terminal_below_start.mean()),
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
    proxy = exact_fast(
        data,
        targets,
        execution["base_cost_per_side"],
        execution["maintenance_equity_fraction"],
        gross_guard_cap=1.5,
    ).equity

    report = {
        "status": "in_progress",
        "candidate": config["name"],
        "method": (
            "Causal de-risking only: no winner pyramiding. The uncontrolled "
            "candidate equity observed through close t controls targets that can "
            "execute no earlier than the next open."
        ),
        "rows": [],
    }
    checkpoint(report)
    combinations = list(
        itertools.product((0.08, 0.12, 0.16), (0.25, 0.50, 0.75))
    )
    for threshold, multiplier in combinations:
        guarded = convex_equity_overlay(
            targets,
            proxy,
            short_hours=24 * 30,
            long_hours=24 * 90,
            drawdown_hours=24 * 180,
            drawdown_threshold=threshold,
            winner_multiplier=1.0,
            loser_multiplier=1.0,
            drawdown_multiplier=multiplier,
            rebalance_hours=24,
            maximum_gross=1.35,
        )
        result = screen(data, guarded, execution["base_cost_per_side"])
        summary = metric(result)
        risk = bootstrap_single(result.equity)
        row = {
            "drawdown_threshold": threshold,
            "drawdown_multiplier": multiplier,
            "screen_metric": summary,
            "bootstrap_screen": risk,
            "passes_screen": (
                summary["cagr"] >= 0.50
                and summary["max_drawdown"] >= -0.35
                and risk["estimated_ruin_probability"] < 0.01
            ),
        }
        report["rows"].append(row)
        checkpoint(report)
        print(
            f"threshold={threshold:.2f} multiplier={multiplier:.2f} "
            f"CAGR={summary['cagr']:.4f} DD={summary['max_drawdown']:.4f} "
            f"ruin={risk['estimated_ruin_probability']:.4f}",
            flush=True,
        )

    report["status"] = "completed"
    viable = [row for row in report["rows"] if row["passes_screen"]]
    report["finalists"] = sorted(
        viable, key=lambda row: row["screen_metric"]["cagr"], reverse=True
    )[:3]
    checkpoint(report)
    print(json.dumps({"finalists": report["finalists"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
