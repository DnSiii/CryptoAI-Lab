"""Adversarial fixture-only Ed25519 provenance tests. NEVER original fills/ROI.

The two signed-wallet calls isolate cryptographic event/manifest identity;
the separate dated-fee integration suite checks actual wallet debits.
"""
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from research.tools.v99_r106_i1_native_coin_account_replay import D, Quote, start_wallet
from research.tools.v99_r106_i1_cost_bound_execution import costed_open, charge_floor
from research.tools.v99_r106_i1_signed_event_source_gate import (
    REQUIRED, SCHEMA, event_digest, verify_signed_event_attestation,
)

AT = int(datetime.fromisoformat("2022-01-03T00:00:00+00:00").timestamp() * 1000)
EXP = int(datetime.fromisoformat("2022-02-04T08:00:00+00:00").timestamp() * 1000)


def quote(strike, bid, ask):
    return Quote("BTC", f"BTC-04FEB22-{strike}-P", EXP, D(strike),
                 D(bid), D(ask), D("10"), D("10"), AT-2000, AT-1000, D("46000"))


class SignedEventSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "evidence"
        self.root.mkdir()
        self.private = self.base / "auditor_private.pem"
        self.public = self.base / "auditor_public.pem"
        subprocess.run(["openssl", "genpkey", "-algorithm", "Ed25519",
                        "-out", str(self.private)], check=True, capture_output=True)
        subprocess.run(["openssl", "pkey", "-in", str(self.private), "-pubout",
                        "-out", str(self.public)], check=True, capture_output=True)
        self.env = {
            "V99_I1_TRUSTED_AUDITOR_PUBKEY": str(self.public),
            "V99_I1_TRUSTED_AUDITOR_PUBKEY_SHA256":
                hashlib.sha256(self.public.read_bytes()).hexdigest(),
        }
        self.w = start_wallet("BTC", "severe", "100")
        self.short = quote("50000", ".08", ".09")
        self.long = quote("45000", ".04", ".05")
        self.fee, self.slip = charge_floor("severe", "1")
        self.inputs = dict(name="p1", short=self.short, long=self.long, at_ms=AT,
                           native_lots="1", entry_fees_coin=self.fee,
                           entry_slippage_coin=self.slip, initial_margin_coin="4",
                           maintenance_margin_coin="2")
        self.digest = event_digest("OPEN", self.w, **self.inputs)
        self.descriptors = {}
        for idx, kind in enumerate(sorted(REQUIRED)):
            name = f"source_{idx}.bin"
            f = self.root / name
            f.write_bytes(("SYNTHETIC_TEST_ONLY:" + kind).encode())
            self.descriptors[kind] = {
                "file": name, "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
            }
        self.write_oracle()
        self.sign()

    def write_oracle(self, **overrides):
        source_hashes = {
            kind: item["sha256"] for kind, item in self.descriptors.items()
            if kind != "independent_event_oracle_replay"
        }
        oracle = {
            "schema": "V99_I1_ORIGINAL_EVENT_INDEPENDENT_ORACLE_V1",
            "fixture": False, "event_sha256": self.digest,
            "replay_status": "PASS",
            "historical_economic_train_certified": False,
            "promotion_authorized": False,
            "bound_source_sha256": source_hashes,
        }
        oracle.update(overrides)
        raw = json.dumps(oracle, sort_keys=True, separators=(",", ":")).encode()
        self.write_oracle_raw(raw)

    def write_oracle_raw(self, raw):
        descriptor = self.descriptors["independent_event_oracle_replay"]
        (self.root / descriptor["file"]).write_bytes(raw)
        descriptor["sha256"] = hashlib.sha256(raw).hexdigest()

    def sign(self, *, digest=None, evidence=None):
        doc = {"schema": SCHEMA, "event_sha256": digest or self.digest,
               "evidence": evidence if evidence is not None else self.descriptors}
        (self.root / "attestation.json").write_text(
            json.dumps(doc, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", str(self.private),
                        "-rawin", "-in", str(self.root / "attestation.json"),
                        "-out", str(self.root / "attestation.sig")],
                       check=True, capture_output=True)

    @patch("research.tools.v99_r106_i1_cost_bound_execution._signed_dated_fee_bound", new=lambda *args, **kwargs: None)
    def test_valid_test_signature_allows_only_software_path_not_promotion(self):
        with patch.dict(os.environ, self.env):
            verdict = verify_signed_event_attestation(self.root, self.digest)
            self.assertEqual(verdict["evidence_classes_bound"], len(REQUIRED))
            self.assertFalse(verdict["promotion_authorized"])
            result = costed_open(self.w, "p1", self.short, self.long, AT, "1",
                                 self.fee, self.slip, "4", "2",
                                 fixture=False, attestation=self.root)
            self.assertEqual(len(result.positions), 1)
            with self.assertRaisesRegex(ValueError, "SIGNED_ATTESTATION_NOT_BOUND_TO_EVENT"):
                costed_open(self.w, "p1", self.short, self.long, AT, "1",
                            self.fee, self.slip, "4", "2.1",
                            fixture=False, attestation=self.root)

    @patch("research.tools.v99_r106_i1_cost_bound_execution._signed_dated_fee_bound", new=lambda *args, **kwargs: None)
    def test_real_signed_archive_must_equal_original_source_manifest(self):
        # Valid ephemeral Ed25519 signature for archive B is still invalid
        # when the independent source-byte oracle consumed archive A.
        correct = self.descriptors["licensed_train_archive_manifest"]["sha256"]
        with patch.dict(os.environ, self.env):
            verdict = verify_signed_event_attestation(
                self.root, self.digest,
                expected_archive_manifest_sha256=correct.upper())
            self.assertTrue(verdict["event_bound"])
            costed_open(self.w, "p1", self.short, self.long, AT, "1",
                        self.fee, self.slip, "4", "2", fixture=False,
                        attestation=self.root,
                        expected_archive_manifest_sha256=correct)
            with self.assertRaisesRegex(ValueError, "SIGNED_EVENT_ORIGINAL_ARCHIVE_MANIFEST_MISMATCH"):
                verify_signed_event_attestation(
                    self.root, self.digest,
                    expected_archive_manifest_sha256="0" * 64)
            with self.assertRaisesRegex(ValueError, "SIGNED_EVENT_ORIGINAL_ARCHIVE_MANIFEST_MISMATCH"):
                costed_open(self.w, "p1", self.short, self.long, AT, "1",
                            self.fee, self.slip, "4", "2", fixture=False,
                            attestation=self.root,
                            expected_archive_manifest_sha256="f" * 64)
            with self.assertRaisesRegex(ValueError, "INVALID_EXPECTED_ORIGINAL_ARCHIVE_MANIFEST_SHA256"):
                verify_signed_event_attestation(
                    self.root, self.digest,
                    expected_archive_manifest_sha256="not-a-sha")

    def test_no_trust_anchor_and_forged_boolean_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "MISSING_INDEPENDENT_AUDITOR_TRUST_ANCHOR"):
                verify_signed_event_attestation(self.root, self.digest)
        with patch.dict(os.environ, self.env):
            with self.assertRaisesRegex(ValueError, "UNTRUSTED_SOURCE_GATE_FLAGS"):
                costed_open(self.w, "p1", self.short, self.long, AT, "1",
                            self.fee, self.slip, "4", "2", fixture=False,
                            original_quote_verified=True, attestation=self.root)
            with self.assertRaisesRegex(ValueError, "FIXTURE_CANNOT_CLAIM"):
                costed_open(self.w, "p1", self.short, self.long, AT, "1",
                            self.fee, self.slip, "4", "2", fixture=True,
                            attestation=self.root)

    def test_real_ephemeral_signature_binds_daily_index_regime_and_decisions(self):
        # Real Ed25519 verification on a TEST-ONLY signed whole-journal digest.
        # A valid signature for one NAV/index path cannot authorize another.
        journal = {
            "initial_index_usd": {"BTC": "46000", "ETH": "3500"},
            "scenarios": {"severe": [{"index_usd": {"BTC": "46000", "ETH": "3500"},
                                      "regime": "RANGE", "fold_edge_index_usd": None}]},
            "scenario_decisions": {"severe": [{"action": "CASH"}]},
        }
        self.digest = event_digest("JOURNAL", None, journal=journal)
        self.write_oracle()
        self.sign()
        with patch.dict(os.environ, self.env):
            verified = verify_signed_event_attestation(self.root, self.digest)
            self.assertFalse(verified["promotion_authorized"])
            for change in ("index", "regime", "decision"):
                altered = json.loads(json.dumps(journal))
                if change == "index":
                    altered["scenarios"]["severe"][0]["index_usd"]["BTC"] = "47000"
                elif change == "regime":
                    altered["scenarios"]["severe"][0]["regime"] = "TREND"
                else:
                    altered["scenario_decisions"]["severe"][0]["action"] = "OPEN"
                with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "SIGNED_ATTESTATION_NOT_BOUND_TO_EVENT"
                ):
                    verify_signed_event_attestation(
                        self.root, event_digest("JOURNAL", None, journal=altered))

    def test_mutated_original_evidence_is_vetoed(self):
        with patch.dict(os.environ, self.env):
            (self.root / "source_0.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "SIGNED_ORIGINAL_EVIDENCE_SHA256_MISMATCH"):
                verify_signed_event_attestation(self.root, self.digest)

    def test_bad_signature_and_swapped_scenario_are_vetoed(self):
        with patch.dict(os.environ, self.env):
            other = start_wallet("BTC", "supersevere", "100")
            with self.assertRaisesRegex(ValueError, "SIGNED_ATTESTATION_NOT_BOUND_TO_EVENT"):
                verify_signed_event_attestation(
                    self.root, event_digest("OPEN", other, **self.inputs))
            (self.root / "attestation.sig").write_bytes(bytes(64))
            with self.assertRaisesRegex(ValueError, "INDEPENDENT_AUDITOR_SIGNATURE_INVALID"):
                verify_signed_event_attestation(self.root, self.digest)

    def test_path_traversal_and_missing_evidence_rejected_even_when_signed(self):
        with patch.dict(os.environ, self.env):
            tampered = json.loads(json.dumps(self.descriptors))
            tampered["historical_account_fee_schedule"]["file"] = "../escape.bin"
            self.sign(evidence=tampered)
            with self.assertRaisesRegex(ValueError, "UNSAFE_SIGNED_EVIDENCE_PATH"):
                verify_signed_event_attestation(self.root, self.digest)
            tampered.pop("historical_account_fee_schedule")
            self.sign(evidence=tampered)
            with self.assertRaisesRegex(ValueError, "SIGNED_ATTESTATION_NOT_BOUND_TO_EVENT"):
                verify_signed_event_attestation(self.root, self.digest)

    def test_changed_key_pin_rejected(self):
        with patch.dict(os.environ, {**self.env,
                                     "V99_I1_TRUSTED_AUDITOR_PUBKEY_SHA256": "0"*64}):
            with self.assertRaisesRegex(ValueError, "UNTRUSTED_INDEPENDENT_AUDITOR_KEY"):
                verify_signed_event_attestation(self.root, self.digest)

    def test_signed_unrelated_event_oracle_is_rejected(self):
        self.write_oracle(event_sha256="0"*64)
        self.sign()
        with patch.dict(os.environ, self.env):
            with self.assertRaisesRegex(ValueError, "SIGNED_ORACLE_NOT_BOUND"):
                verify_signed_event_attestation(self.root, self.digest)

    def test_signed_oracle_wrong_original_source_hash_is_rejected(self):
        hashes = {
            kind: item["sha256"] for kind, item in self.descriptors.items()
            if kind != "independent_event_oracle_replay"
        }
        hashes["historical_account_fee_schedule"] = "f"*64
        self.write_oracle(bound_source_sha256=hashes)
        self.sign()
        with patch.dict(os.environ, self.env):
            with self.assertRaisesRegex(ValueError, "SIGNED_ORACLE_NOT_BOUND"):
                verify_signed_event_attestation(self.root, self.digest)

    def test_signed_arbitrary_oracle_bytes_and_fixture_claim_rejected(self):
        with patch.dict(os.environ, self.env):
            self.write_oracle_raw(b"SYNTHETIC_TEST_ONLY:no_event_replay")
            self.sign()
            with self.assertRaisesRegex(ValueError, "INVALID_SIGNED_ORACLE_JSON"):
                verify_signed_event_attestation(self.root, self.digest)
            self.write_oracle(fixture=True)
            self.sign()
            with self.assertRaisesRegex(ValueError, "SIGNED_ORACLE_NOT_BOUND"):
                verify_signed_event_attestation(self.root, self.digest)

    def test_oracle_is_parsed_from_exact_verified_byte_snapshot(self):
        # Mutating the file after its read must not substitute a second JSON
        # for the bytes verified against the independently signed SHA256.
        oracle_path = self.root / self.descriptors["independent_event_oracle_replay"]["file"]
        real_read = Path.read_bytes
        def read_then_mutate(path):
            original = real_read(path)
            if path == oracle_path:
                oracle_path.write_bytes(b"FORGED_AFTER_HASH")
            return original
        with patch.dict(os.environ, self.env):
            with patch.object(Path, "read_bytes", read_then_mutate):
                result = verify_signed_event_attestation(self.root, self.digest)
        self.assertTrue(result["event_bound"])
        self.assertEqual(oracle_path.read_bytes(), b"FORGED_AFTER_HASH")
        self.assertFalse(result["promotion_authorized"])

    def test_signed_duplicate_json_key_and_intermediate_symlink_rejected(self):
        with patch.dict(os.environ, self.env):
            oracle_name = self.descriptors["independent_event_oracle_replay"]["file"]
            raw = (self.root / oracle_name).read_bytes()
            self.write_oracle_raw(raw.replace(
                b'{"bound_source_sha256":',
                b'{"fixture":false,"bound_source_sha256":', 1))
            self.sign()
            with self.assertRaisesRegex(ValueError, "INVALID_SIGNED_ORACLE_JSON"):
                verify_signed_event_attestation(self.root, self.digest)
            self.write_oracle()
            # A parent symlink is rejected even when the target stays under root.
            (self.root / "real_dir").mkdir()
            (self.root / "real_dir" / "copy.bin").write_bytes(
                (self.root / "source_0.bin").read_bytes())
            (self.root / "alias").symlink_to("real_dir", target_is_directory=True)
            key = sorted(REQUIRED)[0]
            self.descriptors[key]["file"] = "alias/copy.bin"
            self.sign()
            with self.assertRaisesRegex(ValueError, "MISSING_OR_UNSAFE_SIGNED_EVIDENCE_FILE"):
                verify_signed_event_attestation(self.root, self.digest)


if __name__ == "__main__":
    unittest.main()
