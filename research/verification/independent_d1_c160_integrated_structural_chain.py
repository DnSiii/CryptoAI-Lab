"""C160 independent full-TRAIN structural integration; NEVER economic provenance.

Connects C150 account replay, C133 funding calendar and C148 risk scorecard
on the SAME pair of scenario journals. Explicitly does not independently
re-execute C146 feature decisions or authenticate any historical OKX receipt.
No orders, validation, final holdout, ROI or promotion.
"""
from __future__ import annotations

from datetime import timedelta
from research.tools.v99_r106_d1_full_train_guard import START, HOURS
from research.verification.independent_d1_c150_cold_start_oracle import cold_start_oracle
from research.verification.independent_d1_full_train_schedule_gate_cycle133 import (
    verify_full_train_funding_closure,
)
from research.verification.independent_d1_c148_risk_fold_scorecard import (
    SCENARIOS, score_full_train_model_only,
)
from research.verification.independent_d1_c149_account_oracle import state


def verify_integrated_train_structural_only(journals, decisions_by_scenario,
                                          funding_schedule, initial_marks,
                                          initial_marks_time):
    """Fail closed on partial scenarios, inherited capital, bad funding or NAV.

    A synthetically populated account proof or C146 label is NOT provenance.
    This is a pre-economic wiring test, not a trading result.
    """
    if type(journals) is not dict or set(journals) != set(SCENARIOS):
        raise ValueError('C160_TWO_COST_PATHS_REQUIRED')
    if initial_marks_time != START - timedelta(hours=1):
        raise ValueError('C160_INITIAL_MARK_TIME')
    if not isinstance(initial_marks, dict) or set(initial_marks) != {'BTC', 'ETH'}:
        raise ValueError('C160_INITIAL_MARK_SCHEMA')

    # C148 alone uses scenario-1 initial NAV as the baseline for both paths.
    # A separately balanced, but larger scenario-2 initial cash balance
    # could otherwise look like model alpha. Enforce identical starting books.
    first_books = []
    for scenario in SCENARIOS:
        frames = journals[scenario].get('frames')
        if not isinstance(frames, list) or len(frames) != HOURS:
            raise ValueError('C160_COMPLETE_TRAIN_REQUIRED')
        if frames[0].get('time') != START:
            raise ValueError('C160_TRAIN_START_REQUIRED')
        first_books.append(state(frames[0]['before']))
    if first_books[0] != first_books[1]:
        raise ValueError('C160_SCENARIO_INITIAL_CAPITAL_MISMATCH')

    independent_accounts = {}
    independent_calendars = {}
    for scenario in SCENARIOS:
        journal = journals[scenario]
        independent_accounts[scenario] = cold_start_oracle(
            journal, initial_marks, initial_marks_time, scenario, full_train=True
        )
        independent_calendars[scenario] = verify_full_train_funding_closure(
            journal['frames'], funding_schedule
        )
        if (independent_accounts[scenario]['modeled_funding_events'] !=
                independent_calendars[scenario]['observed_funding_events']):
            raise ValueError('C160_FUNDING_ACCOUNT_CALENDAR_DISAGREE')
        if independent_accounts[scenario]['flat_warmup_hours_verified'] != 168:
            raise ValueError('C160_WARMUP_PROOF_MISSING')

    score = score_full_train_model_only(journals, decisions_by_scenario)
    if score['hours'] != HOURS or score['daily_decisions'] != 654:
        raise ValueError('C160_RISK_GRID_MISMATCH')
    return {
        'status': 'C160_INTEGRATED_STRUCTURAL_ONLY_DATA_ONLY_HOLD',
        'train_hours_per_scenario': HOURS,
        'chronological_folds': score['fold_hours'],
        'daily_decisions': score['daily_decisions'],
        'funding_events_per_scenario': independent_calendars[SCENARIOS[0]]['observed_funding_events'],
        'independent_account_hours_per_scenario': {
            s: independent_accounts[s]['hours'] for s in SCENARIOS
        },
        'independent_account_residuals': {
            s: independent_accounts[s]['max_accounting_residual'] for s in SCENARIOS
        },
        'risk_model_only': score,
        'initial_capital_identical_across_scenarios': True,
        'independent_c146_feature_reexecution': False,
        'first_party_okx_receipts_authenticated': False,
        'native_historical_fee_and_fills_authenticated': False,
        'historical_roi_authorized': False,
        'validation_opened': False,
        'holdout_opened': False,
        'promotion_authorized': False,
        'orders_enabled': False,
    }
