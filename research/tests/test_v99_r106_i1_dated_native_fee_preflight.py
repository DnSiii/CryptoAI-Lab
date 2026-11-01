"""Synthetic/adversarial tests only. No licensed options, PnL or orders."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_dated_terms_can_precede_train_without_reading_sealed_period(self):
        doc = schedule()
        doc["rows"][0]["effective_from_ms"] = FIRST - 365 * 86400000
        doc["rows"][0]["effective_to_ms"] = END + 365 * 86400000
        result = calculate_minimum_fee(
            doc, event_type="OPEN", asset="BTC", at_ms=FIRST+1000,
            native_lots="1", premiums_coin=["0.02", "0.01"])
        self.assertFalse(result["historical_native_fee_certified"])
        with self.assertRaisesRegex(ValueError, "INVALID_NATIVE_FEE_CLOCK_OR_ASSET"):
            calculate_minimum_fee(
                doc, event_type="OPEN", asset="BTC", at_ms=END+1000,
                native_lots="1", premiums_coin=["0.02", "0.01"])

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

    def test_swapped_signed_attestation_and_fee_descriptor_fail_closed(self):
        # Simulate a valid signature check followed by a simultaneous
        # attestation + fee schedule swap before the preflight reopens files.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = b'{"signed":"original"}'
            replacement = b'{"signed":"replacement"}'
            (root / "attestation.json").write_bytes(original)
            (root / "schedule.json").write_text(json.dumps(schedule()))
            def swap_after_verification(*args, **kwargs):
                (root / "attestation.json").write_bytes(replacement)
                return {"independent_signature_verified": True,
                        "verified_attestation_sha256":
                            hashlib.sha256(original).hexdigest()}
            with patch(
                "research.tools.v99_r106_i1_dated_native_fee_preflight.verify_signed_event_attestation",
                side_effect=swap_after_verification,
            ):
                with self.assertRaisesRegex(
                    ValueError, "SIGNED_FEE_ATTESTATION_CHANGED_AFTER_VERIFICATION"
                ):
                    signed_fee_preflight(
                        root, "a"*64, "b"*64, event_type="OPEN",
                        asset="BTC", at_ms=FIRST+1000, native_lots="1",
                        scenario="severe", fee_coin="0.01",
                        slippage_coin="0.01", premiums_coin=["0.02", "0.01"])

    def test_signed_settlement_no_invented_slippage_and_native_fee_floor(self):
        # Synthetic signature stub only: the production signature gate is
        # separately tested with actual ephemeral Ed25519 signatures.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = json.dumps(schedule(), sort_keys=True).encode()
            (root / "fee.json").write_bytes(raw)
            descriptor = {"file": "fee.json",
                          "sha256": hashlib.sha256(raw).hexdigest()}
            attestation = {"evidence": {
                "historical_account_fee_schedule": descriptor}}
            payload = json.dumps(attestation).encode()
            (root / "attestation.json").write_bytes(payload)
            fake_verified = {"independent_signature_verified": True,
                "verified_attestation_sha256": hashlib.sha256(payload).hexdigest()}
            kwargs = dict(
                event_type="SETTLE_BATCH", asset="BTC", at_ms=FIRST+1000,
                native_lots="1", scenario="severe", fee_coin="0.0024",
                strikes_usd=["30000", "25000"],
                delivery_index_usd="28000")
            with patch(
                "research.tools.v99_r106_i1_dated_native_fee_preflight.verify_signed_event_attestation",
                return_value=fake_verified,
            ):
                result = signed_fee_preflight(
                    root, "a"*64, "b"*64, slippage_coin="0", **kwargs)
                self.assertFalse(result["historical_native_fee_certified"])
                with self.assertRaisesRegex(
                    ValueError, "INVENTED_CONTRACTUAL_SETTLEMENT_SLIPPAGE"
                ):
                    signed_fee_preflight(
                        root, "a"*64, "b"*64, slippage_coin="0.0024", **kwargs)
                with self.assertRaisesRegex(
                    ValueError, "NATIVE_OR_SCENARIO_FRICTION_UNDERPAYMENT"
                ):
                    signed_fee_preflight(
                        root, "a"*64, "b"*64, slippage_coin="0",
                        **dict(kwargs, fee_coin="0.00001"))

    def test_signed_wallet_path_vetoes_primary_total_and_leg_tampering(self):
        # Synthetic attestation stub: independent math MUST run inside the
        # actual signed wallet fee path before a debit can be accepted.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = json.dumps(schedule(), sort_keys=True).encode()
            (root / "fee.json").write_bytes(raw)
            payload = json.dumps({"evidence": {
                "historical_account_fee_schedule": {
                    "file": "fee.json", "sha256": hashlib.sha256(raw).hexdigest()
                }
            }}).encode()
            (root / "attestation.json").write_bytes(payload)
            verified = {"independent_signature_verified": True,
                        "verified_attestation_sha256":
                            hashlib.sha256(payload).hexdigest()}
            inputs = dict(event_type="OPEN", asset="BTC", at_ms=FIRST+1000,
                          native_lots="1", premiums_coin=["0.02", "0.01"])
            correct = calculate_minimum_fee(schedule(), **inputs)
            understated = dict(correct, native_fee_minimum_coin="0")
            wrong_legs = dict(correct, leg_native_fee_coin=[
                "0", correct["native_fee_minimum_coin"]
            ])
            with patch(
                "research.tools.v99_r106_i1_dated_native_fee_preflight.verify_signed_event_attestation",
                return_value=verified,
            ):
                for forged in (understated, wrong_legs):
                    with self.subTest(forged=forged):
                        with patch(
                            "research.tools.v99_r106_i1_dated_native_fee_preflight.calculate_minimum_fee",
                            return_value=forged,
                        ):
                            with self.assertRaisesRegex(
                                ValueError, "SIGNED_NATIVE_FEE_INDEPENDENT_ORACLE_MISMATCH"
                            ):
                                signed_fee_preflight(
                                    root, "a"*64, "b"*64, scenario="severe",
                                    fee_coin="0.01", slippage_coin="0.01",
                                    **inputs)
                good = signed_fee_preflight(
                    root, "a"*64, "b"*64, scenario="severe",
                    fee_coin="0.01", slippage_coin="0.01", **inputs)
                self.assertFalse(good["historical_native_fee_certified"])
                self.assertFalse(good["promotion_authorized"])

    def test_untrusted_promotion_never_in_report(self):
        result = calculate_minimum_fee(schedule(), event_type="OPEN",
                                       asset="BTC", at_ms=FIRST+1000,
                                       native_lots="1",
                                       premiums_coin=["0.02", "0.01"])
        self.assertFalse(result["promotion_authorized"])
        self.assertFalse(result["original_options_economic_train_certified"])


    def test_mark_close_sides_use_dated_native_fee_and_independent_oracle(self):
        # MARK is a hypothetical exit, not a realized fill. Signed historical
        # native account terms must still bound the exit liability.
        doc = schedule()
        inputs = dict(event_type="MARK", asset="BTC", at_ms=FIRST+1000,
                      native_lots="1", premiums_coin=["0.09", "0.04"])
        result = calculate_minimum_fee(doc, **inputs)
        self.assertEqual(result["native_fee_minimum_coin"], "0.0006")
        self.assertTrue(verify(doc, result, **inputs)["independent_native_fee_arithmetic_verified"])
        forged = dict(result, leg_native_fee_coin=["0", "0.0006"])
        with self.assertRaisesRegex(AssertionError, "INDEPENDENT_NATIVE_FEE"):
            verify(doc, forged, **inputs)
        self.assertFalse(result["historical_native_fee_certified"])

    def test_signed_mark_rejects_historical_undercharge_before_nav(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = json.dumps(schedule(), sort_keys=True).encode()
            (root / "fee.json").write_bytes(raw)
            payload = json.dumps({"evidence": {"historical_account_fee_schedule": {
                "file": "fee.json", "sha256": hashlib.sha256(raw).hexdigest()}}}).encode()
            (root / "attestation.json").write_bytes(payload)
            fake_verified = {"independent_signature_verified": True,
                             "verified_attestation_sha256": hashlib.sha256(payload).hexdigest()}
            params = dict(event_type="MARK", asset="BTC", at_ms=FIRST+1000,
                          native_lots="1", scenario="severe",
                          premiums_coin=["0.09", "0.04"], slippage_coin="0.0024")
            with patch("research.tools.v99_r106_i1_dated_native_fee_preflight.verify_signed_event_attestation",
                       return_value=fake_verified):
                with self.assertRaisesRegex(ValueError, "NATIVE_OR_SCENARIO_FRICTION_UNDERPAYMENT"):
                    signed_fee_preflight(root, "a"*64, "b"*64, fee_coin="0.0005", **params)
                accepted = signed_fee_preflight(root, "a"*64, "b"*64,
                                                fee_coin="0.0024", **params)
                self.assertFalse(accepted["promotion_authorized"])
                self.assertEqual(accepted["status"],
                                 "SIGNED_NATIVE_FEE_LOWER_BOUND_ONLY_NOT_EXECUTION_CERTIFICATION")


if __name__ == "__main__":
    unittest.main()
