"""C167: independently bind preregistered D1 C136 decisions to C140/C165 account journals.

Recompute the EXACT ex-ante fee veto from 168 prior hourly opens, three
already-settled funding fixes, and the tier known by t-1. This closes a
source-only loophole where internally consistent journals could contain
arbitrary caller-supplied (including posthoc cash-only) decisions.

This is an adversarial MODEL-ONLY proof. 'OKX' strings are not receipts;
historical TRAIN economics, validation, holdout, orders and promotion CLOSED.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from research.tools.v99_r106_d1_basis_carry_preregistered import (
    ASSETS, Decision, FeeEvidence, FundingFix, PairedBar,
)
from research.tools.v99_r106_d1_native_fee_veto_cycle136 import (
    CausalFeeTier, fee_bound_intent,
)
from research.verification.independent_d1_c165_two_cost_path_bridge import (
    SCENARIOS, WARMUP, verify_two_cost_path_bridge,
)


def _num(x):
    try:
        v = Decimal(str(x))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("C167_BAD_NUMBER") from exc
    if not v.is_finite():
        raise ValueError("C167_NONFINITE_NUMBER")
    return v


def verify_c167_preregistered_account_binding(
    *, journals, decisions_by_scenario, evidence_by_decision,
    native_fee_schedule, initial_marks, initial_marks_time, expected_hours=216,
):
    """Recompute all source decisions, then independently replay BOTH accounts.

    Evidence must be supplied separately from the journals, but source identity
    is checked only structurally. This does NOT authenticate the original venue.
    """
    if (type(journals) is not dict or set(journals) != set(SCENARIOS)
            or type(decisions_by_scenario) is not dict
            or set(decisions_by_scenario) != set(SCENARIOS)
            or type(evidence_by_decision) is not dict
            or type(native_fee_schedule) is not dict
            or set(native_fee_schedule) != set(ASSETS)
            or type(expected_hours) is not int or expected_hours < WARMUP + 24):
        raise ValueError("C167_COMPLETE_TWO_SCENARIO_INPUT_REQUIRED")
    frames = journals[SCENARIOS[0]].get("frames")
    if type(frames) is not list or len(frames) != expected_hours:
        raise ValueError("C167_INCOMPLETE_JOURNAL")
    start = frames[0].get("time")
    if (type(start) is not datetime or start.tzinfo is not timezone.utc
            or start.hour or start.minute or start.second or start.microsecond):
        raise ValueError("C167_CANONICAL_MIDNIGHT_START_REQUIRED")
    expected_times = tuple(start + timedelta(hours=i)
                           for i in range(WARMUP, expected_hours, 24))
    if (set(evidence_by_decision) != set(expected_times)
            or any(set(decisions_by_scenario[s]) != set(expected_times)
                   for s in SCENARIOS)):
        raise ValueError("C167_EXACT_DAILY_DECISION_GRID_REQUIRED")

    previous_funding = {a: [] for a in ASSETS}
    bar_pairs = funding_fixes = exact_decisions = 0
    positive_pairs = {s: 0 for s in SCENARIOS}
    for i, frame in enumerate(frames):
        t = start + timedelta(hours=i)
        if frame.get("time") != t:
            raise ValueError("C167_NONCONTIGUOUS_HOURLY_JOURNAL")
        if t in evidence_by_decision:
            ev = evidence_by_decision[t]
            if (type(ev) is not dict or set(ev) != {"bars", "funding", "fee_tiers"}
                    or any(type(ev.get(k)) is not dict
                           or set(ev[k]) != set(ASSETS)
                           for k in ("bars", "funding", "fee_tiers"))):
                raise ValueError("C167_INCOMPLETE_INDEPENDENT_EVIDENCE")
            for asset in ASSETS:
                history = ev["bars"][asset]
                if type(history) not in (list, tuple) or len(history) != WARMUP:
                    raise ValueError("C167_EXACT_168H_FEATURE_WINDOW_REQUIRED")
                for j, bar in enumerate(history):
                    original = frames[i - WARMUP + j]
                    if (type(bar) is not PairedBar or bar.asset != asset
                            or bar.time != original["time"]
                            or bar.observed_at != original["time"]
                            or bar.source_spot != "OKX" or bar.source_perp != "OKX"
                            or _num(bar.spot_open) != _num(original["marks"][asset]["spot"])
                            or _num(bar.perp_open) != _num(original["marks"][asset]["perp"])):
                        raise ValueError("C167_FEATURE_MARK_IDENTITY_MISMATCH")
                    bar_pairs += 1
                known = ev["funding"][asset]
                actual = previous_funding[asset][-3:]
                if (type(known) not in (tuple, list) or len(known) != 3
                        or len(actual) != 3):
                    raise ValueError("C167_EXACT_THREE_SETTLED_FIXES_REQUIRED")
                for fix, raw in zip(known, actual):
                    if (type(fix) is not FundingFix or fix.asset != asset
                            or fix.instrument != asset + "-USDT-SWAP"
                            or fix.source != "OKX" or fix.announced_at > t-timedelta(hours=1)
                            or fix.settled_at != raw["time"]
                            or _num(fix.rate) != _num(raw["rate"])):
                        raise ValueError("C167_FUNDING_FIX_IDENTITY_MISMATCH")
                    funding_fixes += 1
                tier = ev["fee_tiers"][asset]
                schedule = native_fee_schedule[asset]
                if type(tier) is not CausalFeeTier or type(schedule) not in (list, tuple):
                    raise ValueError("C167_CAUSAL_NATIVE_TIER_REQUIRED")
                candidates = [x for x in schedule
                              if x["start"] <= t-timedelta(hours=1) < x["end"]
                              and x["observed_at"] <= t-timedelta(hours=1)]
                if len(candidates) != 1:
                    raise ValueError("C167_NO_UNAMBIGUOUS_ASOF_TIER")
                row = candidates[0]
                fee = tier.evidence
                if (type(fee) is not FeeEvidence
                        or tier.observed_at != row["observed_at"]
                        or fee.valid_from != row["start"] or fee.valid_until != row["end"]
                        or _num(fee.spot_taker) != _num(row["spot_taker"])
                        or _num(fee.perp_taker) != _num(row["perp_taker"])):
                    raise ValueError("C167_NATIVE_TIER_JOURNAL_MISMATCH")
            for scenario in SCENARIOS:
                calculated = fee_bound_intent(
                    time=t, bars=ev["bars"], funding=ev["funding"],
                    scenario=scenario, fee_tiers=ev["fee_tiers"],
                )["decision"]
                declared = decisions_by_scenario[scenario][t]
                if type(declared) is not Decision or declared != calculated:
                    raise ValueError("C167_POSTHOC_OR_INCORRECT_PREREG_DECISION")
                exact_decisions += 1
                positive_pairs[scenario] += sum(
                    getattr(calculated, a.lower() + "_pair_weight") > 0
                    for a in ASSETS
                )
        for fix in frame.get("funding", ()):
            if (fix.get("asset") not in ASSETS or fix.get("time") != t
                    or fix.get("source") != "OKX"
                    or fix.get("instrument") != fix["asset"] + "-USDT-SWAP"):
                raise ValueError("C167_INVALID_HOURLY_FUNDING")
            previous_funding[fix["asset"]].append(fix)

    replay = verify_two_cost_path_bridge(
        journals=journals, decisions_by_scenario=decisions_by_scenario,
        initial_marks=initial_marks, initial_marks_time=initial_marks_time,
        expected_hours=expected_hours,
    )
    return {
        "status": "C167_EXACT_PREREG_DECISION_TO_ACCOUNT_SOURCE_ONLY_HOLD",
        "hours_per_scenario": expected_hours,
        "daily_decision_hours": len(expected_times),
        "scenario_decisions_recomputed": exact_decisions,
        "feature_asset_hours_verified": bar_pairs,
        "historical_funding_fix_identities_verified": funding_fixes,
        "positive_pair_decisions_by_scenario_synthetic": positive_pairs,
        "independent_c165_account_replay": replay,
        "original_first_party_receipts_authenticated": False,
        "historical_economics_authorized": False,
        "validation_opened": False,
        "holdout_opened": False,
        "promotion_authorized": False,
        "orders_enabled": False,
    }
