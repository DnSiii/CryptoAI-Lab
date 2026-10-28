"""I1 fixed native-coin events -> 661 TRAIN daily equity, never certified profits.

An executable ACCOUNTING bridge, not original Deribit source/fill attestation.
Preregistered: research/V99_R106_I1_NATIVE_EVENT_TO_661D_EQUITY_PREREG_20261028.md
No validation, holdout, paper, frozen state or orders are accessed.
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from research.tools.v99_r106_i1_native_coin_account_replay import (
    D, Quote, account_nav, mark_to_exit, open_vertical, settle_batch, start_wallet,
)
from research.tools.v99_r106_i1_fixed_vertical_bridge import select_fixed_vertical
from research.tools.v99_r106_i1_cost_bound_execution import charge_floor, verify_charges
from research.tools.v99_r106_i1_train_numeric_gate import (
    DAYS, REGIMES, SCENARIOS, _expected_clock, _fold,
)

SCHEMA = "V99_I1_NATIVE_EVENT_TO_661D_TRAIN_EQUITY_V1"
OUTPUT_SCHEMA = "V99_I1_FIXED_90W_DAILY_TRAIN_EQUITY_INPUT_V1"
NO_PROMOTION = {
    "original_options_economic_train_certified": False,
    "independent_original_trade_replay_verified": False,
    "historical_native_fee_certified": False,
    "freeze_authorized": False,
    "promotion_authorized": False,
    "validation_opened": False,
    "holdout_opened": False,
    "orders_enabled": False,
    "paper_publication_authorized": False,
}


def _quote(raw):
    if not isinstance(raw, dict):
        raise ValueError("MISSING_NATIVE_QUOTE_RECEIPT")
    try:
        return Quote(**{key: D(value) if key in (
            "strike_usd", "bid_coin", "ask_coin", "bid_native_lots",
            "ask_native_lots", "index_usd") else value
            for key, value in raw.items()})
    except (TypeError, KeyError) as exc:
        raise ValueError("INVALID_NATIVE_QUOTE_RECEIPT") from exc


def _open(wallet, event, at_ms):
    # The fixed signal and deterministic selector, not a caller-selected winner.
    quotes = [_quote(q) for q in event["quotes"]]
    chosen = select_fixed_vertical(event["signal"], quotes)
    if chosen is None:
        raise ValueError("OPEN_WITHOUT_FIXED_EX_ANTE_VERTICAL")
    short, long = chosen
    name = event["position_id"]
    qty = Decimal("1")
    fee, slip = D(event["fee_coin"]), D(event["slippage_coin"])
    verify_charges(wallet.scenario, qty, fee, slip)
    out = open_vertical(wallet, name, short, long, at_ms, qty, fee, slip,
                        event["initial_margin_coin"],
                        event["maintenance_margin_coin"])
    # Include immediate adverse liquidation-at-ask/bid and scenario exit costs.
    exit_fee, exit_slip = charge_floor(wallet.scenario, qty)
    immediate = max(D(0), qty*(D(short.ask_coin)-D(long.bid_coin))) + exit_fee + exit_slip
    existing = sum((D(mark[1]) for mark in wallet.marks), D(0))
    maintenance = sum((D(p.maintenance_margin_coin) for p in out.positions), D(0))
    if D(out.cash_coin)-existing-immediate < maintenance:
        raise ValueError("POSTENTRY_SCENARIO_COST_MAINTENANCE_VETO")
    return out


def _mark(wallet, event, at_ms):
    name = event["position_id"]
    position = next((p for p in wallet.positions if p.name == name), None)
    if position is None:
        raise ValueError("MARK_UNKNOWN_POSITION")
    fee, slip = D(event["fee_coin"]), D(event["slippage_coin"])
    verify_charges(wallet.scenario, position.qty, fee, slip)
    return mark_to_exit(wallet, name, _quote(event["short"]),
                        _quote(event["long"]), at_ms, fee, slip)


def _settle(wallet, event, at_ms):
    names = event["position_ids"]
    fees = event["delivery_fees_coin"]
    if not isinstance(names, list) or not isinstance(fees, dict):
        raise ValueError("INVALID_SETTLEMENT_JOURNAL")
    due = {p.name: p for p in wallet.positions if p.expiry_ms == at_ms}
    if not due or set(names) != set(due) or set(fees) != set(due):
        raise ValueError("INCOMPLETE_ATOMIC_SETTLEMENT_JOURNAL")
    for name, position in due.items():
        floor, _ = charge_floor(wallet.scenario, position.qty)
        if D(fees[name]) < floor:
            raise ValueError("SCENARIO_DELIVERY_FEE_UNDERPAYMENT")
    return settle_batch(wallet, names, at_ms, event["delivery_index_usd"], fees)


def _run_scenario(rows, scenario, initial_coin, initial_index, initial_usd):
    if not isinstance(rows, list) or len(rows) != DAYS:
        raise ValueError("INCOMPLETE_661_DAY_EVENT_JOURNAL")
    wallets = {a: start_wallet(a, scenario, initial_coin[a]) for a in ("BTC", "ETH")}
    result = []
    prev_clock = min(w.last_ms for w in wallets.values()) - 1
    for i, row in enumerate(rows):
        clock = _expected_clock(i)
        if (not isinstance(row, dict) or type(row.get("ts_ms")) is not int
                or row["ts_ms"] != clock or type(row.get("fold")) is not int
                or row["fold"] != _fold(clock) or row.get("regime") not in REGIMES):
            raise ValueError("FORGED_OR_SEALED_DAILY_EVENT_GRID")
        events = row.get("events")
        indices = row.get("index_usd")
        if (not isinstance(events, list) or not isinstance(indices, dict)
                or set(indices) != {"BTC", "ETH"}):
            raise ValueError("MISSING_NATIVE_DAILY_EVENTS_OR_INDICES")
        indices = {asset: D(indices[asset]) for asset in ("BTC", "ETH")}
        if any(v <= 0 for v in indices.values()):
            raise ValueError("INVALID_ORIGINAL_INDEX")
        last_event = prev_clock
        for event in events:
            if not isinstance(event, dict):
                raise ValueError("INVALID_NATIVE_JOURNAL_EVENT")
            at_ms, asset, kind = (event.get("at_ms"), event.get("asset"),
                                  event.get("kind"))
            if (type(at_ms) is not int or not prev_clock < at_ms <= clock
                    or at_ms < last_event or asset not in wallets):
                raise ValueError("NONCHRONOLOGICAL_OR_SEALED_NATIVE_EVENT")
            last_event = at_ms
            wallet = wallets[asset]
            if kind == "OPEN":
                wallet = _open(wallet, event, at_ms)
            elif kind == "MARK":
                wallet = _mark(wallet, event, at_ms)
            elif kind == "SETTLE_BATCH":
                wallet = _settle(wallet, event, at_ms)
            else:
                raise ValueError("UNREGISTERED_NATIVE_CASH_FLOW")
            wallets[asset] = wallet
        total = D(0)
        exposures = []
        for asset, wallet in wallets.items():
            if wallet.positions:
                # No stale/missing mark or caller-forged native NAV is accepted.
                if wallet.last_ms != clock:
                    raise ValueError("MISSING_SAME_CLOCK_DAILY_OPEN_MARK")
                nav = account_nav(wallet, clock)
                if D(nav["nav_usd_equivalent_at_source_index"]) != (
                    D(nav["nav_coin"])*indices[asset]):
                    raise ValueError("UNBOUND_ORIGINAL_INDEX_FOR_DAILY_NAV")
            else:
                wallet = replace(wallet, last_ms=clock)
                wallets[asset] = wallet
                nav = account_nav(wallet, clock, flat_index_usd=indices[asset])
            total += D(nav["nav_usd_equivalent_at_source_index"])
            exposures.extend(asset+":"+p.name for p in wallet.positions)
        if total <= 0:
            raise ValueError("INSOLVENT_NATIVE_DAILY_NAV")
        benchmark = D(row.get("benchmark_usd"))
        if benchmark <= 0:
            raise ValueError("INVALID_ORIGINAL_BENCHMARK")
        result.append({
            "ts_ms": clock, "fold": row["fold"], "regime": row["regime"],
            "equity_usd": str(total), "benchmark_usd": str(benchmark),
            "actual_exposure_key": "|".join(sorted(exposures)) or "CASH",
        })
        prev_clock = clock
    return result


def replay(document):
    if (not isinstance(document, dict) or document.get("schema") != SCHEMA
            or type(document.get("fixture")) is not bool
            or set(document.get("scenarios", {})) != set(SCENARIOS)):
        raise ValueError("INVALID_NATIVE_EVENT_JOURNAL_SCHEMA")
    initial_coin = document.get("initial_coin")
    initial_index = document.get("initial_index_usd")
    if (not isinstance(initial_coin, dict) or not isinstance(initial_index, dict)
            or set(initial_coin) != {"BTC", "ETH"}
            or set(initial_index) != {"BTC", "ETH"}):
        raise ValueError("INVALID_INITIAL_NATIVE_WALLETS")
    coin = {a: D(initial_coin[a]) for a in ("BTC", "ETH")}
    index = {a: D(initial_index[a]) for a in ("BTC", "ETH")}
    if any(coin[a] <= 0 or index[a] <= 0 for a in coin):
        raise ValueError("INVALID_INITIAL_NATIVE_CAPITAL")
    initial_usd = sum((coin[a]*index[a] for a in coin), D(0))
    if initial_usd != D(document.get("initial_capital_usd")):
        raise ValueError("INITIAL_NATIVE_CAPITAL_NOT_SELF_FINANCING")
    results = {scenario: _run_scenario(document["scenarios"][scenario],
                                      scenario, coin, index, initial_usd)
               for scenario in SCENARIOS}
    a, b = (results[name] for name in SCENARIOS)
    if any((x["ts_ms"], x["regime"], x["benchmark_usd"]) !=
           (y["ts_ms"], y["regime"], y["benchmark_usd"])
           for x, y in zip(a, b)):
        raise ValueError("SCENARIO_BENCHMARK_OR_REGIME_PATH_MISMATCH")
    # Scenario costs may change exposures, never the original market index.
    # Compare the source path itself, not the derived NAV.
    for severe_day, super_day in zip(document["scenarios"]["severe"],
                                     document["scenarios"]["supersevere"]):
        for asset in ("BTC", "ETH"):
            if D(severe_day["index_usd"][asset]) != D(super_day["index_usd"][asset]):
                raise ValueError("SCENARIO_ORIGINAL_INDEX_PATH_MISMATCH")
    return {
        "schema": OUTPUT_SCHEMA, "fixture": document["fixture"],
        "initial_capital_usd": str(initial_usd),
        "scenarios": results,
        "status": ("FIXTURE_NATIVE_EVENT_EQUITY_ONLY" if document["fixture"]
                   else "PROVISIONAL_UNCERTIFIED_NATIVE_EVENT_EQUITY"),
        "original_source_receipts_independently_authenticated": False,
        "original_historical_economic_train_executed": False,
        **NO_PROMOTION,
    }


def main(input_path, output_path):
    source = json.loads(Path(input_path).read_text(encoding="utf-8"))
    report = replay(source)
    Path(output_path).write_text(json.dumps(report, indent=2, sort_keys=True)+"\n",
                                 encoding="utf-8")
    print(json.dumps({"status": report["status"], "days": DAYS,
                      "economic_train_certified": False,
                      "promotion_authorized": False}, sort_keys=True))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m research.tools.v99_r106_i1_native_event_equity INPUT_JSON OUTPUT_JSON")
    main(*sys.argv[1:])
