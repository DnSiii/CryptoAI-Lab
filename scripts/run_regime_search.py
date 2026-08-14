from __future__ import annotations

import json
import random
import sys
import argparse
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import screen
from cryptoai_v13.data import load_data, validate_data
from cryptoai_v13.metrics import slice_summary, summarize
from cryptoai_v13.signals import StrategySpec, build_targets
from run_coarse_search import BLOCKS, TRAIN_WINDOWS, SEED, sample_unique


def factory(r: random.Random) -> StrategySpec:
    return StrategySpec(
        family="regime", lookback=r.choice([24, 48, 72, 168, 336, 720, 1440]),
        rebalance=r.choice([3, 6, 12, 24, 48, 72]), top_n=r.choice([1, 2, 3]),
        slow=r.choice([72, 168, 336, 720, 1440]),
        vol_lookback=r.choice([72, 168, 336, 720]), vol_target=r.choice([0.5, 0.8, 1.1, 1.4, 1.8]),
        leverage_cap=r.choice([1.0, 1.5, 2.0, 2.5, 3.0]), trend_lookback=r.choice([72, 168, 336, 720]),
        long_short_balance=r.choice([0.65, 0.8, 0.9, 1.0]), threshold=r.choice([0.0, 0.01, 0.03, 0.05, 0.08]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=600)
    parser.add_argument("--data-config", default="research.json")
    parser.add_argument("--prefix", default="regime")
    args = parser.parse_args()
    rng = random.Random(SEED + 17)
    specs = sample_unique(factory, 600, rng)
    data = load_data(PROJECT, args.data_config)
    validation = validate_data(data)
    if validation["errors"]:
        raise RuntimeError(validation["errors"])
    config = json.loads((PROJECT / "config" / "research.json").read_text())
    cost = config["costs"]["base_fee_per_side"] + config["costs"]["base_slippage_per_side"]
    rows = []
    selected = specs[args.start:args.end]
    output = PROJECT / "reports" / f"{args.prefix}_{1200 + args.start:04d}_{1200 + args.end:04d}.json"
    for done, spec in enumerate(selected, 1):
        result = screen(data, build_targets(data, spec), cost)
        rows.append({
            "index": 1200 + args.start + done - 1,
            "spec": spec.to_dict(),
            "combined": summarize(result.equity, result.turnover, result.gross_exposure, result.ruin),
            "blocks": {name: slice_summary(result.equity, result.turnover, result.gross_exposure, *period)
                       for name, period in BLOCKS.items()},
            "train_windows": {name: slice_summary(result.equity, result.turnover, result.gross_exposure, *period)
                              for name, period in TRAIN_WINDOWS.items()},
        })
        if done % 25 == 0 or done == len(selected):
            output.write_text(json.dumps({"seed": SEED + 17, "candidate_count_total": 1800,
                                          "range": [1200 + args.start, 1200 + args.end], "cost_per_side": cost,
                                          "data_config": args.data_config,
                                          "screen_only_not_final": True, "rows": rows}, indent=2) + "\n")
            print(f"{done}/{len(selected)}", flush=True)
