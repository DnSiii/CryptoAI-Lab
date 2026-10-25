"""I1 overlapping-position USD-equivalent CASH/RESERVE ledger, no economic TRAIN.

This is deliberately not an inverse-coin margin model, executable fill simulator,
native fee schedule, option mark-to-market NAV, or strategy selection engine.
No orders, promotion, paper or holdout access.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import isclose, isfinite

from research.tools.v99_r106_i1_defined_risk_options_ledger import (
    COST_SCENARIOS, TRAIN_END_MS, TRAIN_START_MS, PutQuote, Spread, open_vertical,
)

MAX_AGGREGATE_WIDTH_FRACTION = 0.20


@dataclass(frozen=True)
class LedgerEvent:
    """Immutable replay input; NOT a venue fill or authenticated market receipt."""
    kind: str
    position_id: str
    time_ms: int
    spread: Spread | None = None
    short_quote: PutQuote | None = None
    long_quote: PutQuote | None = None
    delivery_index_usd: float | None = None


@dataclass(frozen=True)
class Portfolio:
    initial_usd: float
    cash_usd: float
    reserved_usd: float
    scenario: str
    open_positions: tuple[tuple[str, Spread], ...]
    settled_ids: tuple[str, ...]
    last_event_ms: int
    events: tuple[LedgerEvent, ...] = ()

    def verify(self) -> None:
        if self.scenario not in COST_SCENARIOS:
            raise ValueError("UNKNOWN_COST_SCENARIO")
        if not all(isfinite(x) for x in (self.initial_usd, self.cash_usd, self.reserved_usd)):
            raise ValueError("NONFINITE_PORTFOLIO_LEDGER")
        if self.initial_usd <= 0 or self.reserved_usd < -1e-7:
            raise ValueError("INVALID_PORTFOLIO_CAPITAL")
        if self.cash_usd - self.reserved_usd < -1e-7:
            raise ValueError("DOUBLE_SPENT_PORTFOLIO_COLLATERAL")
        if self.reserved_usd > self.initial_usd * MAX_AGGREGATE_WIDTH_FRACTION + 1e-7:
            raise ValueError("AGGREGATE_WIDTH_LIMIT")
        if not TRAIN_START_MS <= self.last_event_ms < TRAIN_END_MS:
            raise ValueError("SEALED_PORTFOLIO_EVENT")
        ids = [name for name, _ in self.open_positions]
        if len(set(ids + list(self.settled_ids))) != len(ids) + len(self.settled_ids):
            raise ValueError("DUPLICATE_POSITION_ID")
        if not all(isinstance(name, str) and 0 < len(name) <= 128
                   for name in ids + list(self.settled_ids)):
            raise ValueError("INVALID_POSITION_ID")
        for _, spread in self.open_positions:
            spread.verify_open_invariants()
            if spread.scenario != self.scenario or spread.decision_ms > self.last_event_ms:
                raise ValueError("UNBOUND_PORTFOLIO_POSITION")
        expected = sum(s.collateral_reserved_usd for _, s in self.open_positions)
        if not isclose(self.reserved_usd, expected, rel_tol=1e-10, abs_tol=1e-7):
            raise ValueError("FORGED_PORTFOLIO_RESERVE")
        # A balanced but fabricated cash balance can pass a reserve-only check.
        # Reconstruct every opening premium and expiry debit from event inputs.
        # This is a model integrity witness, NOT original source authentication.
        cash, reserve, clock = self.initial_usd, 0.0, TRAIN_START_MS
        opened: dict[str, Spread] = {}
        settled: list[str] = []
        for event in self.events:
            if not isinstance(event, LedgerEvent) or event.time_ms < clock:
                raise ValueError("MISSING_OR_NONCHRONOLOGICAL_JOURNAL_EVENT")
            if event.kind == "open":
                spread = event.spread
                if (not isinstance(spread, Spread) or
                        not isinstance(event.short_quote, PutQuote) or
                        not isinstance(event.long_quote, PutQuote) or
                        event.delivery_index_usd is not None or
                        event.position_id in opened or event.position_id in settled or
                        any(x.expiry_ms <= event.time_ms for x in opened.values())):
                    raise ValueError("INVALID_JOURNALED_OPEN")
                if spread.decision_ms != event.time_ms or spread.scenario != self.scenario:
                    raise ValueError("JOURNAL_OPEN_SCENARIO_OR_CLOCK_MISMATCH")
                reproduced = open_vertical(
                    event.short_quote, event.long_quote, event.time_ms,
                    cash - reserve, self.scenario)
                if reproduced != spread:
                    raise ValueError("JOURNAL_OPEN_NOT_SELF_FINANCING")
                if reserve + spread.collateral_reserved_usd > (
                    self.initial_usd * MAX_AGGREGATE_WIDTH_FRACTION + 1e-7
                ):
                    raise ValueError("JOURNAL_AGGREGATE_COLLATERAL_EXCEEDED")
                cash += spread.premium_credit_usd
                reserve += spread.collateral_reserved_usd
                opened[event.position_id] = spread
            elif event.kind == "settle":
                spread = opened.get(event.position_id)
                if (spread is None or event.spread is not None or
                        event.short_quote is not None or event.long_quote is not None or
                        event.delivery_index_usd is None or
                        event.time_ms != spread.expiry_ms or
                        any(x.expiry_ms < event.time_ms for key, x in opened.items()
                            if key != event.position_id)):
                    raise ValueError("INVALID_JOURNALED_SETTLEMENT")
                debit = spread.expiry_nav(event.delivery_index_usd)["settlement_payoff_usd"]
                cash -= debit
                reserve -= spread.collateral_reserved_usd
                del opened[event.position_id]
                settled.append(event.position_id)
            else:
                raise ValueError("UNKNOWN_JOURNAL_EVENT")
            if cash - reserve < -1e-7:
                raise ValueError("JOURNAL_DOUBLE_SPENT_COLLATERAL")
            clock = event.time_ms
        if (tuple(opened.items()) != self.open_positions or
                tuple(settled) != self.settled_ids or clock != self.last_event_ms or
                not isclose(cash, self.cash_usd, rel_tol=1e-10, abs_tol=1e-7) or
                not isclose(reserve, self.reserved_usd, rel_tol=1e-10, abs_tol=1e-7)):
            raise ValueError("JOURNAL_CASH_RESERVE_OR_POSITION_MISMATCH")


def start_portfolio(initial_usd: float, scenario: str) -> Portfolio:
    if not isfinite(initial_usd) or initial_usd <= 0 or scenario not in COST_SCENARIOS:
        raise ValueError("INVALID_STARTING_PORTFOLIO")
    state = Portfolio(initial_usd, initial_usd, 0.0, scenario, (), (), TRAIN_START_MS)
    state.verify()
    return state


def open_position(state: Portfolio, position_id: str, spread: Spread,
                  short_quote: PutQuote, long_quote: PutQuote) -> Portfolio:
    state.verify()
    spread.verify_open_invariants()
    if not isinstance(position_id, str) or not 0 < len(position_id) <= 128:
        raise ValueError("INVALID_POSITION_ID")
    if position_id in state.settled_ids or any(i == position_id for i, _ in state.open_positions):
        raise ValueError("DUPLICATE_POSITION_ID")
    if spread.scenario != state.scenario or spread.decision_ms < state.last_event_ms:
        raise ValueError("WRONG_SCENARIO_OR_TIME_REVERSAL")
    if any(s.expiry_ms <= spread.decision_ms for _, s in state.open_positions):
        raise ValueError("UNSETTLED_EXPIRED_POSITION")
    free_cash = state.cash_usd - state.reserved_usd
    if not isclose(spread.initial_cash_usd, free_cash, rel_tol=1e-10, abs_tol=1e-7):
        raise ValueError("OPENING_SPREAD_NOT_FUNDED_BY_UNRESERVED_CASH")
    expected = open_vertical(short_quote, long_quote, spread.decision_ms,
                             free_cash, spread.scenario)
    if expected != spread:
        raise ValueError("OPENING_SPREAD_NOT_BOUND_TO_ORIGINAL_MODEL_QUOTES")
    if state.reserved_usd + spread.collateral_reserved_usd > (
        state.initial_usd * MAX_AGGREGATE_WIDTH_FRACTION + 1e-7
    ):
        raise ValueError("AGGREGATE_WIDTH_LIMIT")
    next_state = replace(
        state,
        cash_usd=state.cash_usd + spread.premium_credit_usd,
        reserved_usd=state.reserved_usd + spread.collateral_reserved_usd,
        open_positions=state.open_positions + ((position_id, spread),),
        last_event_ms=spread.decision_ms,
        events=state.events + (LedgerEvent('open', position_id, spread.decision_ms,
                                           spread, short_quote, long_quote),),
    )
    next_state.verify()
    return next_state


def settle_position(
    state: Portfolio, position_id: str, settlement_ms: int, delivery_index_usd: float
) -> Portfolio:
    state.verify()
    if not isfinite(delivery_index_usd) or delivery_index_usd <= 0:
        raise ValueError("INVALID_DELIVERY_INDEX")
    matches = [(i, s) for i, s in state.open_positions if i == position_id]
    if len(matches) != 1:
        raise ValueError("MISSING_OR_ALREADY_SETTLED_POSITION")
    spread = matches[0][1]
    if settlement_ms != spread.expiry_ms or settlement_ms < state.last_event_ms:
        raise ValueError("NONCHRONOLOGICAL_OR_NONCONTRACTUAL_SETTLEMENT")
    if any(s.expiry_ms < settlement_ms for i, s in state.open_positions if i != position_id):
        raise ValueError("UNSETTLED_EARLIER_EXPIRY")
    result = spread.expiry_nav(delivery_index_usd)
    obligation = result["settlement_payoff_usd"]
    next_state = replace(
        state,
        cash_usd=state.cash_usd - obligation,
        reserved_usd=state.reserved_usd - spread.collateral_reserved_usd,
        open_positions=tuple((i, s) for i, s in state.open_positions if i != position_id),
        settled_ids=state.settled_ids + (position_id,),
        last_event_ms=settlement_ms,
        events=state.events + (LedgerEvent('settle', position_id, settlement_ms,
                                           delivery_index_usd=delivery_index_usd),),
    )
    next_state.verify()
    return next_state


def source_only_status(state: Portfolio) -> dict:
    state.verify()
    return {
        "schema": "I1_MODELED_OVERLAPPING_CASH_RESERVE_ONLY_V1",
        "cash_balance_usd_not_nav": state.cash_usd,
        "reserved_width_usd_not_native_margin": state.reserved_usd,
        "free_cash_usd": state.cash_usd - state.reserved_usd,
        "open_positions": len(state.open_positions),
        "settled_positions": len(state.settled_ids),
        "unrealized_option_liability_known": False,
        "native_coin_margin_authenticated": False,
        "historical_fee_or_fill_authenticated": False,
        "economic_train_executed": False,
        "validation_opened": False,
        "holdout_opened": False,
        "promotion_authorized": False,
        "orders_enabled": False,
    }
