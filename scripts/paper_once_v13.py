from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.backtest import exact_fast
from run_final_candidate import build_candidate


STATE_PATH = PROJECT / "state" / "paper_v13_state.json"
SNAPSHOT_PATH = PROJECT / "reports" / "paper_v13_snapshot.json"
LEDGER_PATH = PROJECT / "reports" / "paper_v13_ledger.json"
PAPER_CAPITAL_BRL = 10_000.0


def cap_targets(targets: pd.DataFrame, cap: float) -> pd.DataFrame:
    gross = targets.abs().sum(axis=1)
    scale = (cap / gross.replace(0.0, np.nan)).clip(upper=1.0).fillna(0.0)
    return targets.mul(scale, axis=0)


def load_state() -> dict | None:
    if not STATE_PATH.exists():
        return None
    return json.loads(STATE_PATH.read_text())


def resolve_paper_start(
    previous: dict | None, initialized_at: pd.Timestamp, latest: pd.Timestamp
) -> pd.Timestamp:
    initialization_hour = initialized_at.floor("h")
    if previous:
        # Once frozen, the forward boundary must never chase newly downloaded
        # data. Backfills before this hour stay excluded, while genuine new
        # hours after it are allowed into the paper ledger.
        return max(
            pd.Timestamp(previous["paper_start_after_timestamp"]),
            initialization_hour,
        )
    return max(latest, initialization_hour)


def checkpoint(payload: dict, ledger: dict) -> None:
    STATE_PATH.parent.mkdir(exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    SNAPSHOT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2) + "\n")


def action_label(previous: float, current: float) -> tuple[str, str]:
    epsilon = 1e-8
    if abs(current) <= epsilon:
        return (
            ("Fechou compra", "close_long")
            if previous > 0
            else ("Fechou venda", "close_short")
        )
    if abs(previous) <= epsilon:
        return (
            ("Abriu compra", "open_long")
            if current > 0
            else ("Abriu venda", "open_short")
        )
    if previous * current < 0:
        return (
            ("Virou para compra", "flip_long")
            if current > 0
            else ("Virou para venda", "flip_short")
        )
    growing = abs(current) > abs(previous)
    if current > 0:
        return ("Aumentou compra", "increase_long") if growing else ("Reduziu compra", "reduce_long")
    return ("Aumentou venda", "increase_short") if growing else ("Reduziu venda", "reduce_short")


