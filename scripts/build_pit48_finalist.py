from __future__ import annotations

import glob
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact, screen
from cryptoai_v13.data import load_data, point_in_time_liquid_view
from cryptoai_v13.metrics import slice_summary
from cryptoai_v13.signals import StrategySpec, build_targets
from build_walk_forward import scale_portfolio


CORE_IDS = (1461, 1434, 1264, 1217, 1443, 1705, 1593, 1540)
FAMILIES = ("xmom", "trend", "regime", "funding", "breakout", "meanrev")
TRAIN_START = "2020-01-01"
TRAIN_END = "2024-12-31 23:00"
HOLDOUT_START = "2025-01-01"
HOLDOUT_END = "2026-07-31 23:00"


def load_rows(patterns: tuple[str, ...], expected: int) -> dict[int, dict]:
    rows: dict[int, dict] = {}
    for pattern in patterns:
        for path in glob.glob(str(PROJECT / pattern)):
            for row in json.loads(Path(path).read_text())["rows"]:
                if row["index"] in rows:
                    raise ValueError(f"índice duplicado {row['index']}")
                rows[row["index"]] = row
    if len(rows) != expected:
        raise ValueError(f"esperadas {expected} regras, encontradas {len(rows)}")
    return rows


def neighborhood(spec: dict) -> tuple:
    family = spec["family"]
    if family in ("xmom", "regime"):
        return family, spec["lookback"], spec["top_n"], spec.get("slow")
    if family == "trend":
        return family, spec["fast"], spec["slow"]
    if family == "funding":
        return family, spec["lookback"], spec["top_n"]
    if family == "breakout":
        return family, spec["lookback"], spec["exit_lookback"]
    return family, spec["lookback"], spec["threshold"]


def eligible(row: dict) -> bool:
    metric = row["train_windows"]["for_2025"]
    annual = metric.get("annual_returns", {})
    return (
        not metric["ruin"]
        and metric["max_drawdown"] >= -0.65
        and set(annual) == {"2020", "2021", "2022", "2023", "2024"}
        and min(annual.values()) > 0.0
        and metric["positive_month_ratio"] >= 0.55
        and metric.get("position_decisions_per_month", 0.0) >= 3.0
    )


def ranked_family(rows: dict[int, dict], family: str) -> list[dict]:
    candidates = [row for row in rows.values()
                  if row["spec"]["family"] == family and eligible(row)]
    candidates.sort(key=lambda row: (
        min(row["train_windows"]["for_2025"]["annual_returns"].values()),
        row["train_windows"]["for_2025"]["calmar"],
        row["train_windows"]["for_2025"]["cagr"],
    ), reverse=True)
    selected, counts = [], Counter()
    for row in candidates:
        key = neighborhood(row["spec"])
        if counts[key] >= 2:
            continue
        selected.append(row)
        counts[key] += 1
        if len(selected) == 5:
            break
    return selected


def summary(result, start: str, end: str) -> dict:
    return slice_summary(result.equity, result.turnover, result.gross_exposure,
                         start, end)


