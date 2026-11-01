"""Synthetic integration: actual signed wallet debits -> dated fee preflight.

The signature verifier is mocked ONLY to exercise fee/wallet integration.
This is not venue evidence, exchange fills, certified TRAIN, or ROI.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.tools.v99_r106_i1_cost_bound_execution import (
    costed_open, costed_mark, costed_settle_batch, charge_floor,
)
from research.tools.v99_r106_i1_native_coin_account_replay import (
    D, start_wallet,
)
from research.tests.test_v99_r106_i1_cost_bound_execution import AT, EXP, q
from research.tools.v99_r106_i1_signed_event_source_gate import event_digest

ARCHIVE = "a" * 64


def fee_evidence(root):
    schedule = {
        "schema": "V99_I1_HISTORICAL_NATIVE_OPTION_FEE_SCHEDULE_V1",
        "fixture": False, "venue": "deribit",
        "account_tier": "SYNTHETIC_ONLY_NOT_VENUE",
        "account_tier_original_document_sha256": "b" * 64,
        "rows": [
            {"asset": asset, "effective_from_ms": AT - 1000,
             "effective_to_ms": EXP + 1000,
             "account_tier": "SYNTHETIC_ONLY_NOT_VENUE",
             "entry_per_lot_coin": "0.005",
             "delivery_per_lot_coin": "0.005",
             "cap_fraction": "0.5", "native_lot_quantity": "1"}
            for asset in ("BTC", "ETH")
        ],
    }
    raw = json.dumps(schedule, sort_keys=True).encode()
    (root / "fee.json").write_bytes(raw)
    attestation = {"evidence": {
        "historical_account_fee_schedule": {
            "file": "fee.json", "sha256": hashlib.sha256(raw).hexdigest()}}}
    signed = json.dumps(attestation).encode()
    (root / "attestation.json").write_bytes(signed)
    return hashlib.sha256(signed).hexdigest()


class SignedWalletFeeBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        digest = fee_evidence(self.root)
        self.calls = []
        def verifier(root, event_hash, **kwargs):
            self.calls.append((str(root), event_hash, kwargs))
            return {"independent_signature_verified": True,
                    "verified_attestation_sha256": digest}
        self.gate = patch(
            "research.tools.v99_r106_i1_cost_bound_execution._source_gate",
            return_value={"independent_signature_verified": True})
        self.signed = patch(
            "research.tools.v99_r106_i1_dated_native_fee_preflight.verify_signed_event_attestation",
            side_effect=verifier)
        self.gate.start()
        self.signed.start()
        self.addCleanup(self.signed.stop)
        self.addCleanup(self.gate.stop)
        self.s = q("50000", ".08", ".09", AT)
        self.l = q("45000", ".04", ".05", AT)
        self.wallet = start_wallet("BTC", "severe", "100")

    def open(self, name, fee, archive=ARCHIVE):
        return costed_open(
            self.wallet, name, self.s, self.l, AT, "1",
            fee, "0.0024", "4", "2", fixture=False,
            attestation=str(self.root),
            expected_archive_manifest_sha256=archive)

    def test_open_uses_actual_original_executable_sides_and_rejects_underpay(self):
        with self.assertRaisesRegex(ValueError, "NATIVE_OR_SCENARIO_FRICTION_UNDERPAYMENT"):
            self.open("p1", "0.0024")
        self.assertEqual(len(self.wallet.positions), 0)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][2]["expected_archive_manifest_sha256"], ARCHIVE)
        expected = event_digest(
            "OPEN", self.wallet, name="p1", short=self.s, long=self.l,
            at_ms=AT, native_lots="1", entry_fees_coin="0.0024",
            entry_slippage_coin="0.0024", initial_margin_coin="4",
            maintenance_margin_coin="2")
        self.assertEqual(self.calls[0][1], expected)
        opened = self.open("p1", "0.01")
        self.assertEqual(len(opened.positions), 1)

    def test_missing_archive_manifest_fails_closed_before_cash(self):
        with self.assertRaisesRegex(ValueError, "SIGNED_NATIVE_FEE_REQUIRES_ORIGINAL_ARCHIVE_SHA256"):
            self.open("p1", "0.01", archive=None)
        self.assertEqual(len(self.wallet.positions), 0)
        self.assertEqual(len(self.calls), 0)

    def test_atomic_settlement_checks_every_position_individually(self):
        self.wallet = self.open("p1", "0.01")
        # Synthetic-only same-clock mark before another open; no invented NAV.
        floor, slip = charge_floor("severe", "1")
        self.wallet = costed_mark(self.wallet, "p1", self.s, self.l, AT,
                                  floor, slip, fixture=True)
        self.wallet = self.open("p2", "0.01")
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, "NATIVE_OR_SCENARIO_FRICTION_UNDERPAYMENT"):
            costed_settle_batch(
                self.wallet, ["p1", "p2"], EXP, "48000",
                {"p1": "0.01", "p2": "0.0024"}, fixture=False,
                attestation=str(self.root),
                expected_archive_manifest_sha256=ARCHIVE)
        self.assertEqual(len(self.wallet.positions), 2)
        self.assertEqual(len(self.calls), 2)
        expected = event_digest(
            "SETTLE_BATCH", self.wallet, names=["p1", "p2"], at_ms=EXP,
            original_delivery_index_usd="48000",
            delivery_fees_coin={"p1": "0.01", "p2": "0.0024"})
        self.assertEqual([x[1] for x in self.calls], [expected, expected])
        settled = costed_settle_batch(
            self.wallet, ["p1", "p2"], EXP, "48000",
            {"p1": "0.01", "p2": "0.01"}, fixture=False,
            attestation=str(self.root),
            expected_archive_manifest_sha256=ARCHIVE)
        self.assertEqual(len(settled.positions), 0)

    def test_fixture_path_does_not_require_historical_schedule(self):
        floor, slip = charge_floor("severe", "1")
        result = costed_open(
            self.wallet, "p1", self.s, self.l, AT, "1",
            floor, slip, "4", "2", fixture=True)
        self.assertEqual(len(result.positions), 1)
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
