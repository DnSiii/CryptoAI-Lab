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
from cryptoai_v13.data import FuturesData
from run_final_candidate import build_candidate


STATE_PATH = PROJECT / "state" / "paper_v13_state.json"
SNAPSHOT_PATH = PROJECT / "reports" / "paper_v13_snapshot.json"
LEDGER_PATH = PROJECT / "reports" / "paper_v13_ledger.json"
PAPER_CAPITAL_BRL = 10_000.0
SYNC_REPORT_PATH = PROJECT / "reports" / "paper_data_sync_v13.json"


def quarantine_stale_funding(
    data: FuturesData,
    targets: pd.DataFrame,
    stale_symbols: list[str],
    last_funding: dict[str, pd.Timestamp],
    maximum_lag_hours: int,
) -> tuple[FuturesData, pd.DataFrame]:
    """Make a contract untradable once its verified funding feed goes stale."""
    frames = {name: frame.copy() for name, frame in data.frames.items()}
    funding = data.funding.copy()
    safe_targets = targets.copy()
    for symbol in stale_symbols:
        if symbol not in safe_targets.columns or symbol not in last_funding:
            continue
        cutoff = pd.Timestamp(last_funding[symbol]) + pd.Timedelta(
            hours=maximum_lag_hours
        )
        unavailable = safe_targets.index > cutoff
        safe_targets.loc[unavailable, symbol] = 0.0
        funding.loc[unavailable, symbol] = 0.0
        for frame in frames.values():
            frame.loc[unavailable, symbol] = np.nan
    return FuturesData(frames=frames, funding=funding, symbols=data.symbols), safe_targets


