from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import screen
from cryptoai_v13.data import load_data, point_in_time_liquid_view, validate_data
from cryptoai_v13.metrics import slice_summary, summarize
from cryptoai_v13.signals import build_targets
from run_coarse_search import BLOCKS, TRAIN_WINDOWS, SEED, make_specs, sample_unique
from run_regime_search import factory as regime_factory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("coarse", "regime"), required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--liquidity-lookback", type=int, default=24 * 30)
    args = parser.parse_args()

    if args.kind == "coarse":
        specs = make_specs({"xmom": 360, "trend": 360, "funding": 180,
                            "breakout": 120, "meanrev": 180})
        offset = 0
    else:
        specs = sample_unique(regime_factory, 600, random.Random(SEED + 17))
        offset = 1200
    if not (0 <= args.start < args.end <= len(specs)):
        raise ValueError("intervalo inválido")

    raw = load_data(PROJECT, "research_pit48.json")
    validation = validate_data(raw)
    if validation["errors"]:
        raise RuntimeError(validation["errors"])
    signal_data, membership = point_in_time_liquid_view(
        raw, top_n=args.top_n, lookback_hours=args.liquidity_lookback,
        minimum_history_hours=24 * 30)
    config = json.loads((PROJECT / "config" / "research_pit48.json").read_text())
    cost = config["costs"]["base_fee_per_side"] + config["costs"]["base_slippage_per_side"]
    rows = []
    first, last = offset + args.start, offset + args.end
    output = PROJECT / "reports" / f"pit48_{args.kind}_{first:04d}_{last:04d}.json"
    for done, local_index in enumerate(range(args.start, args.end), 1):
        spec = specs[local_index]
        targets = build_targets(signal_data, spec)
        result = screen(raw, targets, cost)
        rows.append({
            "index": offset + local_index,
            "spec": spec.to_dict(),
            "combined": summarize(result.equity, result.turnover,
                                  result.gross_exposure, result.ruin),
            "blocks": {
                name: slice_summary(result.equity, result.turnover,
                                    result.gross_exposure, *period)
                for name, period in BLOCKS.items()
            },
            "train_windows": {
                name: slice_summary(result.equity, result.turnover,
                                    result.gross_exposure, *period)
                for name, period in TRAIN_WINDOWS.items()
            },
        })
        if done % 25 == 0 or done == args.end - args.start:
            output.write_text(json.dumps({
                "seed": SEED if args.kind == "coarse" else SEED + 17,
                "candidate_count_total": 1800,
                "range": [first, last],
                "data_config": "research_pit48.json",
                "point_in_time_universe": {
                    "top_n": args.top_n,
                    "lookback_hours": args.liquidity_lookback,
                    "uses_volume_through": "t-1",
                    "average_members": float(membership.sum(axis=1).mean()),
                },
                "cost_per_side": cost,
                "screen_only_not_final": True,
                "rows": rows,
            }, indent=2) + "\n")
            print(f"{done}/{args.end - args.start}", flush=True)


if __name__ == "__main__":
    main()
