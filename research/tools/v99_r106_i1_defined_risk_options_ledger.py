"""I1 reusable defined-risk vertical-put cash ledger, isolated economic plumbing.

NO STRATEGY, NO HISTORICAL BACKTEST, NO ORDERS. This is USD-equivalent modeled
settlement accounting for future verified native Deribit option quotes. It is
NOT native margin/liquidation or actual account fills. Never promote from tests.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite

TRAIN_END_MS = 1696118400000
TRAIN_START_MS = 1639008000000
MAX_QUOTE_AGE_MS = 300_000
COST_SCENARIOS = {
    "severe": (0.0012, 0.0012),
    "supersevere": (0.0024, 0.0024),
}


@dataclass(frozen=True)
class PutQuote:
    asset: str
    symbol: str
    expiry_ms: int
    strike_usd: float
    bid_coin: float
    ask_coin: float
    bid_qty: float
    ask_qty: float
    venue_ms: int
    arrival_ms: int
    spot_usd: float

    def validate(self, decision_ms):
        if self.asset not in ("BTC", "ETH") or not self.symbol.endswith("-P"):
            raise ValueError("WRONG_OPTION_INSTRUMENT")
        if not TRAIN_START_MS <= decision_ms < TRAIN_END_MS:
            raise ValueError("SEALED_VALIDATION_OR_HOLDOUT")
        if not (self.venue_ms <= self.arrival_ms <= decision_ms
                and decision_ms-self.arrival_ms <= MAX_QUOTE_AGE_MS):
            raise ValueError("NONCAUSAL_OR_STALE_OPTION_QUOTE")
        if not (decision_ms < self.expiry_ms < TRAIN_END_MS):
            raise ValueError("EXPIRY_OUTSIDE_TRAIN")
        vals = (self.strike_usd, self.bid_coin, self.ask_coin, self.bid_qty,
                self.ask_qty, self.spot_usd)
        if not all(isfinite(x) and x > 0 for x in vals):
            raise ValueError("INVALID_NATIVE_QUOTE")
        if not self.bid_coin < self.ask_coin:
            raise ValueError("CROSSED_OR_LOCKED_NATIVE_QUOTE")


@dataclass(frozen=True)
class Spread:
    decision_ms: int
    expiry_ms: int
    asset: str
    qty: float
    short_strike_usd: float
    long_strike_usd: float
    initial_cash_usd: float
    cash_after_open_usd: float
    collateral_reserved_usd: float
    premium_credit_usd: float
    entry_cost_usd: float
    scenario: str

    def expiry_nav(self, settlement_spot_usd):
        if not isfinite(settlement_spot_usd) or settlement_spot_usd <= 0:
            raise ValueError("BAD_SETTLEMENT_SPOT")
        obligation = self.qty * (
            max(self.short_strike_usd-settlement_spot_usd, 0)
            - max(self.long_strike_usd-settlement_spot_usd, 0))
        nav = self.cash_after_open_usd-obligation
        if obligation < -1e-9 or obligation > self.collateral_reserved_usd+1e-9:
            raise ValueError("DEFINED_RISK_PAYOFF_VIOLATION")
        return {"nav_usd": nav, "settlement_payoff_usd": obligation,
                "collateral_released_usd": self.collateral_reserved_usd,
                "pnl_usd": nav-self.initial_cash_usd}


def open_vertical(short_put, long_put, decision_ms, initial_cash_usd,
                  scenario="severe", risk_fraction=0.05):
    if scenario not in COST_SCENARIOS or risk_fraction != 0.05:
        raise ValueError("UNPREREGISTERED_COST_OR_RISK")
    short_put.validate(decision_ms)
    long_put.validate(decision_ms)
    if not (short_put.asset == long_put.asset
            and short_put.expiry_ms == long_put.expiry_ms
            and short_put.strike_usd > long_put.strike_usd
            and short_put.symbol != long_put.symbol):
        raise ValueError("INVALID_VERTICAL_PAIR")
    if abs(short_put.spot_usd-long_put.spot_usd) > 1e-9:
        raise ValueError("MISMATCHED_CAUSAL_UNDERLYING")
    if not isfinite(initial_cash_usd) or initial_cash_usd <= 0:
        raise ValueError("BAD_INITIAL_CAPITAL")
    fee, slip = COST_SCENARIOS[scenario]
    width = short_put.strike_usd-long_put.strike_usd
    # Maximum 5% initial NAV is reserved as the full USD strike width.
    # No leverage, no naked short, no reuse of collateral.
    qty = min(short_put.bid_qty, long_put.ask_qty,
              initial_cash_usd*risk_fraction/width)
    if qty <= 0:
        raise ValueError("NO_DISPLAYED_SIZE")
    spot = short_put.spot_usd
    gross_credit = qty*(short_put.bid_coin-long_put.ask_coin)*spot
    # Stress fee and slippage per leg are USD-notional models, NOT authenticated
    # historical Deribit account-specific fee tier or executable fills.
    entry_cost = 2*qty*spot*(fee+slip)
    credit = gross_credit-entry_cost
    if credit <= 0:
        raise ValueError("NEGATIVE_AFTER_COST_CREDIT_NO_ENTRY")
    reserve = qty*width
    cash = initial_cash_usd+credit
    if cash-reserve < -1e-8:
        raise ValueError("INSUFFICIENT_COLLATERAL")
    return Spread(decision_ms, short_put.expiry_ms, short_put.asset, qty,
                  short_put.strike_usd, long_put.strike_usd, initial_cash_usd,
                  cash, reserve, credit, entry_cost, scenario)


def liquidation_nav(spread, short_quote, long_quote, mark_ms):
    # Strict bid/ask exit, no mid-price fiction. Margin/liquidation remains
    # unverified: this is conservative mark-to-exit, not a real exchange fill.
    short_quote.validate(mark_ms)
    long_quote.validate(mark_ms)
    if mark_ms <= spread.decision_ms or mark_ms >= spread.expiry_ms:
        raise ValueError("BAD_MARK_TIME")
    if (short_quote.asset != spread.asset or long_quote.asset != spread.asset
            or short_quote.expiry_ms != spread.expiry_ms
            or long_quote.expiry_ms != spread.expiry_ms
            or short_quote.strike_usd != spread.short_strike_usd
            or long_quote.strike_usd != spread.long_strike_usd):
        raise ValueError("MARK_INSTRUMENT_MISMATCH")
    if short_quote.ask_qty < spread.qty or long_quote.bid_qty < spread.qty:
        raise ValueError("INSUFFICIENT_EXIT_DEPTH")
    fee, slip = COST_SCENARIOS[spread.scenario]
    spot = short_quote.spot_usd
    if abs(spot-long_quote.spot_usd) > 1e-9:
        raise ValueError("MISMATCHED_MARK_UNDERLYING")
    exit_debit = spread.qty*(short_quote.ask_coin-long_quote.bid_coin)*spot
    exit_cost = 2*spread.qty*spot*(fee+slip)
    return {"nav_usd": spread.cash_after_open_usd-exit_debit-exit_cost,
            "exit_debit_usd": exit_debit, "exit_cost_usd": exit_cost,
            "modeled_only": True, "orders_enabled": False}