def apply_funding_quarantine(
    data: FuturesData, targets: pd.DataFrame
) -> tuple[FuturesData, pd.DataFrame, list[str]]:
    if not SYNC_REPORT_PATH.exists():
        return data, targets, []
    report = json.loads(SYNC_REPORT_PATH.read_text())
    stale_symbols = list(report.get("funding_stale", []))
    last_funding: dict[str, pd.Timestamp] = {}
    for symbol in stale_symbols:
        path = PROJECT / "data" / "canonical" / f"{symbol}_funding.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path, usecols=["timestamp"])
        if len(frame):
            last_funding[symbol] = pd.to_datetime(
                frame["timestamp"], utc=True, format="mixed"
            ).max()
    data, targets = quarantine_stale_funding(
        data,
        targets,
        stale_symbols,
        last_funding,
        int(report.get("maximum_funding_lag_hours", 12)),
    )
    return data, targets, sorted(last_funding)


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
    latest = forward_index[-1]

    if any(
        value is None
        for value in (
            result.open_positions,
            result.asset_gross,
            result.asset_fees,
            result.asset_funding,
            result.asset_orders,
            result.asset_order_notional,
        )
    ):
        raise RuntimeError("motor paper sem atribuição por ativo")

    event_index = index[
        (index > paper_start)
        & (result.asset_orders.reindex(index).abs().sum(axis=1) > 1e-12)
    ]

    # The strategy can rotate beyond BTC/ETH.  The ledger must follow every
    # asset that was actually held or traded during the forward interval;
    # otherwise a new position can disappear from the dashboard and its P&L
    # gets incorrectly folded into the last hard-coded asset.
    paper_symbols = [
        symbol
        for symbol in data.close.columns
        if (
            result.open_positions.loc[forward_index, symbol].abs().gt(1e-8).any()
            or result.asset_orders.loc[forward_after_start, symbol].abs().gt(1e-12).any()
            or result.asset_gross.loc[forward_after_start, symbol].abs().gt(1e-12).any()
            or result.asset_fees.loc[forward_after_start, symbol].abs().gt(1e-12).any()
            or result.asset_funding.loc[forward_after_start, symbol].abs().gt(1e-12).any()
        )
    ]

    def to_brl(value: float) -> float:
        return PAPER_CAPITAL_BRL * float(value) / base_equity

    def rounded_breakdown(
        gross_brl: float, fees_brl: float, funding_result_brl: float
    ) -> dict:
        """Round for display while keeping bruto - custos = líquido to the cent."""
        exact_net_brl = round(gross_brl - fees_brl + funding_result_brl, 2)
        rounded_fees = round(fees_brl, 2)
        rounded_funding = round(funding_result_brl, 2)
        rounded_cost = round(rounded_fees - rounded_funding, 2)
        rounded_gross = round(gross_brl, 2)
        rounded_gross = round(
            rounded_gross + exact_net_brl - (rounded_gross - rounded_cost), 2
        )
        return {
            "gross_result_brl": rounded_gross,
            "fees_brl": rounded_fees,
            "funding_result_brl": rounded_funding,
            "total_cost_brl": rounded_cost,
            "net_result_brl": exact_net_brl,
        }

    def reconcile_rows(rows: list[dict], total: dict) -> None:
        """Put cent-rounding residue in the last row so visible rows add to total."""
        if not rows:
            return
        last = rows[-1]
        for key in ("gross_result_brl", "fees_brl", "funding_result_brl"):
            residue = round(total[key] - sum(float(row[key]) for row in rows), 2)
            last[key] = round(float(last[key]) + residue, 2)
        for row in rows:
            row["total_cost_brl"] = round(
                float(row["fees_brl"]) - float(row["funding_result_brl"]), 2
            )
            row["net_result_brl"] = round(
                float(row["gross_result_brl"]) - float(row["total_cost_brl"]), 2
            )

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
        return rounded_breakdown(gross_brl, fees_brl, funding_result_brl)

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
    for symbol in paper_symbols:
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
        orders = result.asset_orders.loc[timestamp]
        symbols = list(orders.index[orders.abs() > 1e-12])
        rows = []
        for symbol in symbols:
            order_weight = float(result.asset_orders.loc[timestamp, symbol])
            after = float(result.open_positions.loc[timestamp, symbol])
            before = after - order_weight
            label, code = action_label(before, after)
            breakdown = result_breakdown(timestamp, symbol)
            rows.append(
                {
                    "symbol": symbol,
                    "action": label,
                    "action_code": code,
                    "order_side": "buy" if order_weight > 0.0 else "sell",
                    "order_value_brl": round(
                        to_brl(
                            abs(
                                float(
                                    result.asset_order_notional.loc[
                                        timestamp, symbol
                                    ]
                                )
                            )
                        ),
                        2,
                    ),
                    "previous_weight": round(before, 8),
                    "new_weight": round(after, 8),
                    "execution_price": round(
                        float(data.frames["open"].loc[timestamp, symbol]), 8
                    ),
                    "result_scope": "whole_asset_hour_not_order_profit",
                    **breakdown,
                }
            )
        previous_timestamp = index[position - 1]
        capital_before = PAPER_CAPITAL_BRL * float(result.equity.loc[previous_timestamp]) / base_equity
        capital_after = PAPER_CAPITAL_BRL * float(result.equity.loc[timestamp]) / base_equity
        decision_breakdown = result_breakdown(timestamp)
        reconcile_rows(rows, decision_breakdown)
        decisions.append(
            {
                "timestamp": timestamp.isoformat(),
                "status": "open_or_rebalanced",
                "reason": "O robô mudou o tamanho das posições na abertura desta hora.",
                "result_scope": "whole_hour_not_trade_profit",
                "capital_before_brl": round(capital_before, 2),
                "capital_after_hour_brl": round(capital_after, 2),
                **decision_breakdown,
                "adjustments": rows,
            }
        )

    asset_summaries = {}
    for symbol in paper_symbols:
        if symbol not in data.close.columns:
            continue
        gross_brl = to_brl(float(result.asset_gross.loc[forward_after_start, symbol].sum()))
        fees_brl = to_brl(float(result.asset_fees.loc[forward_after_start, symbol].sum()))
        funding_result_brl = -to_brl(
            float(result.asset_funding.loc[forward_after_start, symbol].sum())
        )
        breakdown = rounded_breakdown(gross_brl, fees_brl, funding_result_brl)
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
            **breakdown,
        }

    total_breakdown = rounded_breakdown(
        to_brl(float(result.asset_gross.loc[forward_after_start].sum().sum())),
        to_brl(float(result.asset_fees.loc[forward_after_start].sum().sum())),
        -to_brl(float(result.asset_funding.loc[forward_after_start].sum().sum())),
    )
    reconcile_rows(list(asset_summaries.values()), total_breakdown)
    latest_multiple = float(result.equity.loc[latest]) / base_equity
    exact_net_brl = PAPER_CAPITAL_BRL * (latest_multiple - 1.0)
    attributed_net_brl = sum(
        item["net_result_brl"] for item in asset_summaries.values()
    )
    if abs(exact_net_brl - attributed_net_brl) > 0.05:
        raise RuntimeError(
            f"atribuição não reconcilia: {attributed_net_brl:.6f} != {exact_net_brl:.6f}"
        )
    hourly_results = [point["net_result_brl"] for point in equity_curve[1:]]
    capital_values = [point["capital_brl"] for point in equity_curve]
    return {
        "schema_version": 4,
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
            **total_breakdown,
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
    data, targets, quarantined = apply_funding_quarantine(data, targets)
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
        "funding_quarantined_symbols": quarantined,
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
