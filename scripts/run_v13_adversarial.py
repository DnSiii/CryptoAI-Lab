from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path

import pandas as pd

from cryptoai.binance_data import discover_archives
from cryptoai.gates import PromotionGates
from cryptoai.metrics import block_bootstrap_ruin_probability
from cryptoai.replay import CandidateSpec, load_universe, phase_sweep, run_replay


def select_universe(max_symbols: int) -> tuple[list[str], list[dict[str, object]]]:
    archives = discover_archives()
    eligible = [a for a in archives if a.first_month and a.first_month <= "2024-01" and a.monthly_files >= 12]
    delisted = [a for a in eligible if a.delisted]
    live = [a for a in eligible if not a.delisted]
    n_delisted = min(max(4, max_symbols // 4), len(delisted))
    chosen = delisted[:n_delisted] + live[: max_symbols - n_delisted]
    by_symbol = {a.symbol: a for a in eligible}
    for required in ("BTCUSDT", "ETHUSDT"):
        if required in by_symbol and required not in {x.symbol for x in chosen}:
            if chosen:
                chosen[-1] = by_symbol[required]
            else:
                chosen.append(by_symbol[required])
    chosen = sorted({x.symbol: x for x in chosen}.values(), key=lambda x: x.symbol)
    metadata = [
        {
            "symbol": a.symbol,
            "first_month": a.first_month,
            "last_month": a.last_month,
            "monthly_files": a.monthly_files,
            "delisted": a.delisted,
        }
        for a in chosen
    ]
    return [a.symbol for a in chosen], metadata


def complete_archive_end(requested_end: str, universe_meta: list[dict[str, object]]) -> str:
    """Do not silently zero-fill a partial funding month.

    Funding-rate archives are monthly in the reproducible public archive path used by this lab.
    The replay therefore stops at the last month available for both BTC and ETH core contracts.
    """
    core_last = {
        str(row["symbol"]): str(row["last_month"])
        for row in universe_meta
        if row.get("symbol") in {"BTCUSDT", "ETHUSDT"} and row.get("last_month")
    }
    if set(core_last) != {"BTCUSDT", "ETHUSDT"}:
        raise RuntimeError(f"Could not determine complete funding archive cutoff for BTC/ETH: {core_last}")
    latest_common_month = min(core_last.values())
    archive_end = pd.Period(latest_common_month, freq="M").end_time.normalize()
    requested = pd.Timestamp(requested_end)
    return str(min(requested, archive_end).date())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2020-01-01")
    p.add_argument("--end", default="2026-08-10")
    p.add_argument("--max-symbols", type=int, default=16)
    p.add_argument("--cache-dir", default=".cache/cryptoai")
    p.add_argument("--report", default="reports/v13_adversarial.json")
    p.add_argument("--bootstrap-samples", type=int, default=3000)
    p.add_argument("--skip-phases", action="store_true")
    args = p.parse_args()

    symbols, universe_meta = select_universe(args.max_symbols)
    if not {"BTCUSDT", "ETHUSDT"}.issubset(symbols):
        raise RuntimeError(f"BTC/ETH not both discovered in Binance Vision universe: {symbols}")

    effective_end = complete_archive_end(args.end, universe_meta)
    data = load_universe(symbols, args.start, effective_end, Path(args.cache_dir))
    spec = CandidateSpec()

    base = run_replay(data, spec)
    severe = run_replay(data, spec, cost_multiplier=spec.severe_cost_multiplier)
    delayed = run_replay(data, replace(spec, execution_delay_hours=3))
    funding_adverse = run_replay(data, spec, funding_adverse=True)
    phases = {} if args.skip_phases else phase_sweep(data, spec)
    bootstrap_ruin = block_bootstrap_ruin_probability(
        base["returns"], samples=args.bootstrap_samples, block_hours=24 * 7, ruin_equity=0.20
    )

    phase_min = min(phases.values()) if phases else float("nan")
    gate_metrics = {
        "base_cagr": base["performance"]["cagr"],
        "max_drawdown": base["performance"]["max_drawdown"],
        "severe_cost_cagr": severe["performance"]["cagr"],
        "delay_3h_cagr": delayed["performance"]["cagr"],
        "decisions_per_month": base["decisions_per_month"],
        "bootstrap_ruin_probability": bootstrap_ruin,
        "phase_min_cagr": phase_min,
        "liquidated": base["liquidated"] or severe["liquidated"] or delayed["liquidated"] or funding_adverse["liquidated"],
    }
    gates = PromotionGates().report(gate_metrics)

    report = {
        "status": "RECONSTRUCTION_UNVERIFIED" if not gates["passed"] else "CANDIDATE_PASSES_RECONSTRUCTED_GATES",
        "warning": "The exact formula source of the pre-repository candidate was not recoverable; this replay is a causal reconstruction and must not be represented as reproducing the legacy 56.1% result unless metrics independently match.",
        "mode": "RESEARCH_ONLY_PAPER_ONLY",
        "period": {"requested_start": args.start, "requested_end": args.end, "effective_end": effective_end},
        "spec": asdict(spec),
        "universe": universe_meta,
        "base": {k: v for k, v in base.items() if k not in {"returns", "weights", "sleeves"}},
        "severe_costs": {k: v for k, v in severe.items() if k not in {"returns", "weights", "sleeves"}},
        "delay_3h": {k: v for k, v in delayed.items() if k not in {"returns", "weights", "sleeves"}},
        "funding_adverse": {k: v for k, v in funding_adverse.items() if k not in {"returns", "weights", "sleeves"}},
        "phase_cagr": phases,
        "bootstrap_ruin_probability": bootstrap_ruin,
        "promotion": gates,
    }
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "symbols": symbols,
        "effective_end": effective_end,
        "base_cagr": gate_metrics["base_cagr"],
        "max_drawdown": gate_metrics["max_drawdown"],
        "severe_cost_cagr": gate_metrics["severe_cost_cagr"],
        "delay_3h_cagr": gate_metrics["delay_3h_cagr"],
        "phase_min_cagr": phase_min,
        "bootstrap_ruin_probability": bootstrap_ruin,
        "passed": gates["passed"],
        "report": str(path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