def main() -> None:
    pit_rows = load_rows(("reports/pit48_coarse_*.json",
                          "reports/pit48_regime_*.json"), 1800)
    core_rows = load_rows(("reports/core2_coarse_*.json",
                           "reports/core2_regime_*.json"), 1800)
    raw = load_data(PROJECT, "research_pit48.json")
    signal_data, membership = point_in_time_liquid_view(raw, top_n=20,
                                                        lookback_hours=24 * 30)
    config = json.loads((PROJECT / "config" / "research_pit48.json").read_text())
    cost = config["costs"]["base_fee_per_side"] + config["costs"]["base_slippage_per_side"]
    severe_cost = (config["costs"]["severe_fee_per_side"]
                   + config["costs"]["severe_slippage_per_side"])

    selected_by_family = {family: ranked_family(pit_rows, family) for family in FAMILIES}
    sleeves: dict[str, pd.DataFrame] = {}
    sleeve_metrics = {}
    for family, selected in selected_by_family.items():
        if not selected:
            continue
        target = sum(build_targets(signal_data, StrategySpec(**row["spec"]))
                     for row in selected) / len(selected)
        result = screen(raw, target, cost)
        metric = summary(result, TRAIN_START, TRAIN_END)
        annual = metric["annual_returns"]
        admitted = (metric["cagr"] > 0.20 and annual.get("2023", -1) > 0
                    and annual.get("2024", -1) > 0)
        sleeve_metrics[family] = {"admitted": admitted, "metric": metric,
                                  "ids": [row["index"] for row in selected]}
        if admitted:
            sleeves[family] = target
    if not sleeves:
        raise RuntimeError("nenhum sleeve PIT passou o registro prévio")
    print("sleeves admitidos", sorted(sleeves), flush=True)

    core_data = load_data(PROJECT, "research_core2.json")
    core = sum(build_targets(core_data, StrategySpec(**core_rows[index]["spec"]))
               for index in CORE_IDS) / len(CORE_IDS)
    core = core.reindex(index=raw.close.index, columns=raw.close.columns).fillna(0.0)
    pit = sum(sleeves.values()) / len(sleeves)

    search = []
    target_cache: dict[float, pd.DataFrame] = {}
    for core_weight in (0.25, 0.50, 0.75):
        base = core * core_weight + pit * (1.0 - core_weight)
        target_cache[core_weight] = base
        for target_vol, max_gross, lookback in itertools.product(
            (0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60),
            (0.75, 1.00, 1.25, 1.50),
            (24 * 30, 24 * 60),
        ):
            targets = scale_portfolio(raw, base, target_vol, max_gross,
                                      lookback=lookback, rebalance=24, phase=0)
            result = screen(raw, targets, cost)
            metric = summary(result, TRAIN_START, TRAIN_END)
            annual = metric["annual_returns"]
            search.append({
                "params": {"core_weight": core_weight, "target_volatility": target_vol,
                           "maximum_target_gross_leverage": max_gross,
                           "volatility_lookback_hours": lookback,
                           "risk_rebalance_hours": 24, "phase_utc_hour": 0},
                "metric_2020_2024": metric,
                "eligible": metric["max_drawdown"] >= -0.35
                            and len(annual) == 5 and min(annual.values()) > 0,
            })
    eligible_search = [row for row in search if row["eligible"]]
    if not eligible_search:
        raise RuntimeError("nenhuma dose de risco respeitou o limite pré-registrado")
    selected = max(eligible_search, key=lambda row: (
        row["metric_2020_2024"]["cagr"],
        row["metric_2020_2024"]["calmar"],
    ))
    params = selected["params"]
    base = target_cache[params["core_weight"]]
    targets = scale_portfolio(
        raw, base, params["target_volatility"],
        params["maximum_target_gross_leverage"],
        lookback=params["volatility_lookback_hours"], rebalance=24, phase=0)
    screen_base = screen(raw, targets, cost)
    holdout_screen = summary(screen_base, HOLDOUT_START, HOLDOUT_END)
    print("holdout screen", json.dumps(holdout_screen), flush=True)

    exact_base = exact(raw, targets, cost)
    print("exact base concluído", flush=True)
    exact_severe = exact(raw, targets, severe_cost)
    print("exact severo concluído", flush=True)
    exact_delay = exact(raw, targets.shift(2).fillna(0.0), cost)
    print("exact atraso concluído", flush=True)
    holdout_exact = summary(exact_base, HOLDOUT_START, HOLDOUT_END)
    holdout_severe = summary(exact_severe, HOLDOUT_START, HOLDOUT_END)
    holdout_delay = summary(exact_delay, HOLDOUT_START, HOLDOUT_END)
    annual = holdout_exact["annual_returns"]
    gate = {
        "cagr_at_least_50pct": holdout_exact["cagr"] >= 0.50,
        "drawdown_no_worse_than_35pct": holdout_exact["max_drawdown"] >= -0.35,
        "2025_positive": annual.get("2025", -1.0) > 0,
        "2026_partial_positive": annual.get("2026", -1.0) > 0,
        "no_exact_ruin": not exact_base.ruin,
        "severe_cost_cagr_at_least_35pct": holdout_severe["cagr"] >= 0.35,
    }
    report = {
        "protocol": "reports/PIT48_PREREGISTRATION.md",
        "holdout_opened_once_after_selection": True,
        "universe": {"source_contracts": len(raw.symbols), "top_n_point_in_time": 20,
                     "average_members": float(membership.sum(axis=1).mean())},
        "core_ids": CORE_IDS,
        "sleeves": sleeve_metrics,
        "search_count": len(search),
        "eligible_search_count": len(eligible_search),
        "selected": selected,
        "holdout_screen": holdout_screen,
        "holdout_exact_base": holdout_exact,
        "holdout_exact_severe_cost": holdout_severe,
        "holdout_exact_delay_3h": holdout_delay,
        "ruin": {"base": exact_base.ruin, "severe": exact_severe.ruin,
                 "delay_3h": exact_delay.ruin},
        "gate": gate,
        "gate_passed": all(gate.values()),
        "selection_search": search,
    }
    (PROJECT / "reports" / "pit48_finalist_validation.json").write_text(
        json.dumps(report, indent=2) + "\n")
    targets.loc[TRAIN_START:HOLDOUT_END].to_csv(
        PROJECT / "reports" / "pit48_finalist_targets.csv", index_label="timestamp")
    exact_base.equity.loc[TRAIN_START:HOLDOUT_END].rename("equity").to_csv(
        PROJECT / "reports" / "pit48_finalist_equity.csv", index_label="timestamp")
    print(json.dumps({"gate": gate, "holdout": holdout_exact,
                      "severe": holdout_severe, "delay": holdout_delay}, indent=2))


if __name__ == "__main__":
    main()
