"""I1 source-grounded CASH attribution, not venue completeness or economic proof.

Ex-ante: V99_R106_I1_SOURCE_CASH_VETO_PROVENANCE_PREREG_20261029.md
"""
from __future__ import annotations

SCHEMA = "V99_I1_SOURCE_CASH_VETO_PROVENANCE_V1"
BOOK_SCHEMA = "V99_I1_SOURCE_DRIVEN_90W_ORIGINAL_ENTRY_BOOK_V1"
SCENARIOS = ("severe", "supersevere")
SIGNAL = "POSITIVE_EX_ANTE_PREMIUM"
BOOK_FALSE_FLAGS = (
    "original_underlying_index_authenticated", "original_native_lot_units_authenticated",
    "historical_fee_margin_delivery_authenticated", "original_execution_or_fills_certified",
    "economic_train_executed", "freeze_authorized", "promotion_authorized",
    "validation_opened", "holdout_opened", "orders_enabled",
    "paper_publication_authorized",
)
JOURNAL_FALSE_IF_PRESENT = (
    "promotion_authorized", "freeze_authorized", "validation_opened",
    "holdout_opened", "orders_enabled", "paper_publication_authorized",
    "original_options_economic_train_certified",
    "original_historical_economic_train_executed",
    "independent_original_trade_replay_verified",
)


def assess(book_report, journal):
    if (not isinstance(book_report, dict) or book_report.get("schema") != BOOK_SCHEMA
            or book_report.get("asset_week_decisions") != 180
            or book_report.get("source_sundays_scanned") != 90
            or any(book_report.get(k) is not False for k in BOOK_FALSE_FLAGS)):
        raise ValueError("UNTRUSTED_SOURCE_BOOK_ATTESTATION")
    rows = book_report.get("rows")
    ledgers = journal.get("scenario_decisions") if isinstance(journal, dict) else None
    if (not isinstance(rows, list) or len(rows) != 180
            or not isinstance(ledgers, dict) or set(ledgers) != set(SCENARIOS)):
        raise ValueError("SOURCE_VETO_180_GRID_REQUIRED")
    if (journal.get("fixture") is not False or
            any(k in journal and journal[k] is not False
                for k in JOURNAL_FALSE_IF_PRESENT)):
        raise ValueError("SOURCE_VETO_CERTIFICATION_FORBIDDEN")
    results = {}
    for scenario in SCENARIOS:
        decisions = ledgers[scenario]
        if not isinstance(decisions, list) or len(decisions) != 180:
            raise ValueError("SOURCE_VETO_180_GRID_REQUIRED")
        counts = dict(observed_empty_tenor_cash=0, positive_cash_unverified=0,
                      positive_opens_with_observed_book=0, negative_signal_cash=0)
        for book, decision in zip(rows, decisions):
            if not isinstance(book, dict) or not isinstance(decision, dict):
                raise ValueError("SOURCE_VETO_INVALID_ROW")
            if any(book.get(k) != decision.get(k)
                   for k in ("decision_ms", "asset", "fold", "signal")):
                raise ValueError("SOURCE_VETO_INTENT_BOOK_MISMATCH")
            observed = book.get("original_books")
            if not isinstance(observed, list):
                raise ValueError("SOURCE_VETO_INVALID_ORIGINAL_BOOK")
            action, reason = decision.get("action"), decision.get("reason")
            positive = book["signal"] == SIGNAL
            if positive and action == "OPEN":
                if reason != "FIXED_VERTICAL" or not observed:
                    raise ValueError("SOURCE_VETO_OPEN_WITHOUT_ORIGINAL_TENOR_BOOK")
                counts["positive_opens_with_observed_book"] += 1
            elif positive and action == "CASH":
                if reason not in ("RISK_VETO", "NO_ELIGIBLE_FIXED_VERTICAL"):
                    raise ValueError("SOURCE_VETO_INVALID_POSITIVE_CASH_REASON")
                if not observed:
                    if reason != "NO_ELIGIBLE_FIXED_VERTICAL":
                        raise ValueError("SOURCE_VETO_RISK_CLAIM_WITHOUT_TENOR_BOOK")
                    counts["observed_empty_tenor_cash"] += 1
                else:
                    # Moneyness, risk and venue completeness remain unverified.
                    counts["positive_cash_unverified"] += 1
            elif not positive and action == "CASH" and reason == book["signal"]:
                counts["negative_signal_cash"] += 1
            else:
                raise ValueError("SOURCE_VETO_DECISION_CONTRADICTS_CAUSAL_SIGNAL")
        if sum(counts.values()) != 180:
            raise ValueError("SOURCE_VETO_INCOMPLETE_ACCOUNTING")
        results[scenario] = counts
    return {"schema": SCHEMA,
            "status": "SOURCE_ONLY_CONDITIONAL_EMPTY_BOOK_NOT_VENUE_CERTIFIED",
            "scenarios": results,
            "original_archive_completeness_certified": False,
            "underlying_index_lot_fee_margin_certified": False,
            "positive_cash_veto_economically_certified": False,
            "original_options_economic_train_certified": False,
            "freeze_authorized": False, "promotion_authorized": False,
            "validation_opened": False, "holdout_opened": False,
            "orders_enabled": False, "paper_publication_authorized": False}
