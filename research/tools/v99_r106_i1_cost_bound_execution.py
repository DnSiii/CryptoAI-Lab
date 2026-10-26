"""V99 I1 fixed severe/supersevere native-coin cost-bound wallet entry/mark.

Research-only adapter, never a certified historical execution or trading system.
Preregistered before code: research/V99_R106_I1_SCENARIO_COST_BINDING_PREREG_20261026.md
"""
from __future__ import annotations

from decimal import Decimal
from research.tools.v99_r106_i1_native_coin_account_replay import (
    D, Wallet, Quote, open_vertical, mark_to_exit, account_nav,
)

# Fixed *modeled* rates per leg, matching the older USD-equivalent stress ledger.
# They are NOT original Deribit fee-tier evidence.
RATES = {
    "severe": (Decimal("0.0012"), Decimal("0.0012")),
    "supersevere": (Decimal("0.0024"), Decimal("0.0024")),
}


def charge_floor(scenario: str, native_lots):
    if scenario not in RATES:
        raise ValueError("UNKNOWN_COST_SCENARIO")
    q = D(native_lots)
    if q <= 0:
        raise ValueError("NONPOSITIVE_NATIVE_LOTS")
    fee, slip = RATES[scenario]
    return 2 * q * fee, 2 * q * slip


def verify_charges(scenario, native_lots, fee_coin, slip_coin):
    floor_fee, floor_slip = charge_floor(scenario, native_lots)
    fee, slip = D(fee_coin), D(slip_coin)
    if fee < floor_fee or slip < floor_slip:
        raise ValueError("SEVERE_SUPERSEVERE_FRICTION_UNDERPAYMENT")
    return {"fee_coin": str(fee), "slippage_coin": str(slip),
            "modeled_fee_floor_coin": str(floor_fee),
            "modeled_slippage_floor_coin": str(floor_slip),
            "historical_native_fee_certified": False,
            "economic_train_executed": False, "promotion_authorized": False}


def _source_gate(*, fixture, original_fee_verified, native_contract_verified,
                 margin_rules_verified, original_quote_verified):
    # The booleans are only upstream interface claims, not independent proof.
    # A real execution runner must separately authenticate the actual receipts.
    if type(fixture) is not bool or any(type(x) is not bool for x in (
        original_fee_verified, native_contract_verified,
        margin_rules_verified, original_quote_verified
    )):
        raise ValueError("UNTRUSTED_SOURCE_GATE_FLAGS")
    if fixture:
        if any((original_fee_verified, native_contract_verified,
                margin_rules_verified, original_quote_verified)):
            raise ValueError("FIXTURE_CANNOT_CLAIM_AUTHENTICATED_PROVENANCE")
        return
    # Deliberately fail closed: no original historical fee/margin/quote archive
    # currently exists. Never accept caller-supplied booleans as certification.
    raise ValueError("HISTORICAL_SOURCE_RECEIPTS_REQUIRE_INDEPENDENT_ATTESTATION")


def costed_open(w: Wallet, name: str, short: Quote, long: Quote, at_ms: int,
                native_lots, entry_fees_coin, entry_slippage_coin,
                initial_margin_coin, maintenance_margin_coin, *,
                fixture=False, original_fee_verified=False,
                native_contract_verified=False, margin_rules_verified=False,
                original_quote_verified=False):
    _source_gate(fixture=fixture, original_fee_verified=original_fee_verified,
                 native_contract_verified=native_contract_verified,
                 margin_rules_verified=margin_rules_verified,
                 original_quote_verified=original_quote_verified)
    verify_charges(w.scenario, native_lots, entry_fees_coin, entry_slippage_coin)
    proposed = open_vertical(w, name, short, long, at_ms, native_lots,
                            entry_fees_coin, entry_slippage_coin,
                            initial_margin_coin, maintenance_margin_coin)
    # The wallet's weak post-entry check intentionally omits closing costs.
    # Enforce the actual severe/supersevere modeled exit-cost FLOOR here,
    # before a research caller can mistake the position for collateral-safe.
    exit_fee_floor, exit_slip_floor = charge_floor(w.scenario, native_lots)
    immediate_exit = max(
        D(0), D(native_lots) * (D(short.ask_coin) - D(long.bid_coin))
    ) + exit_fee_floor + exit_slip_floor
    other_exit = sum((D(m[1]) for m in w.marks), D(0))
    maintenance = sum((D(p.maintenance_margin_coin)
                       for p in proposed.positions), D(0))
    if D(proposed.cash_coin) - other_exit - immediate_exit < maintenance:
        raise ValueError("POSTENTRY_SCENARIO_COST_MAINTENANCE_VETO")
    return proposed


def costed_mark(w: Wallet, name: str, short: Quote, long: Quote, at_ms: int,
                exit_fees_coin, exit_slippage_coin, *,
                fixture=False, original_fee_verified=False,
                native_contract_verified=False, margin_rules_verified=False,
                original_quote_verified=False):
    _source_gate(fixture=fixture, original_fee_verified=original_fee_verified,
                 native_contract_verified=native_contract_verified,
                 margin_rules_verified=margin_rules_verified,
                 original_quote_verified=original_quote_verified)
    p = next((p for p in w.positions if p.name == name), None)
    if p is None:
        raise ValueError("UNKNOWN_POSITION")
    verify_charges(w.scenario, p.qty, exit_fees_coin, exit_slippage_coin)
    marked = mark_to_exit(w, name, short, long, at_ms,
                          exit_fees_coin, exit_slippage_coin)
    # A complete same-clock mark set is not valid if its NAV violates
    # maintenance. Incomplete marks are never promoted to NAV.
    if (len(marked.marks) == len(marked.positions)
            and all(t == at_ms for _, _, t, _ in marked.marks)):
        account_nav(marked, at_ms)
    return marked
