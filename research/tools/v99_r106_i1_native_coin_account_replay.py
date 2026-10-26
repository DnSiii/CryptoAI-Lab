"""V99 I1 native BTC/ETH coin-account event replay (research-only).

No authenticated historical fills, native fee tier, or margin rules are implied.
This is deterministic accounting machinery, NOT an economic TRAIN or orders.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

START = 1639008000000
END = 1696118400000
MAX_AGE_MS = 300_000
MAX_SKEW_MS = 1_000
MIN_TENOR_MS = 21 * 86_400_000
MAX_TENOR_MS = 45 * 86_400_000
ASSETS = ("BTC", "ETH")
SCENARIOS = ("severe", "supersevere")


def D(value):
    if isinstance(value, bool):
        raise ValueError("BOOLEAN_NOT_NUMERIC")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("BAD_COIN_NUMBER") from exc
    if not result.is_finite():
        raise ValueError("NONFINITE_COIN_NUMBER")
    return result


@dataclass(frozen=True)
class Quote:
    asset: str
    symbol: str
    expiry_ms: int
    strike_usd: Decimal
    bid_coin: Decimal
    ask_coin: Decimal
    bid_native_lots: Decimal
    ask_native_lots: Decimal
    venue_ms: int
    arrival_ms: int
    index_usd: Decimal

    def check(self, asof_ms):
        if self.asset not in ASSETS or type(asof_ms) is not int:
            raise ValueError("INVALID_ASSET_OR_CLOCK")
        parts = self.symbol.split("-")
        if len(parts) != 4 or parts[0] != self.asset or parts[3] != "P":
            raise ValueError("INVALID_NATIVE_INSTRUMENT")
        try:
            expiry = datetime.strptime(parts[1].upper(), "%d%b%y").replace(
                hour=8, tzinfo=timezone.utc)
            strike = D(parts[2])
        except (ValueError, OverflowError) as exc:
            raise ValueError("INVALID_NATIVE_EXPIRY") from exc
        if (self.expiry_ms != int(expiry.timestamp() * 1000)
                or D(self.strike_usd) != strike or strike <= 0):
            raise ValueError("INSTRUMENT_TERMS_MISMATCH")
        if not (START <= self.venue_ms <= self.arrival_ms < asof_ms < END
                and self.expiry_ms < END and asof_ms < self.expiry_ms
                and asof_ms-self.arrival_ms <= MAX_AGE_MS
                and asof_ms-self.venue_ms <= MAX_AGE_MS):
            raise ValueError("NONCAUSAL_STALE_OR_SEALED_QUOTE")
        if not (D(self.index_usd) > 0 and
                0 < D(self.bid_coin) < D(self.ask_coin) and
                D(self.bid_native_lots) > 0 and D(self.ask_native_lots) > 0):
            raise ValueError("INVALID_NATIVE_BOOK")


def pair(short: Quote, long: Quote, asof_ms: int, qty: Decimal, side: str):
    short.check(asof_ms)
    long.check(asof_ms)
    if not (short.asset == long.asset
            and short.expiry_ms == long.expiry_ms
            and D(short.strike_usd) > D(long.strike_usd) > 0
            and short.symbol != long.symbol
            and D(short.index_usd) == D(long.index_usd)
            and abs(short.arrival_ms-long.arrival_ms) <= MAX_SKEW_MS
            and abs(short.venue_ms-long.venue_ms) <= MAX_SKEW_MS):
        raise ValueError("UNSYNCHRONIZED_OR_WRONG_VERTICAL")
    qty = D(qty)
    if qty <= 0:
        raise ValueError("NONPOSITIVE_NATIVE_LOTS")
    if side == "open":
        sizes = (short.bid_native_lots, long.ask_native_lots)
    elif side == "close":
        sizes = (short.ask_native_lots, long.bid_native_lots)
    else:
        raise ValueError("INVALID_BOOK_SIDE")
    if any(qty > D(size) for size in sizes):
        raise ValueError("INSUFFICIENT_ORIGINAL_NATIVE_DEPTH")


@dataclass(frozen=True)
class Position:
    name: str
    short_symbol: str
    long_symbol: str
    expiry_ms: int
    high: Decimal
    low: Decimal
    qty: Decimal
    initial_margin_coin: Decimal
    maintenance_margin_coin: Decimal


@dataclass(frozen=True)
class Wallet:
    asset: str
    scenario: str
    initial_coin: Decimal
    cash_coin: Decimal
    reserved_coin: Decimal
    positions: tuple[Position, ...]
    marks: tuple[tuple[str, Decimal, int, Decimal], ...]
    settled: tuple[str, ...]
    last_ms: int

    def check(self):
        if self.asset not in ASSETS or self.scenario not in SCENARIOS:
            raise ValueError("INVALID_COIN_WALLET")
        if (D(self.initial_coin) <= 0 or D(self.cash_coin) < 0
                or D(self.reserved_coin) < 0
                or D(self.cash_coin) < D(self.reserved_coin)
                or not START <= self.last_ms < END):
            raise ValueError("INSOLVENT_OR_SEALED_WALLET")
        names = [p.name for p in self.positions]
        if len(set(names + list(self.settled))) != len(names) + len(self.settled):
            raise ValueError("DUPLICATE_COIN_POSITION")
        if D(self.reserved_coin) != sum(
                (D(p.initial_margin_coin) for p in self.positions), Decimal(0)):
            raise ValueError("FABRICATED_COIN_RESERVE")
        mark_names = [name for name, _, _, _ in self.marks]
        if len(mark_names) != len(set(mark_names)) or any(
                name not in names for name in mark_names):
            raise ValueError("FABRICATED_OR_DUPLICATE_MARK")
        # A deserialized or externally reconstructed Wallet must not be
        # able to invent negative exit liabilities or an invalid NAV index.
        # These invariants are checked even before account_nav is requested.
        for p in self.positions:
            if (not isinstance(p.name, str) or not p.name
                    or type(p.expiry_ms) is not int
                    or not START < p.expiry_ms < END
                    or not (D(p.high) > D(p.low) > 0
                            and D(p.qty) > 0
                            and D(p.initial_margin_coin) >= D(p.maintenance_margin_coin) > 0)):
                raise ValueError("INVALID_OPEN_COIN_POSITION")
        for _, liability, t, index in self.marks:
            if (type(t) is not int or not START <= t <= self.last_ms
                    or D(liability) < 0 or D(index) <= 0):
                raise ValueError("INVALID_COIN_MARK_PROVENANCE")
        if any(p.expiry_ms < self.last_ms for p in self.positions):
            raise ValueError("UNSETTLED_EXPIRED_POSITION")


def start_wallet(asset: str, scenario: str, initial_coin) -> Wallet:
    w = Wallet(asset, scenario, D(initial_coin), D(initial_coin), D(0),
               (), (), (), START)
    w.check()
    return w


def open_vertical(w: Wallet, name: str, short: Quote, long: Quote, at_ms: int,
                  native_lots, entry_fees_coin, entry_slippage_coin,
                  initial_margin_coin, maintenance_margin_coin) -> Wallet:
    w.check()
    if not isinstance(name, str) or not 0 < len(name) <= 128:
        raise ValueError("INVALID_POSITION_ID")
    if name in w.settled or any(p.name == name for p in w.positions):
        raise ValueError("DUPLICATE_POSITION")
    if at_ms < w.last_ms or short.asset != w.asset:
        raise ValueError("WRONG_COIN_WALLET_OR_CLOCK")
    # Never finance a fresh position against stale or absent open-position NAV.
    # Existing positions must be re-marked at this SAME decision using quotes
    # strictly received before it; maintenance failure vetoes the new opening.
    if w.positions:
        if at_ms != w.last_ms:
            raise ValueError("PRETRADE_ALL_POSITION_MARKS_REQUIRED")
        try:
            account_nav(w, at_ms)
        except ValueError as exc:
            raise ValueError("PRETRADE_MARK_OR_MAINTENANCE_VETO") from exc
    t = datetime.fromtimestamp(at_ms / 1000, tz=timezone.utc)
    if (t.weekday(), t.hour, t.minute, t.second, t.microsecond) != (0,0,0,0,0):
        raise ValueError("NONPREREGISTERED_MONDAY_OPEN")
    if not MIN_TENOR_MS <= short.expiry_ms-at_ms <= MAX_TENOR_MS:
        raise ValueError("NONPREREGISTERED_EXPIRY_TENOR")
    pair(short, long, at_ms, D(native_lots), "open")
    qty = D(native_lots)
    fees, slip = D(entry_fees_coin), D(entry_slippage_coin)
    initial, maintenance = D(initial_margin_coin), D(maintenance_margin_coin)
    if not (fees >= 0 and slip >= 0 and initial >= maintenance > 0):
        raise ValueError("UNVERIFIED_OR_INVALID_NATIVE_MARGIN_COST")
    premium = qty * (D(short.bid_coin)-D(long.ask_coin)) - fees - slip
    if premium <= 0:
        raise ValueError("NEGATIVE_NET_PREMIUM")
    cash = D(w.cash_coin)+premium
    reserve = D(w.reserved_coin)+initial
    if cash < reserve:
        raise ValueError("REUSED_OR_INSUFFICIENT_COIN_COLLATERAL")
    # Existing marks and the new entry must reference one exact as-of
    # underlying index; different clocks/indices cannot be netted as NAV.
    if w.positions and any(D(m[3]) != D(short.index_usd) for m in w.marks):
        raise ValueError("POSTENTRY_UNBOUND_UNDERLYING_INDEX")
    # A conservative minimum liability is already observable from the
    # SAME predecision two-sided book. It excludes unknown exit costs, so
    # passing this check is NOT a certified posttrade solvency statement.
    minimum_exit_liability = max(
        Decimal(0), qty*(D(short.ask_coin)-D(long.bid_coin)))
    existing_liabilities = sum((D(m[1]) for m in w.marks), Decimal(0))
    existing_maintenance = sum(
        (D(p.maintenance_margin_coin) for p in w.positions), Decimal(0))
    if cash-existing_liabilities-minimum_exit_liability < existing_maintenance+maintenance:
        raise ValueError("POSTENTRY_MAINTENANCE_LOWER_BOUND_BREACH")
    p = Position(name, short.symbol, long.symbol, short.expiry_ms,
                 D(short.strike_usd), D(long.strike_usd), qty,
                 initial, maintenance)
    out = replace(w, cash_coin=cash, reserved_coin=reserve,
                  positions=w.positions+(p,), last_ms=at_ms)
    out.check()
    return out


def mark_to_exit(w: Wallet, name: str, short: Quote, long: Quote,
                 at_ms: int, exit_fees_coin, exit_slippage_coin) -> Wallet:
    w.check()
    if at_ms < w.last_ms:
        raise ValueError("TIME_REVERSAL")
    p = next((x for x in w.positions if x.name == name), None)
    if p is None or not at_ms < p.expiry_ms:
        raise ValueError("MISSING_OR_EXPIRED_POSITION")
    if (short.asset != w.asset or short.symbol != p.short_symbol
            or long.symbol != p.long_symbol):
        raise ValueError("UNBOUND_MARK_INSTRUMENT")
    pair(short, long, at_ms, p.qty, "close")
    fees, slip = D(exit_fees_coin), D(exit_slippage_coin)
    if fees < 0 or slip < 0:
        raise ValueError("NEGATIVE_EXIT_FRICTION")
    # No negative liability credit for a crossed two-leg synthetic exit.
    liability = max(Decimal(0), p.qty*(D(short.ask_coin)-D(long.bid_coin)))+fees+slip
    marks = tuple(m for m in w.marks if m[0] != name) + ((name, liability, at_ms, D(short.index_usd)),)
    out = replace(w, marks=marks, last_ms=at_ms)
    out.check()
    return out


def account_nav(w: Wallet, at_ms: int) -> dict:
    w.check()
    if at_ms != w.last_ms:
        raise ValueError("UNBOUND_MARK_TIME_OR_INDEX")
    if len(w.marks) != len(w.positions) or any(
            t != at_ms for _, _, t, _ in w.marks):
        raise ValueError("MISSING_OR_STALE_OPEN_POSITION_MARKS")
    indices = {idx for _, _, _, idx in w.marks}
    if len(indices) != 1 or next(iter(indices)) <= 0:
        raise ValueError("UNSYNCHRONIZED_SOURCE_INDEX_FOR_NAV")
    index_usd = next(iter(indices))
    liabilities = sum((D(x) for _, x, _, _ in w.marks), Decimal(0))
    nav = D(w.cash_coin)-liabilities
    maintenance = sum((D(p.maintenance_margin_coin) for p in w.positions), Decimal(0))
    if nav < maintenance:
        raise ValueError("MAINTENANCE_BREACH_REQUIRES_AUTHENTICATED_LIQUIDATION_MODEL")
    return {"nav_coin": str(nav), "nav_usd_equivalent_at_source_index":
            str(nav*D(index_usd)), "reserved_coin_not_nav": str(w.reserved_coin),
            "modeled_only": True, "historical_economic_train": False,
            "promotion_authorized": False, "orders_enabled": False}


def settle(w: Wallet, name: str, at_ms: int, original_delivery_index_usd,
           delivery_fee_coin) -> Wallet:
    w.check()
    p = next((x for x in w.positions if x.name == name), None)
    if p is None or at_ms != p.expiry_ms or at_ms < w.last_ms:
        raise ValueError("NONCONTRACTUAL_OR_NONCHRONOLOGICAL_SETTLEMENT")
    if any(x.expiry_ms < at_ms for x in w.positions if x.name != name):
        raise ValueError("UNSETTLED_EARLIER_EXPIRY")
    index, fee = D(original_delivery_index_usd), D(delivery_fee_coin)
    if index <= 0 or fee < 0:
        raise ValueError("MISSING_OR_INVALID_NATIVE_DELIVERY_TERMS")
    due = p.qty*(max(p.high-index, D(0))-max(p.low-index, D(0)))/index
    cash = D(w.cash_coin)-due-fee
    if cash < 0:
        raise ValueError("NEGATIVE_COIN_SETTLEMENT_NO_LIQUIDATION_MODEL")
    out = replace(w, cash_coin=cash,
                  reserved_coin=D(w.reserved_coin)-p.initial_margin_coin,
                  positions=tuple(x for x in w.positions if x.name != name),
                  marks=tuple(m for m in w.marks if m[0] != name),
                  settled=w.settled+(name,), last_ms=at_ms)
    out.check()
    return out
