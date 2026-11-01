"""Synthetic/adversarial tests only. No licensed options, PnL or orders."""
import copy
import tempfile
import unittest

from research.tools.v99_r106_i1_dated_native_fee_preflight import (
    calculate_minimum_fee, parse_schedule, signed_fee_preflight,
)
from research.verification.independent_v99_r106_i1_dated_native_fee_oracle import verify

FIRST = 1639008000000
END = 1696118400000


def schedule():
    return {
        "schema": "V99_I1_HISTORICAL_NATIVE_OPTION_FEE_SCHEDULE_V1",
        "fixture": False,  # Adversarial synthetic impersonation; NOT original data.
        "venue": "deribit", "account_tier": "synthetic-test-only",
        "account_tier_original_document_sha256": "a" * 64,
        "rows": [
            {"asset": asset, "effective_from_ms": FIRST,
             "effective_to_ms": END, "account_tier": "synthetic-test-only",
             "entry_per_lot_coin": "0.0003",
             "delivery_per_lot_coin": "0.00015",
             "cap_fraction": "0.125", "native_lot_quantity": "1"}
            for asset in ("BTC", "ETH")
        ],
    }


class DatedNativeFeePreflightTests(unittest.TestCase):
    def test_two_leg_entry_cap_independent_oracle(self):
        doc = schedule()
        inputs = dict(event_type="OPEN", asset="BTC", at_ms=FIRST+1000,
                      native_lots="2", premiums_coin=["0.001", "0.05"])
        result = calculate_minimum_fee(doc, **inputs)
        self.assertEqual(result["native_fee_minimum_coin"], "0.000850")
        self.assertEqual(result["leg_native_fee_coin"], ["0.000250", "0.0006"])
        self.assertTrue(verify(doc, result, **inputs)["independent_native_fee_arithmetic_verified"])
        self.assertFalse(result["historical_native_fee_certified"])

    def test_two_leg_delivery_intrinsic_independent_oracle(self):
        doc = schedule()
        inputs = dict(event_type="SETTLE_BATCH", asset="ETH", at_ms=FIRST+1000,
                      native_lots="1", strikes_usd=["30000", "25000"],
                      delivery_index_usd="28000")
        result = calculate_minimum_fee(doc, **inputs)
        self.assertEqual(result["native_fee_minimum_coin"], "0.00015")
        self.assertEqual(result["leg_native_fee_coin"], ["0.00015", "0.000"])
        verify(doc, result, **inputs)

    def test_overlap_rejected(self):
        doc = schedule()
        row = copy.deepcopy(doc["rows"][0])
        row["effective_from_ms"] = FIRST + 10
        doc["rows"].append(row)
        with self.assertRaisesRegex(ValueError, "OVERLAPPING_HISTORICAL"):
            parse_schedule(doc)

    def test_gap_rejected(self):
        doc = schedule()
        doc["rows"][0]["effective_to_ms"] = FIRST + 10
        with self.assertRaisesRegex(ValueError, "MISSING_OR_AMBIGUOUS"):
            calculate_minimum_fee(doc, event_type="OPEN", asset="BTC",
                                  at_ms=FIRST+1000, native_lots="1",
                                  premiums_coin=["0.02", "0.01"])

    def test_forged_account_tier_rejected(self):
        doc = schedule()
        doc["rows"][0]["account_tier"] = "VIP10"
        with self.assertRaisesRegex(ValueError, "INVALID_DATED_NATIVE_FEE_INTERVAL"):
            parse_schedule(doc)

    def test_fractional_lot_rejected(self):
        with self.assertRaisesRegex(ValueError, "HISTORICAL_NATIVE_LOT_INCREMENT"):
            calculate_minimum_fee(schedule(), event_type="OPEN", asset="BTC",
                                  at_ms=FIRST+1000, native_lots="0.5",
                                  premiums_coin=["0.02", "0.01"])

    def test_fee_cap_and_source_price_validation(self):
        doc = schedule()
        doc["rows"][0]["cap_fraction"] = "1.5"
        with self.assertRaisesRegex(ValueError, "INVALID_NATIVE_FEE_CAP"):
            parse_schedule(doc)
        doc = schedule()
        with self.assertRaisesRegex(ValueError, "INVALID_NATIVE_FEE_NUMBER"):
            calculate_minimum_fee(doc, event_type="OPEN", asset="BTC",
                                  at_ms=FIRST+1000, native_lots="1",
                                  premiums_coin=["-0.1", "0.01"])

    def test_missing_signature_cannot_claim_fee_proof(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "MISSING_INDEPENDENT_AUDITOR_TRUST_ANCHOR"):
                signed_fee_preflight(root, "a"*64, "b"*64, event_type="OPEN",
                                     asset="BTC", at_ms=FIRST+1000, native_lots="1",
                                     scenario="severe", fee_coin="0.005",
                                     slippage_coin="0.005",
                                     premiums_coin=["0.02", "0.01"])

    def test_independent_oracle_detects_forged_fee(self):
        doc = schedule()
        inputs = dict(event_type="OPEN", asset="BTC", at_ms=FIRST+1000,
                      native_lots="1", premiums_coin=["0.02", "0.01"])
        result = calculate_minimum_fee(doc, **inputs)
        result["native_fee_minimum_coin"] = "0"
        with self.assertRaisesRegex(AssertionError, "INDEPENDENT_NATIVE_FEE"):
            verify(doc, result, **inputs)

    def test_untrusted_promotion_never_in_report(self):
        result = calculate_minimum_fee(schedule(), event_type="OPEN",
                                       asset="BTC", at_ms=FIRST+1000,
                                       native_lots="1",
                                       premiums_coin=["0.02", "0.01"])
        self.assertFalse(result["promotion_authorized"])
        self.assertFalse(result["original_options_economic_train_certified"])


if __name__ == "__main__":
    unittest.main()
