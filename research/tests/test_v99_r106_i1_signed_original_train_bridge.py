"""Synthetic controls for ORIGINAL-source + signed-event join. NOT market evidence."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.tests.test_v99_r106_i1_signed_native_event_replay import signed_shape
from research.tests.test_v99_r106_i1_original_to_provisional_numeric import (
    original_signal_document,
)
from research.tools.v99_r106_i1_native_event_equity import replay
from research.tools.v99_r106_i1_signed_original_train_bridge import main, run
from research.tools.v99_r106_i1_train_numeric_gate import evaluate_provisional


class SignedOriginalBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc, _ = signed_shape()
        cls.unsigned = replay(cls.doc)
        cls.numeric = evaluate_provisional(cls.unsigned)

    def source_mock(self):
        return {
            "original_signal_intents_checked": 180,
            "full_original_source_asset_week_books_independently_verified": 180,
            "original_complete_option_lifecycles_certified": 0,
            "original_quote_event_identities_checked": 100,
            "numeric_descriptive_only": self.numeric,
        }

    def signed_mock(self):
        result = copy.deepcopy(self.unsigned)
        result["signed_event_adapter_replayed"] = True
        return result

    def paths(self, root, document=None):
        root = Path(root)
        journal = root / "journal.json"
        journal.write_text(json.dumps(self.doc if document is None else document))
        return root / "signal.json", root / "original", journal, root / "result.json"

    def test_fixture_veto_before_source_or_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = copy.deepcopy(self.doc)
            doc["fixture"] = True
            args = self.paths(tmp, doc)
            with patch("research.tools.v99_r106_i1_signed_original_train_bridge.source_bound_run") as source:
                with self.assertRaisesRegex(ValueError, "SIGNED_NONFIXTURE_ORIGINAL_JOURNAL_REQUIRED"):
                    main(*args)
                source.assert_not_called()
            self.assertFalse(args[-1].exists())

    def test_real_missing_original_661d_archive_fails_before_signed_nav(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.paths(tmp)
            args[0].write_text(json.dumps(original_signal_document()))
            args[1].mkdir()
            with patch("research.tools.v99_r106_i1_signed_original_train_bridge.replay_signed") as signed:
                with self.assertRaisesRegex(ValueError, "ORIGINAL_661D_MANIFEST_NOT_DELIVERED"):
                    main(*args)
                signed.assert_not_called()
            self.assertFalse(args[-1].exists())

    def test_missing_external_auditor_key_after_source_checks_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = copy.deepcopy(self.doc)
            doc["journal_attestation"] = tmp
            args = self.paths(tmp, doc)
            with patch("research.tools.v99_r106_i1_signed_original_train_bridge.source_bound_run",
                       return_value=self.source_mock()):
                with patch.dict(os.environ, {
                    "V99_I1_TRUSTED_AUDITOR_PUBKEY": "",
                    "V99_I1_TRUSTED_AUDITOR_PUBKEY_SHA256": "",
                }):
                    with self.assertRaisesRegex(ValueError, "MISSING_INDEPENDENT_AUDITOR_TRUST_ANCHOR"):
                        main(*args)
            self.assertFalse(args[-1].exists())

    def test_signed_wallet_mismatch_veto_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.paths(tmp)
            bad = self.signed_mock()
            bad["scenarios"]["severe"][0]["equity_usd"] = "99999"
            with patch("research.tools.v99_r106_i1_signed_original_train_bridge.source_bound_run",
                       return_value=self.source_mock()):
                with patch("research.tools.v99_r106_i1_signed_original_train_bridge.replay_signed",
                           return_value=bad):
                    with self.assertRaisesRegex(ValueError, "SIGNED_ORIGINAL_NATIVE_WALLET_PARITY_MISMATCH"):
                        main(*args)
            self.assertFalse(args[-1].exists())

    def test_signed_source_numeric_mismatch_veto(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.paths(tmp)
            forged = self.source_mock()
            forged["numeric_descriptive_only"] = copy.deepcopy(self.numeric)
            forged["numeric_descriptive_only"]["scenarios"]["severe"]["total_roi"] = "999"
            with patch("research.tools.v99_r106_i1_signed_original_train_bridge.source_bound_run",
                       return_value=forged):
                with patch("research.tools.v99_r106_i1_signed_original_train_bridge.replay_signed",
                           return_value=self.signed_mock()):
                    with self.assertRaisesRegex(ValueError, "SIGNED_ORIGINAL_NUMERIC_SOURCE_PARITY_MISMATCH"):
                        main(*args)
            self.assertFalse(args[-1].exists())

    def test_joined_technical_mock_is_never_certified_and_no_overwrite(self):
        # Mocked source and signature results only test orchestration.
        with tempfile.TemporaryDirectory() as tmp:
            args = self.paths(tmp)
            with patch("research.tools.v99_r106_i1_signed_original_train_bridge.source_bound_run",
                       return_value=self.source_mock()):
                with patch("research.tools.v99_r106_i1_signed_original_train_bridge.replay_signed",
                           return_value=self.signed_mock()):
                    result = main(*args)
            self.assertTrue(args[-1].exists())
            self.assertTrue(result["signed_661d_event_wallet_replayed"])
            self.assertEqual(result["numeric_descriptive_only"], self.numeric)
            for key in ("original_options_economic_train_certified",
                        "promotion_authorized", "freeze_authorized",
                        "validation_opened", "holdout_opened", "orders_enabled"):
                self.assertFalse(result[key])
            with self.assertRaisesRegex(ValueError, "EXISTING_RESULT_IMMUTABLE"):
                main(*args)


if __name__ == "__main__":
    unittest.main()
