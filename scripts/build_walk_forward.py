from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from cryptoai_v13.backtest import exact, screen
from cryptoai_v13.data import load_data
from cryptoai_v13.metrics import slice_summary, summarize
from cryptoai_v13.signals import StrategySpec, build_targets


FOLDS = {
    "2023": {"train": "for_2023", "start": "2023-01-01", "end": "2023-12-31 23:00"},
    "2024": {"train": "for_2024", "start": "2024-01-01", "end": "2024-12-31 23:00"},
    "2025": {"train": "for_2025", "start": "2025-01-01", "end": "2025-12-31 23:00"},
    "2026": {"train": "for_2026", "start": "2026-01-01", "end": "2026-07-31 23:00"},
}


def load_rows() -> list[dict]:
    files = sorted((PROJECT / "reports").glob("coarse_*.json")) + sorted(
        (PROJECT / "reports").glob("regime_*.json"))
    if not files:
        raise FileNotFoundError("nenhum lote coarse encontrado")
    rows = []
    seen = set()
    for path in files:
        payload = json.loads(path.read_text())
        for row in payload["rows"]:
            if row["index"] in seen:
                raise ValueError(f"índice duplicado {row['index']}")
            seen.add(row["index"])
            rows.append(row)
    total = max(seen) + 1 if seen else 0
    if not total or seen != set(range(total)):
        missing = sorted(set(range(total)) - seen)
        raise ValueError(f"lotes incompletos: {missing[:20]}")
    return sorted(rows, key=lambda row: row["index"])


def select_sleeves(rows: list[dict], train_key: str) -> list[dict]:
    chosen = []
    for family in ("xmom", "trend", "regime", "funding", "breakout", "meanrev"):
        eligible = []
        for row in rows:
            if row["spec"]["family"] != family:
                continue
            metric = row["train_windows"][train_key]
            if metric["ruin"] or metric["cagr"] <= 0.05 or metric["max_drawdown"] < -0.55:
                continue
            if metric.get("position_decisions_per_month", 0.0) < 3.0:
                continue
            annual = list(metric.get("annual_returns", {}).values())
            worst_year = min(annual) if annual else -1.0
            eligible.append((row, metric, worst_year))
        if not eligible:
            continue
        objectives = [
            max(eligible, key=lambda item: item[1]["cagr"]),
            max(eligible, key=lambda item: item[1]["calmar"]),
            max(eligible, key=lambda item: (item[2], item[1]["cagr"])),
        ]
        for row, metric, worst_year in objectives:
            if row["index"] not in {item["index"] for item in chosen}:
                chosen.append({"index": row["index"], "spec": row["spec"],
                               "training_metric": metric, "training_worst_year": worst_year})
    return chosen