def build_ledger(
    data,
    targets: pd.DataFrame,
    result,
    paper_start: pd.Timestamp,
    candidate: str,
) -> dict:
    index = data.close.index
    base_equity = float(result.equity.loc[paper_start])
    forward_index = index[index >= paper_start]
    forward_after_start = index[index > paper_start]
    event_index = index[
        (index > paper_start) & (result.turnover.reindex(index).fillna(0.0) > 1e-12)
    ]
    latest = forward_index[-1]

    if any(
        value is None
        for value in (
            result.open_positions,
            result.asset_gross,
            result.asset_fees,
            result.asset_funding,
        )
    ):
        raise RuntimeError("motor paper sem atribuição por ativo")

    def to_brl(value: float) -> float:
        return PAPER_CAPITAL_BRL * float(value) / base_equity

    def result_breakdown(timestamp: pd.Timestamp, symbol: str | None = None) -> dict:
        if symbol is None:
            gross_value = float(result.asset_gross.loc[timestamp].sum())
            fee_value = float(result.asset_fees.loc[timestamp].sum())
            funding_cost_value = float(result.asset_funding.loc[timestamp].sum())
        else:
            gross_value = float(result.asset_gross.loc[timestamp, symbol])
            fee_value = float(result.asset_fees.loc[timestamp, symbol])
            funding_cost_value = float(result.asset_funding.loc[timestamp, symbol])
        gross_brl = to_brl(gross_value)
        fees_brl = to_brl(fee_value)
        funding_result_brl = -to_brl(funding_cost_value)
        total_cost_brl = fees_brl - funding_result_brl
        net_brl = gross_brl - fees_brl + funding_result_brl
        return {
            "gross_result_brl": round(gross_brl, 2),
            "fees_brl": round(fees_brl, 2),
            "funding_result_brl": round(funding_result_brl, 2),
            "total_cost_brl": round(total_cost_brl, 2),
            "net_result_brl": round(net_brl, 2),
        }

    equity_curve = []
    for timestamp in forward_index:
        multiple = float(result.equity.loc[timestamp]) / base_equity
        breakdown = (
            result_breakdown(timestamp)
            if timestamp > paper_start
            else {
                "gross_result_brl": 0.0,
                "fees_brl": 0.0,
                "funding_result_brl": 0.0,
                "total_cost_brl": 0.0,
                "net_result_brl": 0.0,
            }
        )
        equity_curve.append(
            {
                "timestamp": timestamp.isoformat(),
                "equity_multiple": round(multiple, 10),
                "capital_brl": round(PAPER_CAPITAL_BRL * multiple, 2),
                "hour_result_brl": breakdown["net_result_brl"],
                **breakdown,
            }
        )

    candles: dict[str, list[dict]] = {}
    candle_index = forward_index[-240:]
    for symbol in ("BTCUSDT", "ETHUSDT"):
        if symbol not in data.close.columns:
            continue
        candles[symbol] = [
            {
                "timestamp": timestamp.isoformat(),
                "open": round(float(data.frames["open"].loc[timestamp, symbol]), 8),
                "high": round(float(data.frames["high"].loc[timestamp, symbol]), 8),
                "low": round(float(data.frames["low"].loc[timestamp, symbol]), 8),
                "close": round(float(data.close.loc[timestamp, symbol]), 8),
            }
            for timestamp in candle_index
            if pd.notna(data.frames["open"].loc[timestamp, symbol])
        ]

    decisions = []
    for timestamp in event_index:
        position = index.get_loc(timestamp)
        previous_target = targets.iloc[max(0, position - 2)]
        requested_target = targets.iloc[position - 1]
        changed = (requested_target - previous_target).abs() > 1e-8
        symbols = list(targets.columns[changed])
        if not symbols:
            symbols = list(targets.columns[(result.positions.iloc[position] - result.positions.iloc[position - 1]).abs() > 1e-8])
        rows = []
        for symbol in symbols:
            before = float(previous_target[symbol])
            after = float(requested_target[symbol])
            label, code = action_label(before, after)
            breakdown = result_breakdown(timestamp, symbol)
            rows.append(
                {
                    "symbol": symbol,
                    "action": label,
                    "action_code": code,
                    "previous_weight": round(before, 8),
                    "new_weight": round(after, 8),
                    "execution_price": round(
                        float(data.frames["open"].loc[timestamp, symbol]), 8
                    ),
                    **breakdown,
                }
            )
        previous_timestamp = index[position - 1]
        capital_before = PAPER_CAPITAL_BRL * float(result.equity.loc[previous_timestamp]) / base_equity
        capital_after = PAPER_CAPITAL_BRL * float(result.equity.loc[timestamp]) / base_equity
        decision_breakdown = result_breakdown(timestamp)
        decisions.append(
            {
                "timestamp": timestamp.isoformat(),
                "status": "open_or_rebalanced",
                "reason": "O robô mudou o tamanho das posições na abertura desta hora.",
                "capital_before_brl": round(capital_before, 2),
                "capital_after_hour_brl": round(capital_after, 2),
                **decision_breakdown,
                "adjustments": rows,
            }
        )

    asset_summaries = {}
    for symbol in ("BTCUSDT", "ETHUSDT"):
        if symbol not in data.close.columns:
            continue
        gross_brl = to_brl(float(result.asset_gross.loc[forward_after_start, symbol].sum()))
        fees_brl = to_brl(float(result.asset_fees.loc[forward_after_start, symbol].sum()))
        funding_result_brl = -to_brl(
            float(result.asset_funding.loc[forward_after_start, symbol].sum())
        )
        total_cost_brl = fees_brl - funding_result_brl
        net_brl = gross_brl - fees_brl + funding_result_brl
        current_weight = float(result.positions.loc[latest, symbol])
        current_capital = PAPER_CAPITAL_BRL * float(result.equity.loc[latest]) / base_equity
        first_open = forward_index[
            result.open_positions.loc[forward_index, symbol].abs() > 1e-8
        ]
        inherited = abs(float(result.positions.loc[paper_start, symbol])) > 1e-8
        asset_summaries[symbol] = {
            "status": "open" if abs(current_weight) > 1e-8 else "closed",
            "direction": (
                "buy" if current_weight > 0 else "sell" if current_weight < 0 else "none"
            ),
            "current_weight": round(current_weight, 8),
            "position_value_brl": round(abs(current_weight) * current_capital, 2),
            "current_price": round(float(data.close.loc[latest, symbol]), 8),
            "tracked_since": (
                first_open[0].isoformat() if len(first_open) else paper_start.isoformat()
            ),
            "inherited_at_paper_start": inherited,
            "gross_result_brl": round(gross_brl, 2),
            "fees_brl": round(fees_brl, 2),
            "funding_result_brl": round(funding_result_brl, 2),
            "total_cost_brl": round(total_cost_brl, 2),
            "net_result_brl": round(net_brl, 2),
        }

    total_gross_brl = sum(item["gross_result_brl"] for item in asset_summaries.values())
    total_fees_brl = sum(item["fees_brl"] for item in asset_summaries.values())
    total_funding_result_brl = sum(
        item["funding_result_brl"] for item in asset_summaries.values()
    )
    total_cost_brl = total_fees_brl - total_funding_result_brl
    latest_multiple = float(result.equity.loc[latest]) / base_equity
    exact_net_brl = PAPER_CAPITAL_BRL * (latest_multiple - 1.0)
    attributed_net_brl = total_gross_brl - total_fees_brl + total_funding_result_brl
    if abs(exact_net_brl - attributed_net_brl) > 0.05:
        raise RuntimeError(
            f"atribuição não reconcilia: {attributed_net_brl:.6f} != {exact_net_brl:.6f}"
        )
    hourly_results = [point["net_result_brl"] for point in equity_curve[1:]]
    capital_values = [point["capital_brl"] for point in equity_curve]
    return {
        "schema_version": 2,
        "mode": "PAPER_ONLY",
        "candidate": candidate,
        "base_capital_brl": PAPER_CAPITAL_BRL,
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "summary": {
            "decision_events": len(decisions),
            "position_adjustments": sum(len(item["adjustments"]) for item in decisions),
            "positioned_hours": int((result.gross_exposure.loc[forward_after_start] > 1e-8).sum()),
            "positive_hours": sum(value > 0 for value in hourly_results),
            "negative_hours": sum(value < 0 for value in hourly_results),
            "gross_result_brl": round(total_gross_brl, 2),
            "fees_brl": round(total_fees_brl, 2),
            "funding_result_brl": round(total_funding_result_brl, 2),
            "total_cost_brl": round(total_cost_brl, 2),
            "net_result_brl": round(exact_net_brl, 2),
            "current_capital_brl": round(PAPER_CAPITAL_BRL * latest_multiple, 2),
            "highest_capital_brl": round(max(capital_values), 2),
            "lowest_capital_brl": round(min(capital_values), 2),
        },
        "assets": asset_summaries,
        "opening_snapshot": {
            "timestamp": paper_start.isoformat(),
            "positions": {
                symbol: round(float(weight), 8)
                for symbol, weight in result.positions.loc[paper_start].items()
                if abs(float(weight)) > 1e-8
            },
            "explanation": "Posições já existentes no corte inicial; não contam como novas compras do paper.",
        },
        "equity_curve": equity_curve,
        "candles": candles,
        "decisions": decisions,
        "explanation": {
            "gross": "Resultado dos movimentos de preço antes de taxas e funding.",
            "cost": "Taxas mais funding pago, descontando funding recebido.",
            "net": "O que sobrou: bruto menos custos.",
            "open_positions": "Aberta significa que o robô ainda mantém exposição. O resultado pode mudar a cada nova vela.",
        },
    }


