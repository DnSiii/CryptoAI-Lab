"""I1 reusable defined-risk vertical-put cash ledger, isolated economic plumbing.

NO STRATEGY, NO HISTORICAL BACKTEST, NO ORDERS. This is USD-equivalent modeled
settlement accounting for future verified native Deribit option quotes. It is
NOT native margin/liquidation or actual account fills. Never promote from tests.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
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
        # Bind economic inputs to the literal Deribit instrument ID.
        parts = self.symbol.split("-")
        if len(parts) != 4 or parts[0] != self.asset or parts[3] != "P" or self.asset not in ("BTC", "ETH"):
            raise ValueError("WRONG_OPTION_INSTRUMENT")
        try:
            expiry = datetime.strptime(parts[1].upper(), "%d%b%y").replace(hour=8, tzinfo=timezone.utc)
            canonical_expiry_ms = int(expiry.timestamp() * 1000)
            canonical_strike = Decimal(parts[2])
            quoted_strike = Decimal(str(self.strike_usd))
        except (ValueError, InvalidOperation, OverflowError) as exc:
            raise ValueError("INVALID_OPTION_INSTRUMENT_ID") from exc
        if not canonical_strike.is_finite() or canonical_strike <= 0 or canonical_strike != quoted_strike or canonical_expiry_ms != self.expiry_ms:
            raise ValueError("OPTION_ID_STRIKE_OR_EXPIRY_MISMATCH")
        if not TRAIN_START_MS <= decision_ms < TRAIN_END_MS:
            raise ValueError("SEALED_VALIDATION_OR_HOLDOUT")
        if not (self.venue_ms <= self.arrival_ms <= decision_ms
                and decision_ms-self.arrival_ms <= MAX_QUOTE_AGE_MS
                and decision_ms-self.venue_ms <= MAX_QUOTE_AGE_MS):
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
    entry_spot_usd: float = 0.0

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
                "pnl_usd": nav-self.initial_cash_usd,
                "modeled_usd_equivalent_only": True,
                "native_coin_margin_certified": False,
                "promotion_authorized": False,
                "orders_enabled": False}


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
                  cash, reserve, credit, entry_cost, scenario, spot)


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
            "modeled_only": True, "orders_enabled": False,
            "native_coin_margin_certified": False,
            "promotion_authorized": False}

def inverse_coin_expiry_diagnostic(spread: Spread, delivery_index_usd: float) -> dict:
    """COIN-COLLATERAL COUNTERFACTUAL, not executable historical NAV.

    Deribit inverse BTC/ETH option intrinsic USD settles as USD/index IN COIN.
    The existing USD-equivalent expiry_nav() is not a native coin ledger.
    Assumes entire initial USD capital converted to coin at entry with zero FX
    friction, and no liquidation. Both assumptions are deliberately visible.
    """
    if not isinstance(spread, Spread) or spread.entry_spot_usd <= 0:
        raise ValueError("UNBOUND_ENTRY_SPOT")
    if not isfinite(delivery_index_usd) or delivery_index_usd <= 0:
        raise ValueError("INVALID_NATIVE_DELIVERY_INDEX")
    if spread.expiry_ms >= TRAIN_END_MS or spread.decision_ms < TRAIN_START_MS:
        raise ValueError("SEALED_OR_UNTRUSTED_PARTITION")
    s = Decimal(str(delivery_index_usd))
    entry = Decimal(str(spread.entry_spot_usd))
    qty = Decimal(str(spread.qty))
    high = Decimal(str(spread.short_strike_usd))
    low = Decimal(str(spread.long_strike_usd))
    opening_coin = Decimal(str(spread.initial_cash_usd)) / entry
    net_premium_coin = Decimal(str(spread.premium_credit_usd)) / entry
    intrinsic_usd = qty * (max(high-s, Decimal(0)) - max(low-s, Decimal(0)))
    obligation_coin = intrinsic_usd / s
    remaining_coin = opening_coin + net_premium_coin - obligation_coin
    coin_usd = remaining_coin * s
    old_usd = Decimal(str(spread.expiry_nav(delivery_index_usd)["nav_usd"]))
    return {
        "schema": "I1_INVERSE_COIN_EXPIRY_COUNTERFACTUAL_ONLY_V1",
        "opening_coin_assuming_full_conversion": float(opening_coin),
        "net_premium_coin": float(net_premium_coin),
        "intrinsic_obligation_usd": float(intrinsic_usd),
        "intrinsic_obligation_coin": float(obligation_coin),
        "remaining_coin_without_liquidation": float(remaining_coin),
        "coin_account_usd_without_liquidation": float(coin_usd),
        "prior_usd_equivalent_model_nav": float(old_usd),
        "currency_basis_nav_gap_usd": float(coin_usd-old_usd),
        "hypothetical_coin_insolvency": remaining_coin < 0,
        "requires_historical_delivery_index_twap": True,
        "requires_coin_margin_liquidation_and_fx_execution": True,
        "native_fee_tier_authenticated": False,
        "real_execution_authenticated": False,
        "historical_train_economics_run": False,
        "promotion_authorized": False,
        "orders_enabled": False,
        "modeled_only": True,
    }


def replay_inverse_coin_expiry_from_quotes(
    spread: Spread,
    short_quote: PutQuote,
    long_quote: PutQuote,
    delivery_index_usd: float,
    modeled_delivery_fee_coin: float | None = None,
) -> dict:
    """Independent-source-input coin cashflow replay, NOT exchange margin certification.

    Uses ORIGINAL opening bid/ask premiums denominated in BTC/ETH, not the
    previous USD-equivalent ledger's net cash. Models two entry-side fee/slip
    charges in coin; the optional expiry fee is an EXPLICIT synthetic input.
    Never infer a historically certified delivery index from OKX hourly OHLC.
    A negative balance means an insolvent *no-liquidation counterfactual*.
    """
    if not isinstance(spread, Spread) or spread.scenario not in COST_SCENARIOS:
        raise ValueError("INVALID_SPREAD_OR_SCENARIO")
    short_quote.validate(spread.decision_ms)
    long_quote.validate(spread.decision_ms)
    if not (
        short_quote.asset == long_quote.asset == spread.asset
        and short_quote.expiry_ms == long_quote.expiry_ms == spread.expiry_ms
        and short_quote.strike_usd == spread.short_strike_usd
        and long_quote.strike_usd == spread.long_strike_usd
        and short_quote.symbol != long_quote.symbol
        and short_quote.bid_qty >= spread.qty
        and long_quote.ask_qty >= spread.qty
        and short_quote.spot_usd == long_quote.spot_usd == spread.entry_spot_usd
    ):
        raise ValueError("UNBOUND_OPENING_QUOTES_OR_INSUFFICIENT_DEPTH")
    if not isfinite(delivery_index_usd) or delivery_index_usd <= 0:
        raise ValueError("INVALID_DELIVERY_INDEX")
    if modeled_delivery_fee_coin is not None and (
        not isfinite(modeled_delivery_fee_coin) or modeled_delivery_fee_coin < 0
    ):
        raise ValueError("INVALID_MODELED_DELIVERY_FEE")
    D = lambda value: Decimal(str(value))
    q = D(spread.qty)
    entry = D(spread.entry_spot_usd)
    fee, slip = COST_SCENARIOS[spread.scenario]
    gross_credit_coin = q * (D(short_quote.bid_coin) - D(long_quote.ask_coin))
    entry_friction_coin = D(2) * q * (D(fee) + D(slip))
    net_credit_coin = gross_credit_coin - entry_friction_coin
    # Ensure the original spread was opened from these SAME original quotes.
    if abs(net_credit_coin * entry - D(spread.premium_credit_usd)) > D("0.0000001"):
        raise ValueError("OPENING_QUOTE_PREMIUM_NOT_BOUND_TO_SPREAD")
    opening_coin = D(spread.initial_cash_usd) / entry
    s = D(delivery_index_usd)
    intrinsic_usd = q * (
        max(D(spread.short_strike_usd) - s, D(0))
        - max(D(spread.long_strike_usd) - s, D(0))
    )
    intrinsic_coin = intrinsic_usd / s
    expiry_fee = D(modeled_delivery_fee_coin) if modeled_delivery_fee_coin is not None else D(0)
    no_liquidation_coin = opening_coin + net_credit_coin - intrinsic_coin - expiry_fee
    return {
        "schema": "I1_ORIGINAL_OPEN_QUOTES_INVERSE_COIN_EXPIRY_MODELED_V1",
        "asset": spread.asset,
        "scenario": spread.scenario,
        "opening_coin_full_conversion_assumption": float(opening_coin),
        "gross_opening_credit_coin": float(gross_credit_coin),
        "modeled_opening_friction_coin": float(entry_friction_coin),
        "net_opening_credit_coin": float(net_credit_coin),
        "intrinsic_usd": float(intrinsic_usd),
        "intrinsic_settlement_coin": float(intrinsic_coin),
        "modeled_delivery_fee_coin": (
            None if modeled_delivery_fee_coin is None else float(expiry_fee)
        ),
        "coin_balance_without_margin_liquidation": float(no_liquidation_coin),
        "usd_equivalent_at_delivery_without_margin_liquidation": float(no_liquidation_coin * s),
        "hypothetical_insolvency": no_liquidation_coin < 0,
        "delivery_fee_missing": modeled_delivery_fee_coin is None,
        "requires_original_delivery_twap_receipt": True,
        "requires_historical_coin_margin_liquidation_rules": True,
        "requires_authenticated_historical_fee_and_execution": True,
        "historical_train_economics_run": False,
        "native_margin_certified": False,
        "promotion_authorized": False,
        "orders_enabled": False,
        "modeled_only": True,
    }
