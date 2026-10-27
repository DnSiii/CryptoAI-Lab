"""Preregistered I1 t-1 variance-premium -> fixed put vertical -> native wallet.

Fixture-only until independently authenticated historical full lifecycle and
native terms exist. NO economic TRAIN, orders, ROI or promotion.
Prereg: research/V99_R106_I1_FIXED_VERTICAL_INTEGRATION_PREREG_20261026.md
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from research.tools.v99_r106_d1_real_train_source_join import FOLD_EDGES
from research.tools.v99_r106_i1_native_coin_account_replay import (
    Quote, Wallet, D, pair, account_nav, START, END,
)
from research.tools.v99_r106_i1_cost_bound_execution import (
    charge_floor, costed_open,
)

DAY = 86_400_000
LOT = Decimal("1")
SHORT_TARGET = Decimal("0.90")
LONG_TARGET = Decimal("0.80")
STRIKE_TOLERANCE = Decimal("0.02")
CASH = "CASH_NO_ELIGIBLE_SOURCE_OR_SIGNAL"
RISK_VETO = frozenset((
    "POSTENTRY_SCENARIO_COST_MAINTENANCE_VETO",
    "REUSED_OR_INSUFFICIENT_COIN_COLLATERAL",
    "POSTENTRY_MAINTENANCE_LOWER_BOUND_BREACH",
    "NEGATIVE_NET_PREMIUM",
    "UNVERIFIED_OR_INVALID_NATIVE_MARGIN_COST",
    "PRETRADE_MARK_OR_MAINTENANCE_VETO",
    "PRETRADE_ALL_POSITION_MARKS_REQUIRED",
))


def _check_signal(row):
    if not isinstance(row, dict):
        raise ValueError("UNVERIFIED_CAUSAL_SIGNAL_ROW")
    at_ms = row.get("decision_ms")
    asset = row.get("asset")
    signal = row.get("signal")
    fold = row.get("fold")
    if (type(at_ms) is not int or not START < at_ms < END
            or asset not in ("BTC", "ETH") or type(fold) is not int
            or fold not in (1, 2, 3, 4, 5)
            or signal not in ("POSITIVE_EX_ANTE_PREMIUM", "NO_PREMIUM", "NO_30D_HISTORY")):
        raise ValueError("UNVERIFIED_CAUSAL_SIGNAL_ROW")
    d = datetime.fromtimestamp(at_ms / 1000, tz=timezone.utc)
    if (d.weekday(), d.hour, d.minute, d.second, d.microsecond) != (0, 0, 0, 0, 0):
        raise ValueError("NONPREREGISTERED_SIGNAL_CLOCK")
    expected_fold = next((i for i in range(1, 6)
                          if FOLD_EDGES[i-1] <= at_ms < FOLD_EDGES[i]), None)
    if fold != expected_fold:
        raise ValueError("SIGNAL_FOLD_TIME_MISMATCH")
    if at_ms + 21 * DAY >= END:
        raise ValueError("SEALED_OR_RIGHT_CENSORED_SIGNAL")
    return at_ms, asset, signal


def select_fixed_vertical(signal_row: dict, last_asof_quotes: list[Quote]):
    """Select deterministic pair, or None. Quotes MUST already be latest as-of.

    This function does not certify that a supplied book is original. Upstream
    must independently verify original bytes, ordering, provenance and gaps.
    """
    at_ms, asset, signal = _check_signal(signal_row)
    if not isinstance(last_asof_quotes, (list, tuple)):
        raise ValueError("UNTRUSTED_QUOTE_COLLECTION")
    symbols = set()
    for q in last_asof_quotes:
        if not isinstance(q, Quote) or q.asset != asset or q.symbol in symbols:
            raise ValueError("DUPLICATED_OR_WRONG_ASSET_SOURCE_QUOTE")
        symbols.add(q.symbol)
        q.check(at_ms)  # malformed/stale/future rows revoke, never silently skip
    if signal != "POSITIVE_EX_ANTE_PREMIUM":
        return None
    eligible = [q for q in last_asof_quotes
                if 28 * DAY <= q.expiry_ms - at_ms <= 35 * DAY]
    candidates = []
    for short in eligible:
        spot = D(short.index_usd)
        if abs(D(short.strike_usd) / spot - SHORT_TARGET) > STRIKE_TOLERANCE:
            continue
        for long in eligible:
            if short.symbol == long.symbol:
                continue
            if abs(D(long.strike_usd) / spot - LONG_TARGET) > STRIKE_TOLERANCE:
                continue
            if D(short.bid_coin) <= D(long.ask_coin):
                continue
            try:
                pair(short, long, at_ms, LOT, "open")
            except ValueError:
                continue
            key = (abs(short.expiry_ms-at_ms-30*DAY),
                   abs(D(short.strike_usd)/spot-SHORT_TARGET),
                   abs(D(long.strike_usd)/spot-LONG_TARGET),
                   short.symbol, long.symbol)
            candidates.append((key, short, long))
    if not candidates:
        return None
    _, short, long = min(candidates, key=lambda item: item[0])
    return short, long


def fixture_open_fixed_vertical(wallet: Wallet, signal_row: dict,
                                last_asof_quotes: list[Quote], *,
                                name: str, initial_margin_coin,
                                maintenance_margin_coin, fixture: bool):
    """Single-decision integration. Explicitly refuses nonfixture economics.

    Historical path must use separately authenticated receipts, not this
    synthetic helper. Both cost paths use their fixed modeled floors.
    """
    if fixture is not True:
        raise ValueError("HISTORICAL_SOURCE_RECEIPTS_REQUIRE_INDEPENDENT_ATTESTATION")
    at_ms, asset, _ = _check_signal(signal_row)
    if wallet.asset != asset:
        raise ValueError("CROSS_COIN_COLLATERAL_NOT_ALLOWED")
    # A no-trade decision must never hide an unvalued existing portfolio.
    # A stale/absent same-clock mark is a hard failure, not a valid CASH row.
    wallet.check()
    if at_ms < wallet.last_ms:
        raise ValueError("DECISION_TIME_REVERSAL")
    if wallet.positions:
        if wallet.last_ms != at_ms:
            raise ValueError("PREDECISION_ALL_POSITION_MARKS_REQUIRED")
        try:
            account_nav(wallet, at_ms)
        except ValueError as exc:
            raise ValueError("PREDECISION_ALL_POSITION_MARKS_REQUIRED") from exc
    selected = select_fixed_vertical(signal_row, last_asof_quotes)
    if selected is None:
        return wallet, {"decision": CASH, "fixture": True,
                        "economic_train_executed": False,
                        "promotion_authorized": False}
    short, long = selected
    fees, slippage = charge_floor(wallet.scenario, LOT)
    try:
        result = costed_open(
            wallet, name, short, long, at_ms, LOT, fees, slippage,
            initial_margin_coin, maintenance_margin_coin, fixture=True)
    except ValueError as exc:
        if str(exc) not in RISK_VETO:
            raise
        return wallet, {"decision": "CASH_RISK_VETO", "reason": str(exc),
                        "fixture": True, "economic_train_executed": False,
                        "promotion_authorized": False}
    return result, {"decision": "MODELED_FIXTURE_OPEN_ONLY",
                    "short": short.symbol, "long": long.symbol,
                    "scenario": wallet.scenario, "modeled_fees_coin": str(fees),
                    "modeled_slippage_coin": str(slippage),
                    "fixture": True, "economic_train_executed": False,
                    "promotion_authorized": False}
