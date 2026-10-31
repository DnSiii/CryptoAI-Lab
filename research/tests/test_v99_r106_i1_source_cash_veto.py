"""Synthetic-only source CASH attribution negative controls; never trading PnL."""
import copy
import unittest

from research.tools.v99_r106_i1_source_cash_veto import assess
from research.verification.independent_v99_r106_i1_source_cash_veto import verify


def sample():
    rows = []
    decisions = []
    for i in range(180):
        signal = "POSITIVE_EX_ANTE_PREMIUM" if i < 3 else "NO_PREMIUM"
        book = ([{"symbol": "BTC-14JAN22-36000-P"}] if i in (1, 2) else [])
        row = {"decision_ms": 1000 + i, "asset": "BTC" if i % 2 == 0 else "ETH",
               "fold": 1 + i // 36, "signal": signal, "original_books": book}
        rows.append(row)
        decisions.append({k: row[k] for k in ("decision_ms", "asset", "fold", "signal")} |
                         {"action": "CASH", "reason":
                          ("NO_ELIGIBLE_FIXED_VERTICAL" if i == 0 else
                           "RISK_VETO" if i in (1, 2) else "NO_PREMIUM")})
    books = {"schema": "V99_I1_SOURCE_DRIVEN_90W_ORIGINAL_ENTRY_BOOK_V1",
             "asset_week_decisions": 180, "source_sundays_scanned": 90,
             "original_underlying_index_authenticated": False,
             "original_native_lot_units_authenticated": False,
             "historical_fee_margin_delivery_authenticated": False,
             "original_execution_or_fills_certified": False,
             "economic_train_executed": False, "freeze_authorized": False,
             "promotion_authorized": False, "validation_opened": False,
             "holdout_opened": False, "orders_enabled": False,
             "paper_publication_authorized": False,
             "rows": rows}
    journal = {"fixture": False,
               "scenario_decisions": {"severe": copy.deepcopy(decisions),
                                      "supersevere": copy.deepcopy(decisions)}}
    return books, journal


class SourceCashVetoTest(unittest.TestCase):
    def test_independent_full_grid_and_unverified_veto(self):
        books, journal = sample()
        report = assess(books, journal)
        self.assertTrue(verify(books, journal, report)["independent_180_intents_per_scenario"])
        for scenario in ("severe", "supersevere"):
            self.assertEqual(report["scenarios"][scenario]["observed_empty_tenor_cash"], 1)
            self.assertEqual(report["scenarios"][scenario]["positive_cash_unverified"], 2)
            self.assertEqual(report["scenarios"][scenario]["negative_signal_cash"], 177)
        self.assertFalse(report["promotion_authorized"])

    def test_each_forged_book_certification_fails_primary_and_oracle(self):
        unsafe = (
            "original_underlying_index_authenticated", "original_native_lot_units_authenticated",
            "historical_fee_margin_delivery_authenticated", "original_execution_or_fills_certified",
            "economic_train_executed", "freeze_authorized", "promotion_authorized",
            "validation_opened", "holdout_opened", "orders_enabled",
            "paper_publication_authorized",
        )
        for key in unsafe:
            with self.subTest(key=key):
                books, journal = sample()
                valid = assess(books, journal)
                books[key] = True
                with self.assertRaisesRegex(ValueError, "UNTRUSTED_SOURCE_BOOK_ATTESTATION"):
                    assess(books, journal)
                with self.assertRaisesRegex(AssertionError, "ORACLE_SOURCE_VETO_UNSAFE_INPUT_CERTIFICATION"):
                    verify(books, journal, valid)

    def test_missing_or_nonboolean_book_attestation_fails(self):
        for value in (None, 1, "false"):
            with self.subTest(value=value):
                books, journal = sample()
                books["orders_enabled"] = value
                with self.assertRaisesRegex(ValueError, "UNTRUSTED_SOURCE_BOOK_ATTESTATION"):
                    assess(books, journal)

    def test_each_forged_journal_permission_fails_primary_and_oracle(self):
        unsafe = (
            "promotion_authorized", "freeze_authorized", "validation_opened",
            "holdout_opened", "orders_enabled", "paper_publication_authorized",
            "original_options_economic_train_certified",
            "original_historical_economic_train_executed",
            "independent_original_trade_replay_verified",
        )
        for key in unsafe:
            with self.subTest(key=key):
                books, journal = sample()
                valid = assess(books, journal)
                journal[key] = True
                with self.assertRaisesRegex(ValueError, "SOURCE_VETO_CERTIFICATION_FORBIDDEN"):
                    assess(books, journal)
                with self.assertRaisesRegex(AssertionError, "ORACLE_SOURCE_VETO_UNSAFE_INPUT_CERTIFICATION"):
                    verify(books, journal, valid)

    def test_open_without_observed_book_fails(self):
        books, journal = sample()
        for scenario in ("severe", "supersevere"):
            journal["scenario_decisions"][scenario][0].update(action="OPEN", reason="FIXED_VERTICAL")
        with self.assertRaisesRegex(ValueError, "SOURCE_VETO_OPEN_WITHOUT_ORIGINAL_TENOR_BOOK"):
            assess(books, journal)

    def test_risk_veto_without_book_fails(self):
        books, journal = sample()
        journal["scenario_decisions"]["severe"][0]["reason"] = "RISK_VETO"
        with self.assertRaisesRegex(ValueError, "SOURCE_VETO_RISK_CLAIM_WITHOUT_TENOR_BOOK"):
            assess(books, journal)

    def test_book_and_signal_mismatch_fails(self):
        books, journal = sample()
        books["rows"][0]["decision_ms"] += 1
        with self.assertRaisesRegex(ValueError, "SOURCE_VETO_INTENT_BOOK_MISMATCH"):
            assess(books, journal)

    def test_forged_classification_rejected_by_oracle(self):
        books, journal = sample()
        report = assess(books, journal)
        report["scenarios"]["severe"]["positive_cash_unverified"] = 0
        with self.assertRaisesRegex(AssertionError, "ORACLE_SOURCE_VETO_CLASSIFICATION_MISMATCH"):
            verify(books, journal, report)

    def test_forged_certification_rejected_by_oracle(self):
        books, journal = sample()
        report = assess(books, journal)
        report["original_options_economic_train_certified"] = True
        with self.assertRaisesRegex(AssertionError, "ORACLE_SOURCE_VETO_FORGED_CERTIFICATION"):
            verify(books, journal, report)

    def test_valid_open_requires_book_but_does_not_certify(self):
        books, journal = sample()
        for scenario in ("severe", "supersevere"):
            journal["scenario_decisions"][scenario][2].update(action="OPEN", reason="FIXED_VERTICAL")
        report = assess(books, journal)
        self.assertEqual(report["scenarios"]["severe"]["positive_opens_with_observed_book"], 1)
        self.assertFalse(report["underlying_index_lot_fee_margin_certified"])
        verify(books, journal, report)


if __name__ == "__main__":
    unittest.main()
