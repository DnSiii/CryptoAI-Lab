"""Signed 661-day adapter integration: synthetic wiring only, NEVER original economics."""
import copy
import unittest
from unittest.mock import patch

from research.tests.test_v99_r106_i1_native_event_equity import (
    flat_fixture, one_position_fixture, complete_fixed_decisions,
)
from research.tools.v99_r106_i1_native_event_equity import replay_signed


def signed_shape():
    doc = one_position_fixture()
    doc["fixture"] = False
    doc["scenario_decisions"] = {
        scenario: complete_fixed_decisions(one_open=True)
        for scenario in ("severe", "supersevere")
    }
    count = 0
    for scenario, days in doc["scenarios"].items():
        for i, day in enumerate(days):
            for j, event in enumerate(day["events"]):
                event["attestation"] = f"FIXTURE_ONLY_NOT_A_REAL_SIGNATURE/{scenario}/{i}/{j}"
                count += 1
    return doc, count


class SignedNativeEventReplayIntegrationTests(unittest.TestCase):
    def test_fixture_rejected_without_replay(self):
        with self.assertRaisesRegex(ValueError, "SIGNED_ORIGINAL_REPLAY_REJECTS_FIXTURE"):
            replay_signed(one_position_fixture())

    def test_empty_nonfixture_not_vacuously_authenticated(self):
        doc = flat_fixture()
        doc["fixture"] = False
        with self.assertRaisesRegex(ValueError, "SIGNED_ORIGINAL_REPLAY_REQUIRES_EVENTS"):
            replay_signed(doc)

    def test_missing_open_mark_and_settlement_attestations_rejected(self):
        for kind, error in (
            ("OPEN", "MISSING_SIGNED_ORIGINAL_OPEN_ATTESTATION"),
            ("MARK", "MISSING_SIGNED_ORIGINAL_MARK_ATTESTATION"),
            ("SETTLE_BATCH", "MISSING_SIGNED_ORIGINAL_SETTLEMENT_ATTESTATION"),
        ):
            doc, _ = signed_shape()
            for day in doc["scenarios"]["severe"]:
                for event in day["events"]:
                    if event["kind"] == kind:
                        del event["attestation"]
                        break
                else:
                    continue
                break
            # A test-only fake verifier is necessary to reach a later event.
            # The real Ed25519 checks are separately exercised in the gate suite.
            with patch("research.tools.v99_r106_i1_cost_bound_execution.verify_signed_event_attestation",
                       return_value={"promotion_authorized": False}):
                with self.assertRaisesRegex(ValueError, error):
                    replay_signed(doc)

    def test_every_event_routes_through_signed_gate_without_promotion(self):
        doc, expected = signed_shape()
        verified = set()
        def fixture_only_verifier(root, digest):
            self.assertTrue(root.startswith("FIXTURE_ONLY_NOT_A_REAL_SIGNATURE/"))
            self.assertEqual(len(digest), 64)
            self.assertNotIn(root, verified)
            verified.add(root)
            return {"independent_signature_verified": True,
                    "promotion_authorized": False}
        # This mock verifies event wiring only. It is NOT a real signature,
        # original-source certificate, economic TRAIN, or independent replay.
        with patch("research.tools.v99_r106_i1_cost_bound_execution.verify_signed_event_attestation",
                   side_effect=fixture_only_verifier):
            report = replay_signed(doc)
        self.assertEqual(len(verified), expected)
        self.assertGreater(expected, 60)
        self.assertTrue(report["signed_event_adapter_replayed"])
        self.assertEqual(len(report["scenarios"]["severe"]), 661)
        for flag in ("original_source_receipts_independently_authenticated",
                     "original_options_economic_train_certified",
                     "promotion_authorized", "freeze_authorized",
                     "validation_opened", "holdout_opened", "orders_enabled",
                     "paper_publication_authorized"):
            self.assertFalse(report[flag])
        self.assertEqual(report["status"], "PROVISIONAL_UNCERTIFIED_NATIVE_EVENT_EQUITY")


if __name__ == "__main__":
    unittest.main()