def main() -> None:
    finalist = json.loads(
        (PROJECT / "config" / "candidate_v13_circuit_breaker.json").read_text()
    )
    base_config = json.loads(
        (PROJECT / "config" / finalist["base_candidate_config"]).read_text()
    )
    data, targets, _, _ = build_candidate(base_config)
    targets = cap_targets(targets, finalist["target_cap"])
    execution = base_config["execution"]
    guard = finalist["circuit_breaker"]
    result = exact_fast(
        data,
        targets,
        execution["base_cost_per_side"],
        execution["maintenance_equity_fraction"],
        gross_guard_cap=finalist["gross_guard_cap"],
        drawdown_guard_threshold=guard["drawdown_threshold"],
        drawdown_guard_multiplier=guard["exposure_multiplier"],
        drawdown_guard_cooldown_hours=guard["cooldown_hours"],
    )
    latest = data.close.index[-1]
    previous = load_state()
    initialized_at = (
        pd.Timestamp(previous["initialized_at_utc"])
        if previous
        else pd.Timestamp.now(tz="UTC")
    )
    paper_start = resolve_paper_start(previous, initialized_at, latest)
    forward_equity = result.equity.loc[paper_start:]
    if len(forward_equity):
        forward_equity = forward_equity / forward_equity.iloc[0]
    new_hours = int((data.close.index > paper_start).sum())
    nonzero_positions = {
        symbol: round(float(weight), 8)
        for symbol, weight in result.positions.iloc[-1].items()
        if abs(float(weight)) > 1e-8
    }
    next_target = {
        symbol: round(float(weight), 8)
        for symbol, weight in targets.iloc[-1].items()
        if abs(float(weight)) > 1e-8
    }
    payload = {
        "mode": "PAPER_ONLY",
        "real_orders_enabled": False,
        "candidate": finalist["name"],
        "initialized_at_utc": initialized_at.isoformat(),
        "paper_start_after_timestamp": paper_start.isoformat(),
        "latest_data_timestamp": latest.isoformat(),
        "new_forward_hours": new_hours,
        "status": "tracking" if new_hours > 0 else "waiting_for_new_data",
        "forward_equity_multiple": (
            round(float(forward_equity.iloc[-1]), 10)
            if len(forward_equity)
            else 1.0
        ),
        "current_simulated_positions": nonzero_positions,
        "target_for_next_open": next_target,
        "gross_exposure": round(float(result.gross_exposure.iloc[-1]), 8),
        "disclosure": (
            "No exchange order method exists in this runner. The paper ledger "
            "only counts timestamps strictly newer than the model-freeze hour; "
            "later backfills from before that hour are excluded."
        ),
    }
    ledger = build_ledger(data, targets, result, paper_start, finalist["name"])
    checkpoint(payload, ledger)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
