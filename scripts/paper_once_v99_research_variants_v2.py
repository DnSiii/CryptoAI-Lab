from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import paper_once_v99_research_variants as base

PROJECT = Path(__file__).resolve().parents[1]
MAX_OPERATIONS = 1500


def daily_backtest_curve(result) -> list[dict]:
    equity = result.equity.dropna()
    if equity.empty:
        return []
    idx = pd.DatetimeIndex(equity.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    series = pd.Series(equity.to_numpy(dtype=float), index=idx).sort_index()
    local = series.tz_convert("America/Sao_Paulo")
    daily = local.groupby(local.index.date).tail(1)
    if daily.empty:
        return []
    first = float(daily.iloc[0])
    out: list[dict] = []
    prior = 1.0
    for timestamp, value in daily.items():
        multiple = float(value) / first
        out.append(
            {
                "timestamp": timestamp.tz_convert("UTC").isoformat(),
                "equity_multiple": round(multiple, 10),
                "daily_return_pct": round((multiple / prior - 1.0) * 100.0, 8) if out else 0.0,
            }
        )
        prior = multiple
    return out


def paper_operations(targets: pd.DataFrame, paper_start: pd.Timestamp, latest: pd.Timestamp) -> list[dict]:
    eligible = targets.loc[targets.index <= latest]
    if eligible.empty:
        return []
    before = eligible.loc[eligible.index <= paper_start]
    if before.empty:
        return []
    base_ts = before.index[-1]
    window = eligible.loc[base_ts:latest]
    if len(window) < 2:
        return []

    operations: list[dict] = []
    previous = window.iloc[0].fillna(0.0)
    for timestamp, row in window.iloc[1:].iterrows():
        current = row.fillna(0.0)
        symbols = previous.index.union(current.index)
        for symbol in symbols:
            old = float(previous.get(symbol, 0.0))
            new = float(current.get(symbol, 0.0))
            if abs(new - old) < 1e-4:
                continue
            if abs(old) < 1e-8 and abs(new) >= 1e-8:
                action = "opened"
            elif abs(old) >= 1e-8 and abs(new) < 1e-8:
                action = "closed"
            elif old * new < 0:
                action = "flipped"
            elif abs(new) > abs(old):
                action = "increased"
            else:
                action = "reduced"
            operations.append(
                {
                    "timestamp": pd.Timestamp(timestamp).isoformat(),
                    "symbol": str(symbol),
                    "action": action,
                    "direction": "buy" if new > 0 else ("sell" if new < 0 else ("buy" if old > 0 else "sell")),
                    "from_weight_pct": round(old * 100.0, 5),
                    "to_weight_pct": round(new * 100.0, 5),
                    "delta_weight_pct": round((new - old) * 100.0, 5),
                }
            )
        previous = current
    return operations[-MAX_OPERATIONS:]


def main() -> None:
    data, variants, quarantined, metadata = base.build_variants()
    latest = data.close.index[-1]
    previous = base.load_state()
    initialized_at = (
        pd.Timestamp(previous["initialized_at_utc"])
        if previous
        else pd.Timestamp.now(tz="UTC")
    )
    paper_start = (
        pd.Timestamp(previous["paper_start_after_timestamp"])
        if previous
        else latest
    )
    if paper_start > latest:
        raise RuntimeError("paper boundary is newer than canonical market data")

    variant_ledgers: dict[str, dict] = {}
    backtest_reference: dict[str, dict] = {}
    for key, (targets, result) in variants.items():
        item = base.variant_ledger(key, targets, result, paper_start, latest)
        item["operations"] = paper_operations(targets, paper_start, latest)
        variant_ledgers[key] = item
        backtest_reference[key] = {
            **base.VARIANT_META[key],
            **base.REFERENCE_BACKTEST[key],
            "curve": daily_backtest_curve(result),
        }

    state_variants = {
        key: {
            "label": item["label"],
            "status": "tracking" if latest > paper_start else "initialized",
            "current_capital_brl": item["summary"]["current_capital_brl"],
            "forward_return_pct": item["summary"]["forward_return_pct"],
            "gross_exposure_pct": item["summary"]["gross_exposure_pct"],
            "open_positions": len(item["assets"]),
            "operations": len(item.get("operations", [])),
        }
        for key, item in variant_ledgers.items()
    }

    state = {
        "schema_version": 2,
        "version": base.VERSION,
        "mode": "PAPER_ONLY",
        "real_orders_enabled": False,
        "initialized_at_utc": initialized_at.isoformat(),
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "same_boundary_for_all_variants": True,
        "selection_frozen_before_paper": True,
        "variants": state_variants,
        "funding_quarantined_symbols": quarantined,
        "metadata": metadata,
        "disclosure": "Forward-only simulated paper comparison. No real orders and no paper-data retuning.",
    }
    ledger = {
        "schema_version": 2,
        "version": base.VERSION,
        "mode": "PAPER_ONLY",
        "real_orders_enabled": False,
        "base_capital_brl": base.BASE_CAPITAL_BRL,
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "same_boundary_for_all_variants": True,
        "variants": variant_ledgers,
        "backtest_reference": backtest_reference,
        "disclosure": "Backtest curves are frozen historical replays of the five preselected research versions; paper curves contain only observations after the shared boundary.",
    }
    base.write_json(base.STATE_PATH, state)
    base.write_json(base.SNAPSHOT_PATH, state)
    base.write_json(base.LEDGER_PATH, ledger)
    print(json.dumps({
        "schema_version": 2,
        "paper_start": paper_start.isoformat(),
        "latest": latest.isoformat(),
        "variants": {
            key: {
                "backtest_days": len(backtest_reference[key]["curve"]),
                "paper_hours": len(variant_ledgers[key]["equity_curve"]),
                "operations": len(variant_ledgers[key]["operations"]),
            }
            for key in variants
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
