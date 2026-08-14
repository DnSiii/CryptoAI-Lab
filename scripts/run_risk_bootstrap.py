from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
SEED = 1300260812


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--equity", default="reports/candidate_v13_multihorizon_equity.csv")
    parser.add_argument("--output", default="reports/candidate_v13_multihorizon_risk_bootstrap.json")
    args = parser.parse_args()
    equity = pd.read_csv(PROJECT / args.equity)
    equity.index = pd.to_datetime(equity.pop("timestamp"), utc=True)
    daily = equity["equity"].resample("D").last().pct_change(fill_method=None).dropna().to_numpy()
    rng = np.random.default_rng(SEED)
    paths = 50_000
    horizon_days = 365 * 3
    block = 7
    blocks_needed = int(np.ceil(horizon_days / block))
    starts = np.arange(0, len(daily) - block + 1)
    terminal = np.empty(paths)
    max_drawdown = np.empty(paths)
    ruin = np.zeros(paths, dtype=bool)
    batch_size = 500
    for begin in range(0, paths, batch_size):
        size = min(batch_size, paths - begin)
        chosen = rng.choice(starts, size=(size, blocks_needed), replace=True)
        sampled = np.concatenate([daily[chosen[:, j, None] + np.arange(block)]
                                  for j in range(blocks_needed)], axis=1)[:, :horizon_days]
        values = np.cumprod(1.0 + sampled, axis=1)
        peaks = np.maximum.accumulate(values, axis=1)
        drawdowns = values / peaks - 1.0
        terminal[begin:begin + size] = values[:, -1]
        max_drawdown[begin:begin + size] = drawdowns.min(axis=1)
        ruin[begin:begin + size] = (values.min(axis=1) <= 0.10) | (drawdowns.min(axis=1) <= -0.60)
    report = {
        "seed": SEED,
        "paths": paths,
        "horizon_years": 3,
        "block_days": block,
        "ruin_definition": "equity <= 10% of start or drawdown <= -60%",
        "estimated_ruin_probability": float(ruin.mean()),
        "terminal_multiple_percentiles": {str(p): float(np.percentile(terminal, p))
                                           for p in (1, 5, 25, 50, 75, 95, 99)},
        "max_drawdown_percentiles": {str(p): float(np.percentile(max_drawdown, p))
                                     for p in (1, 5, 25, 50, 75, 95, 99)},
        "probability_terminal_below_start": float((terminal < 1.0).mean()),
    }
    output = PROJECT / args.output
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
