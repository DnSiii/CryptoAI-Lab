"""Signed 661-day adapter integration: synthetic wiring only, NEVER original economics.

Synthetic signed fixture tests intentionally bypass ONLY the additional dated-fee
wallet preflight; the real fee preflight and integration have separate adversarial
tests. A fixture signature is never historical venue/account provenance.
"""
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.tests.test_v99_r106_i1_native_event_equity import (
    flat_fixture, one_position_fixture, complete_fixed_decisions,
)
from research.tools.v99_r106_i1_native_event_equity import replay, replay_signed
from research.tools.v99_r106_i1_signed_event_source_gate import (
    REQUIRED, SCHEMA, ORACLE_SCHEMA, verify_signed_event_attestation,
)


def signed_shape():
    doc = one_position_fixture()
    doc["fixture"] = False
    doc["journal_attestation"] = "FIXTURE_ONLY_NOT_A_REAL_SIGNATURE/JOURNAL"
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

    def test_missing_whole_journal_attestation_rejected_before_any_event(self):
        doc, _ = signed_shape()
        del doc["journal_attestation"]
        with self.assertRaisesRegex(ValueError, "MISSING_SIGNED_WHOLE_JOURNAL_ATTESTATION"):
            replay_signed(doc)

    def test_journal_digest_changes_with_unsigned_daily_index_and_regime(self):
        # These were not covered by the per-event Ed25519 signatures.
        from research.tools.v99_r106_i1_signed_event_source_gate import event_digest
        doc, _ = signed_shape()
        def digest(d):
            return event_digest("JOURNAL", None, journal={
                k: v for k, v in d.items() if k != "journal_attestation"})
        original = digest(doc)
        doc["scenarios"]["severe"][0]["index_usd"]["BTC"] = "999999"
        self.assertNotEqual(original, digest(doc))
        doc, _ = signed_shape()
        original = digest(doc)
        doc["scenarios"]["severe"][0]["regime"] = "SHOCK"
        self.assertNotEqual(original, digest(doc))

    def test_changed_journal_digest_is_rejected_before_costed_events(self):
        doc, _ = signed_shape()
        from research.tools.v99_r106_i1_signed_event_source_gate import event_digest
        expected = event_digest("JOURNAL", None, journal={
            k: v for k, v in doc.items() if k != "journal_attestation"})
        doc["scenarios"]["severe"][0]["index_usd"]["BTC"] = "999999"
        def mock_external_attestor(root, digest):
            self.assertEqual(root, doc["journal_attestation"])
            self.assertNotEqual(digest, expected)
            raise ValueError("SIGNED_ATTESTATION_NOT_BOUND_TO_EVENT")
        with patch("research.tools.v99_r106_i1_native_event_equity.verify_signed_event_attestation",
                   side_effect=mock_external_attestor):
            with self.assertRaisesRegex(ValueError, "SIGNED_ATTESTATION_NOT_BOUND_TO_EVENT"):
                replay_signed(doc)

    @patch("research.tools.v99_r106_i1_cost_bound_execution._signed_dated_fee_bound", new=lambda *args, **kwargs: None)
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
            with patch("research.tools.v99_r106_i1_native_event_equity.verify_signed_event_attestation",
                       return_value={"promotion_authorized": False}), patch(
                       "research.tools.v99_r106_i1_cost_bound_execution.verify_signed_event_attestation",
                       return_value={"promotion_authorized": False}):
                with self.assertRaisesRegex(ValueError, error):
                    replay_signed(doc)

    @patch("research.tools.v99_r106_i1_cost_bound_execution._signed_dated_fee_bound", new=lambda *args, **kwargs: None)
    def test_full_661d_adapter_real_ephemeral_ed25519_fixture_signatures(self):
        # Synthetic source bytes signed by a TEMPORARY TEST key. This tests
        # cryptographic event binding, never an independent real auditor.
        doc, expected = signed_shape()
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            private = base / "test-private.pem"
            public = base / "test-public.pem"
            subprocess.run(["openssl", "genpkey", "-algorithm", "Ed25519",
                            "-out", str(private)], check=True, capture_output=True)
            subprocess.run(["openssl", "pkey", "-in", str(private), "-pubout",
                            "-out", str(public)], check=True, capture_output=True)
            env = {
                "V99_I1_TRUSTED_AUDITOR_PUBKEY": str(public),
                "V99_I1_TRUSTED_AUDITOR_PUBKEY_SHA256":
                    hashlib.sha256(public.read_bytes()).hexdigest(),
            }
            doc["journal_attestation"] = str(base / "whole_journal")
            for scenario, days in doc["scenarios"].items():
                for i, day in enumerate(days):
                    for j, event in enumerate(day["events"]):
                        event["attestation"] = str(base / scenario / str(i) / str(j))
            seen = set()

            def sign_fixture_then_verify(root, digest):
                self.assertNotIn(root, seen)
                seen.add(root)
                path = Path(root)
                path.mkdir(parents=True)
                evidence = {}
                for kind in sorted(REQUIRED - {"independent_event_oracle_replay"}):
                    name = kind + ".bin"
                    raw = ("SYNTHETIC_FIXTURE_NOT_VENUE_DATA:" + kind).encode()
                    (path / name).write_bytes(raw)
                    evidence[kind] = {"file": name,
                                      "sha256": hashlib.sha256(raw).hexdigest()}
                oracle = {
                    "schema": ORACLE_SCHEMA, "fixture": False,
                    "event_sha256": digest, "replay_status": "PASS",
                    "historical_economic_train_certified": False,
                    "promotion_authorized": False,
                    "bound_source_sha256": {
                        k: v["sha256"] for k, v in evidence.items()},
                }
                raw = json.dumps(oracle, sort_keys=True, separators=(",", ":")).encode()
                (path / "oracle.json").write_bytes(raw)
                evidence["independent_event_oracle_replay"] = {
                    "file": "oracle.json",
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
                attestation = {"schema": SCHEMA, "event_sha256": digest,
                               "evidence": evidence}
                (path / "attestation.json").write_text(
                    json.dumps(attestation, sort_keys=True, separators=(",", ":")),
                    encoding="utf-8")
                subprocess.run(["openssl", "pkeyutl", "-sign",
                                "-inkey", str(private), "-rawin",
                                "-in", str(path / "attestation.json"),
                                "-out", str(path / "attestation.sig")],
                               check=True, capture_output=True)
                return verify_signed_event_attestation(root, digest)

            with patch.dict(os.environ, env):
                with patch(
                    "research.tools.v99_r106_i1_native_event_equity.verify_signed_event_attestation",
                    side_effect=sign_fixture_then_verify,
                ), patch(
                    "research.tools.v99_r106_i1_cost_bound_execution.verify_signed_event_attestation",
                    side_effect=sign_fixture_then_verify,
                ):
                    report = replay_signed(doc)
            self.assertEqual(len(seen), expected + 1)
            self.assertEqual(report["scenarios"], replay(doc)["scenarios"])
            self.assertFalse(report["original_source_receipts_independently_authenticated"])
            self.assertFalse(report["original_options_economic_train_certified"])
            self.assertFalse(report["promotion_authorized"])

    @patch("research.tools.v99_r106_i1_cost_bound_execution._signed_dated_fee_bound", new=lambda *args, **kwargs: None)
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
        with patch("research.tools.v99_r106_i1_native_event_equity.verify_signed_event_attestation",
                   side_effect=fixture_only_verifier), patch(
                   "research.tools.v99_r106_i1_cost_bound_execution.verify_signed_event_attestation",
                   side_effect=fixture_only_verifier):
            report = replay_signed(doc)
        self.assertEqual(len(verified), expected + 1)
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
