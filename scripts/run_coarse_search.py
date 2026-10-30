from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from cryptoai_v13.backtest import screen
from cryptoai_v13.data import load_data, validate_data
from cryptoai_v13.metrics import slice_summary, summarize
from cryptoai_v13.signals import StrategySpec, build_targets


SEED = 1300260812
BLOCKS = {
    "development": ("2020-01-01", "2022-12-31 23:00"),
    "validation_2023": ("2023-01-01", "2023-12-31 23:00"),
    "validation_2024": ("2024-01-01", "2024-12-31 23:00"),
    "recent_2025": ("2025-01-01", "2025-12-31 23:00"),
    "recent_2026": ("2026-01-01", "2026-07-31 23:00"),
}
TRAIN_WINDOWS = {
    "for_2023": ("2020-01-01", "2022-12-31 23:00"),
    "for_2024": ("2020-01-01", "2023-12-31 23:00"),
    "for_2025": ("2020-01-01", "2024-12-31 23:00"),
    "for_2026": ("2020-01-01", "2025-12-31 23:00"),
}


def sample_unique(factory, count: int, rng: random.Random) -> list[StrategySpec]:
    values = {}
    attempts = 0
    while len(values) < count:
        spec = factory(rng)
        values[json.dumps(spec.to_dict(), sort_keys=True)] = spec
        attempts += 1
        if attempts > count * 100:
            raise RuntimeError("espaço de parâmetros menor que a amostra solicitada")
    return list(values.values())


def make_specs(counts: dict[str, int]) -> list[StrategySpec]:
    rng = random.Random(SEED)

    def xmom(r: random.Random) -> StrategySpec:
        return StrategySpec(
            family="xmom", lookback=r.choice([24, 48, 72, 168, 336, 720, 1440]),
            rebalance=r.choice([6, 12, 24, 48, 72, 168]), top_n=r.choice([1, 2, 3]),
            vol_lookback=r.choice([72, 168, 336, 720]), vol_target=r.choice([0.5, 0.8, 1.1, 1.4, 1.8]),
            leverage_cap=r.choice([1.0, 1.5, 2.0, 2.5, 3.0]), trend_lookback=r.choice([72, 168, 336, 720]),
            long_short_balance=r.choice([0.35, 0.5, 0.65, 0.8]), threshold=r.choice([0.0, 0.01, 0.03, 0.05]))

    def trend(r: random.Random) -> StrategySpec:
        fast, slow = r.choice([(6, 48), (12, 72), (24, 96), (24, 168), (48, 168),
                               (72, 336), (168, 720), (336, 1440)])
        return StrategySpec(
            family="trend", lookback=slow, fast=fast, slow=slow,
            rebalance=r.choice([3, 6, 12, 24, 48]), vol_lookback=r.choice([48, 72, 168, 336, 720]),
            vol_target=r.choice([0.5, 0.8, 1.1, 1.4, 1.8]), leverage_cap=r.choice([1.0, 1.5, 2.0, 2.5, 3.0]),
            threshold=r.choice([0.0, 0.003, 0.01, 0.02, 0.04]))

    def funding(r: random.Random) -> StrategySpec:
        return StrategySpec(
            family="funding", lookback=r.choice([8, 24, 72, 168, 336]),
            rebalance=r.choice([8, 12, 24, 48, 72]), top_n=r.choice([1, 2, 3]),
            vol_lookback=r.choice([72, 168, 336, 720]), vol_target=r.choice([0.4, 0.7, 1.0, 1.3]),
            leverage_cap=r.choice([1.0, 1.5, 2.0, 2.5]), trend_lookback=r.choice([72, 168, 336]),
            long_short_balance=r.choice([0.35, 0.5, 0.65]), threshold=r.choice([0.0, 0.00002, 0.00005, 0.0001]))

    def breakout_factory(r: random.Random) -> StrategySpec:
        lookback = r.choice([24, 48, 72, 168, 336, 720])
        return StrategySpec(
            family="breakout", lookback=lookback, exit_lookback=r.choice([12, 24, 48, 72]),
            rebalance=r.choice([3, 6, 12, 24]), vol_lookback=r.choice([72, 168, 336]),
            vol_target=r.choice([0.5, 0.8, 1.1, 1.4]), leverage_cap=r.choice([1.0, 1.5, 2.0, 2.5]))

    def meanrev(r: random.Random) -> StrategySpec:
        return StrategySpec(
            family="meanrev", lookback=r.choice([24, 48, 72, 120, 168]),
            rebalance=r.choice([1, 3, 6, 12]), vol_lookback=r.choice([48, 72, 168, 336]),
            vol_target=r.choice([0.3, 0.5, 0.8, 1.1]), leverage_cap=r.choice([0.75, 1.0, 1.5, 2.0]),
            trend_lookback=r.choice([24, 48, 72, 168]), threshold=r.choice([1.0, 1.25, 1.5, 1.75, 2.0, 2.5]))

    factories = {"xmom": xmom, "trend": trend, "funding": funding,
                 "breakout": breakout_factory, "meanrev": meanrev}
    specs = []
    for family, count in counts.items():
        specs.extend(sample_unique(factories[family], count, rng))
    rng.shuffle(specs)
    return specs


def metric_block(result, start: str, end: str) -> dict:
    return slice_summary(result.equity, result.turnover, result.gross_exposure, start, end)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int)
    parser.add_argument("--data-config", default="research.json")
    parser.add_argument("--prefix", default="coarse")
    args = parser.parse_args()
    base = {"xmom": 360, "trend": 360, "funding": 180, "breakout": 120, "meanrev": 180}
    counts = {key: max(1, round(value * args.scale)) for key, value in base.items()}
    specs = make_specs(counts)
    end = args.end_index if args.end_index is not None else len(specs)
    selected = list(enumerate(specs))[args.start_index:end]
    data = load_data(PROJECT, args.data_config)
    validation = validate_data(data)
    if validation["errors"]:
        raise RuntimeError(validation["errors"])
    config = json.loads((PROJECT / "config" / "research.json").read_text())
    cost = config["costs"]["base_fee_per_side"] + config["costs"]["base_slippage_per_side"]
    rows = []
    output = PROJECT / "reports" / f"{args.prefix}_{args.start_index:04d}_{end:04d}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    for done, (index, spec) in enumerate(selected, 1):
        targets = build_targets(data, spec)
        result = screen(data, targets, cost_per_side=cost)
        payload = {
            "index": index,
            "spec": spec.to_dict(),
            "combined": summarize(result.equity, result.turnover, result.gross_exposure, result.ruin),
            "blocks": {name: metric_block(result, *period) for name, period in BLOCKS.items()},
            "train_windows": {name: metric_block(result, *period) for name, period in TRAIN_WINDOWS.items()},
        }
        rows.append(payload)
        if done % 25 == 0 or done == len(selected):
            artifact = {
                "seed": SEED,
                "candidate_count_total": len(specs),
                "range": [args.start_index, end],
                "cost_per_side": cost,
                "screen_only_not_final": True,
                "data_config": args.data_config,
                "rows": rows,
            }
            output.write_text(json.dumps(artifact, indent=2) + "\n")
            print(f"{done}/{len(selected)} -> {output.name}", flush=True)


if __name__ == "__main__":
    main()
