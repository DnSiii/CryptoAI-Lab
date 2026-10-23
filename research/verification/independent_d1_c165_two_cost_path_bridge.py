"""C165 independent two-cost-path C140 -> C150 model-ledger integration.

Synthetic/pre-economic ONLY. Enforces a flat 168h warmup, same exogenous
market/funding history and starting capital, exact t-1 decisions, and an
independent C149/C150 cash/fill/funding replay for BOTH cost scenarios.
A caller's 'OKX' label is not an exchange receipt. Never grants ROI rights.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from research.tools.v99_r106_d1_basis_carry_preregistered import Decision
from research.tools.v99_r106_d1_full_train_guard import START, END
from research.verification.independent_d1_c150_cold_start_oracle import cold_start_oracle
from research.verification.independent_d1_c149_account_oracle import state

SCENARIOS = ("severe_model_only", "supersevere_model_only")
ASSETS = ("BTC", "ETH")
WARMUP = 168
REGIMES = frozenset(
    direction + "__" + vol
    for direction in ("BULL", "BEAR", "SIDEWAYS")
    for vol in ("HIGH_VOLATILITY", "LOW_VOLATILITY")
)


def verify_two_cost_path_bridge(*, journals, decisions_by_scenario,
                                initial_marks, initial_marks_time,
                                expected_hours=216):
    """Re-execute both accounts independently; reject silent cross-path drift.

    This small preflight is NOT a substitute for full 15,864h TRAIN, 5 folds,
    actual historical native execution, first-party funding or lot receipts.
    """
    if (type(expected_hours) is not int or expected_hours < WARMUP + 24
            or type(journals) is not dict or set(journals) != set(SCENARIOS)
            or type(decisions_by_scenario) is not dict
            or set(decisions_by_scenario) != set(SCENARIOS)):
        raise ValueError("C165_TWO_COST_PATHS_AND_WARMUP_REQUIRED")
    if (type(initial_marks_time) is not datetime
            or initial_marks_time.tzinfo is not timezone.utc
            or initial_marks_time.minute or initial_marks_time.second
            or initial_marks_time.microsecond
            or type(initial_marks) is not dict
            or set(initial_marks) != set(ASSETS)):
        raise ValueError("C165_BAD_INITIAL_MARKS")
    baseline_frames = journals[SCENARIOS[0]].get("frames")
    if type(baseline_frames) is not list or len(baseline_frames) != expected_hours:
        raise ValueError("C165_INCOMPLETE_BRIDGE")
    first_time = initial_marks_time + timedelta(hours=1)
    if (first_time < START or first_time + timedelta(hours=expected_hours) > END
            or baseline_frames[0].get("time") != first_time):
        raise ValueError("C165_SEALED_OR_SHIFTED_WINDOW")
    initial_books = []
    results = {}
    reference_decisions = decisions_by_scenario[SCENARIOS[0]]
    if type(reference_decisions) is not dict:
        raise ValueError("C165_DECISION_MAP_REQUIRED")
    for scenario in SCENARIOS:
        journal = journals[scenario]
        frames = journal.get("frames")
        if type(frames) is not list or len(frames) != expected_hours:
            raise ValueError("C165_INCOMPLETE_SCENARIO")
        if journal.get("status") != "C140_MODEL_ONLY_ACCOUNTING_NOT_ECONOMICS":
            raise ValueError("C165_ORIGINAL_JOURNAL_REQUIRED")
        if any(journal.get(flag) is not False for flag in (
                "economic_roi_authorized", "first_party_receipts_authenticated",
                "validation_opened", "holdout_opened", "promotion_authorized",
                "orders_enabled")):
            raise ValueError("C165_FALSE_ECONOMIC_PERMISSION")
        initial_books.append(state(frames[0]["before"]))
        decisions = decisions_by_scenario[scenario]
        if type(decisions) is not dict or set(decisions) != set(reference_decisions):
            raise ValueError("C165_DECISION_GRID_MISMATCH")
        for t, decision in decisions.items():
            ref = reference_decisions[t]
            if (type(t) is not datetime or t.tzinfo is not timezone.utc
                    or t.hour != 0 or t.minute or t.second or t.microsecond
                    or not first_time + timedelta(hours=WARMUP) <= t
                    < first_time + timedelta(hours=expected_hours)
                    or not isinstance(decision, Decision)
                    or not isinstance(ref, Decision)
                    or decision.time != t or ref.time != t
                    or decision.regime not in REGIMES or decision.regime != ref.regime
                    or decision.feature_max_time > t - timedelta(hours=1)
                    or decision.funding_asof > t - timedelta(hours=1)
                    or decision.status != "C136_FEE_VETO_MODEL_ONLY_NO_ROI"):
                raise ValueError("C165_NONCAUSAL_OR_UNREGISTERED_DECISION")
        for index, frame in enumerate(frames):
            ref_frame = baseline_frames[index]
            t = first_time + timedelta(hours=index)
            if frame.get("time") != t or ref_frame.get("time") != t:
                raise ValueError("C165_HOURLY_GAP")
            if (frame.get("marks") != ref_frame.get("marks")
                    or frame.get("funding") != ref_frame.get("funding")):
                raise ValueError("C165_EXOGENOUS_HISTORY_DIVERGENCE")
            if index < WARMUP and frame.get("fills"):
                raise ValueError("C165_PREDECISION_FILL")
            if (t in decisions) != bool(frame.get("fills")):
                # A legitimate decision can stay in cash with zero fills;
                # only reject unexplained fills, not cash-only decisions.
                if t not in decisions and frame.get("fills"):
                    raise ValueError("C165_FILL_WITHOUT_DECISION")
        proof = cold_start_oracle(
            journal, initial_marks, initial_marks_time, scenario, full_train=False
        )
        if proof["hours"] != expected_hours or proof["flat_warmup_hours_verified"] != WARMUP:
            raise ValueError("C165_INDEPENDENT_REPLAY_INCOMPLETE")
        results[scenario] = {
            "hours_independently_replayed": proof["hours"],
            "modeled_fills": proof["modeled_fills"],
            "modeled_funding_events": proof["modeled_funding_events"],
            "max_accounting_residual": proof["max_accounting_residual"],
        }
    if initial_books[0] != initial_books[1]:
        raise ValueError("C165_SCENARIO_INITIAL_CAPITAL_MISMATCH")
    return {
        "status": "C165_SYNTHETIC_INDEPENDENT_BRIDGE_DATA_ONLY_HOLD",
        "hours_per_scenario": expected_hours,
        "warmup_hours": WARMUP,
        "decision_hours": len(reference_decisions),
        "scenario_results": results,
        "initial_capital_identical": True,
        "exogenous_market_and_funding_identical": True,
        "first_party_okx_authenticated": False,
        "native_lot_and_fee_tier_authenticated": False,
        "settled_funding_and_fills_authenticated": False,
        "historical_economics_authorized": False,
        "validation_opened": False,
        "holdout_opened": False,
        "promotion_authorized": False,
        "orders_enabled": False,
    }