def scale_portfolio(data, targets: pd.DataFrame, target_vol: float, max_gross: float,
                    lookback: int = 24 * 30, rebalance: int = 24, phase: int = 0) -> pd.DataFrame:
    returns = data.close.pct_change(fill_method=None).fillna(0.0)
    base_return = (targets.shift(1).fillna(0.0) * returns).sum(axis=1)
    realized = base_return.rolling(lookback, min_periods=24 * 10).std() * np.sqrt(365.25 * 24)
    multiplier = target_vol / realized.shift(1).replace(0.0, np.nan)
    multiplier = multiplier.clip(lower=0.0, upper=4.0).fillna(0.0)
    gross = targets.abs().sum(axis=1)
    gross_limit = max_gross / gross.replace(0.0, np.nan)
    multiplier = pd.concat([multiplier, gross_limit], axis=1).min(axis=1).clip(lower=0.0).fillna(0.0)
    event = pd.Series((np.arange(len(multiplier)) - phase) % rebalance == 0, index=multiplier.index)
    multiplier = multiplier.where(event, np.nan).ffill().fillna(0.0)
    scaled = targets.mul(multiplier, axis=0)
    final_gross = scaled.abs().sum(axis=1)
    hard_cap = (max_gross / final_gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    return scaled.mul(hard_cap, axis=0)


def choose_overlay(data, base: pd.DataFrame, train_start: str, train_end: str,
                   cost: float) -> tuple[pd.DataFrame, dict]:
    choices = []
    for target_vol in (0.6, 0.8, 1.0, 1.2, 1.5):
        for max_gross in (1.5, 2.0, 2.5, 3.0, 4.0):
            targets = scale_portfolio(data, base, target_vol, max_gross)
            result = screen(data, targets, cost)
            metric = slice_summary(result.equity, result.turnover, result.gross_exposure,
                                   train_start, train_end)
            choices.append((targets, {"target_vol": target_vol, "max_gross": max_gross,
                                      "training_metric": metric}))
    under_limit = [item for item in choices if item[1]["training_metric"]["max_drawdown"] >= -0.35
                   and not item[1]["training_metric"]["ruin"]]
    pool = under_limit or [item for item in choices if not item[1]["training_metric"]["ruin"]]
    selected = max(pool, key=lambda item: (item[1]["training_metric"]["cagr"],
                                           item[1]["training_metric"]["calmar"]))
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exact", action="store_true")
    args = parser.parse_args()
    rows = load_rows()
    data = load_data(PROJECT)
    config = json.loads((PROJECT / "config" / "research.json").read_text())
    cost = config["costs"]["base_fee_per_side"] + config["costs"]["base_slippage_per_side"]
    severe_cost = config["costs"]["severe_fee_per_side"] + config["costs"]["severe_slippage_per_side"]
    stitched = pd.DataFrame(0.0, index=data.close.index, columns=data.close.columns)
    fold_report = {}
    target_cache: dict[int, pd.DataFrame] = {}
    for year, fold in FOLDS.items():
        selected = select_sleeves(rows, fold["train"])
        if not selected:
            raise RuntimeError(f"nenhum sleeve para {year}")
        matrices = []
        for item in selected:
            index = item["index"]
            if index not in target_cache:
                target_cache[index] = build_targets(data, StrategySpec(**item["spec"]))
            matrices.append(target_cache[index])
        base = sum(matrices) / len(matrices)
        train_start = "2020-01-01"
        train_end = f"{int(year) - 1}-12-31 23:00"
        scaled, overlay = choose_overlay(data, base, train_start, train_end, cost)
        mask = (stitched.index >= pd.Timestamp(fold["start"], tz="UTC")) & (
            stitched.index <= pd.Timestamp(fold["end"], tz="UTC"))
        stitched.loc[mask] = scaled.loc[mask]
        fold_report[year] = {"selected_sleeves": selected, "overlay": overlay}

    base_result = exact(data, stitched, cost) if args.exact else screen(data, stitched, cost)
    severe_result = exact(data, stitched, severe_cost) if args.exact else screen(data, stitched, severe_cost)
    start, end = "2023-01-01", "2026-07-31 23:00"
    base_metric = slice_summary(base_result.equity, base_result.turnover,
                                base_result.gross_exposure, start, end)
    severe_metric = slice_summary(severe_result.equity, severe_result.turnover,
                                  severe_result.gross_exposure, start, end)
    tests = {
        year: slice_summary(base_result.equity, base_result.turnover,
                            base_result.gross_exposure, fold["start"], fold["end"])
        for year, fold in FOLDS.items()
    }
    positions_path = PROJECT / "reports" / "walk_forward_positions.csv"
    stitched.loc[start:end].to_csv(positions_path, index_label="timestamp")
    report = {
        "selection_rule": "past-only expanding walk-forward; three objectives per family; overlay chosen only on prior data",
        "candidate_count": len(rows),
        "replay": "exact" if args.exact else "screen",
        "cost_per_side": cost,
        "severe_cost_per_side": severe_cost,
        "folds": fold_report,
        "oos_combined": base_metric,
        "oos_severe_cost": severe_metric,
        "oos_blocks": tests,
        "ruin": base_result.ruin,
    }
    output = PROJECT / "reports" / ("walk_forward_exact.json" if args.exact else "walk_forward_screen.json")
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(output), "oos": base_metric, "severe": severe_metric}, indent=2))


if __name__ == "__main__":
    main()
