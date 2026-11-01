"""Fail-closed CLI wiring controls; ALL DATA SYNTHETIC, NO ECONOMIC TRAIN.

Mocked signed CLI routing bypasses only the separate dated-fee proof, which
is exercised by dedicated wallet integration tests.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.tests.test_v99_r106_i1_native_event_equity import flat_fixture
from research.tests.test_v99_r106_i1_signed_native_event_replay import signed_shape
from research.tools.v99_r106_i1_native_event_equity import main

ARCHIVE = "a" * 64


class SignedNativeCLIControls(unittest.TestCase):
    def _paths(self, root, document):
        source = Path(root) / "input.json"
        output = Path(root) / "output.json"
        source.write_text(json.dumps(document), encoding="utf-8")
        return source, output

    def test_unsigned_nonfixture_cli_fails_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = self._paths(directory, signed_shape()[0])
            with self.assertRaisesRegex(ValueError, "NONFIXTURE_CLI_REQUIRES_EXPLICIT_SIGNED_MODE"):
                main(source, output)
            self.assertFalse(output.exists())

    def test_signed_cli_rejects_fixture_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = self._paths(directory, flat_fixture())
            with self.assertRaisesRegex(ValueError, "SIGNED_ORIGINAL_REPLAY_REJECTS_FIXTURE"):
                main(source, output, signed=True, expected_archive_manifest_sha256=ARCHIVE)
            self.assertFalse(output.exists())

    def test_signed_nonfixture_without_external_trust_anchor_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            document, _ = signed_shape()
            # A real directory must exist to reach the independent key gate.
            # The verifier correctly checks evidence-root existence first.
            document["journal_attestation"] = directory
            for rows in document["scenarios"].values():
                for day in rows:
                    for event in day["events"]:
                        event["attestation"] = directory
            source, output = self._paths(directory, document)
            with patch.dict(os.environ, {
                "V99_I1_TRUSTED_AUDITOR_PUBKEY": "",
                "V99_I1_TRUSTED_AUDITOR_PUBKEY_SHA256": "",
            }):
                with self.assertRaisesRegex(ValueError, "MISSING_INDEPENDENT_AUDITOR_TRUST_ANCHOR"):
                    main(source, output, signed=True, expected_archive_manifest_sha256=ARCHIVE)
            self.assertFalse(output.exists())

    @patch("research.tools.v99_r106_i1_cost_bound_execution._signed_dated_fee_bound", new=lambda *args, **kwargs: {"immediate_close_fee_minimum_coin": "0"})
    def test_signed_cli_dispatch_mocked_event_gate_is_still_provisional(self):
        # The mock proves CLI routing only, NOT real auditor provenance.
        with tempfile.TemporaryDirectory() as directory:
            document, expected = signed_shape()
            source, output = self._paths(directory, document)
            seen = []
            def mock_only(attestation, digest, **kwargs):
                seen.append((attestation, digest, kwargs))
                return {"independent_signature_verified": True,
                        "promotion_authorized": False}
            with patch(
                "research.tools.v99_r106_i1_native_event_equity.verify_signed_event_attestation",
                side_effect=mock_only,
            ), patch(
                "research.tools.v99_r106_i1_cost_bound_execution.verify_signed_event_attestation",
                side_effect=mock_only,
            ):
                report = main(source, output, signed=True, expected_archive_manifest_sha256=ARCHIVE)
            self.assertEqual(len(seen), expected + 1)
            self.assertTrue(all(call[2].get("expected_archive_manifest_sha256") == ARCHIVE for call in seen))
            self.assertTrue(report["signed_event_adapter_replayed"])
            self.assertEqual(len(report["scenarios"]["severe"]), 661)
            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "PROVISIONAL_UNCERTIFIED_NATIVE_EVENT_EQUITY")
            for key in ("original_source_receipts_independently_authenticated",
                        "original_options_economic_train_certified",
                        "promotion_authorized", "freeze_authorized",
                        "validation_opened", "holdout_opened", "orders_enabled"):
                self.assertFalse(saved[key])

    def test_real_subprocess_signed_mode_no_key_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            document, _ = signed_shape()
            document["journal_attestation"] = directory
            for rows in document["scenarios"].values():
                for day in rows:
                    for event in day["events"]:
                        event["attestation"] = directory
            source, output = self._paths(directory, document)
            env = dict(os.environ)
            env.pop("V99_I1_TRUSTED_AUDITOR_PUBKEY", None)
            env.pop("V99_I1_TRUSTED_AUDITOR_PUBKEY_SHA256", None)
            process = subprocess.run(
                [sys.executable, "-m",
                 "research.tools.v99_r106_i1_native_event_equity",
                 str(source), str(output), "--signed",
                 "--archive-manifest-sha256", ARCHIVE],
                capture_output=True, text=True, env=env, timeout=60,
            )
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("MISSING_INDEPENDENT_AUDITOR_TRUST_ANCHOR", process.stderr)
            self.assertFalse(output.exists())

    def test_signed_missing_or_invalid_archive_crosspin_fails_before_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = self._paths(directory, signed_shape()[0])
            for invalid in (None, "", "g" * 64, "a" * 63, 1, True):
                with self.subTest(invalid=invalid):
                    with self.assertRaisesRegex(
                        ValueError, "SIGNED_CLI_REQUIRES_ORIGINAL_ARCHIVE_MANIFEST_SHA256"
                    ):
                        main(source, output, signed=True,
                             expected_archive_manifest_sha256=invalid)
                    self.assertFalse(output.exists())

    def test_unsigned_cli_cannot_claim_original_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = self._paths(directory, flat_fixture())
            with self.assertRaisesRegex(
                ValueError, "UNSIGNED_CLI_CANNOT_CLAIM_ORIGINAL_MANIFEST"
            ):
                main(source, output, expected_archive_manifest_sha256=ARCHIVE)
            self.assertFalse(output.exists())

    def test_signed_subprocess_without_crosspin_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = self._paths(directory, signed_shape()[0])
            process = subprocess.run(
                [sys.executable, "-m",
                 "research.tools.v99_r106_i1_native_event_equity",
                 str(source), str(output), "--signed",
                 "--archive-manifest-sha256", "g" * 64],
                capture_output=True, text=True, timeout=60,
            )
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("SIGNED_CLI_REQUIRES_ORIGINAL_ARCHIVE_MANIFEST_SHA256",
                          process.stderr)
            self.assertFalse(output.exists())

    def test_fixture_default_cli_remains_available(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = self._paths(directory, flat_fixture())
            report = main(source, output)
            self.assertEqual(len(report["scenarios"]["severe"]), 661)
            self.assertFalse(report["signed_event_adapter_replayed"])
            self.assertFalse(report["promotion_authorized"])
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
