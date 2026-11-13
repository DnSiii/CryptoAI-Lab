"""Adversarial original-byte verification; never touches live paper or Frozen."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_v99_epoch_raw_evidence import verify

def sha(b):
    return hashlib.sha256(b).hexdigest()

class RawEvidenceGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "old.bin").write_bytes(b"immutable historical ledger")
        (self.root / "fill.json").write_bytes(b'{"original":"receipt"}')
        self.manifest = {
            "mode": "RESEARCH_ONLY", "real_orders_enabled": False,
            "economics_status": "UNVERIFIED", "epoch_id": "epoch-20261113",
            "output_namespace": "research-forward-epochs/epoch-20261113",
            "variants": ["F1", "F12", "F3", "F7", "R98"],
            "predecessor": {
                "ledger_sha256": sha(b"immutable historical ledger"),
                "commit_sha": "a" * 40, "immutable_source": "historical",
                "raw_evidence_path": "old.bin",
            },
            "start_after_utc": "2026-11-13T12:00:00Z",
            "last_historical_reference_by_variant": {
                v: "2026-11-13T11:00:00Z" for v in ["F1","F12","F3","F7","R98"]
            },
            "receipts": [{
                "source": "original", "captured_at_utc": "2026-11-13T13:01:00Z",
                "event_at_utc": "2026-11-13T13:00:00Z", "instrument": "BTC-USDT",
                "units": "USDT", "quantity": "1", "price": "100",
                "fee_currency": "USDT", "fee_amount": "0.1",
                "settled_funding": "0", "raw_sha256": sha(b'{"original":"receipt"}'),
                "raw_evidence_path": "fill.json",
            }],
        }

    def test_original_bytes_pass_without_economic_promotion(self):
        result = verify(self.manifest, self.root)
        self.assertTrue(result["original_receipts_independently_verified"])
        self.assertFalse(result["economic_validation"])

    def test_tampered_receipt_rejected(self):
        (self.root / "fill.json").write_bytes(b"altered")
        with self.assertRaisesRegex(ValueError, "receipt original bytes"):
            verify(self.manifest, self.root)

    def test_tampered_predecessor_rejected(self):
        (self.root / "old.bin").write_bytes(b"altered")
        with self.assertRaisesRegex(ValueError, "predecessor original bytes"):
            verify(self.manifest, self.root)

    def test_missing_receipt_rejected(self):
        (self.root / "fill.json").unlink()
        with self.assertRaises(FileNotFoundError):
            verify(self.manifest, self.root)

    def test_no_receipts_rejected(self):
        self.manifest["receipts"] = []
        with self.assertRaisesRegex(ValueError, "zero original receipts"):
            verify(self.manifest, self.root)

    def test_traversal_rejected(self):
        self.manifest["receipts"][0]["raw_evidence_path"] = "../outside"
        with self.assertRaises(ValueError):
            verify(self.manifest, self.root)

    def test_symlink_rejected(self):
        (self.root / "fill.json").unlink()
        (self.root / "fill.json").symlink_to(self.root / "old.bin")
        with self.assertRaisesRegex(ValueError, "symlink"):
            verify(self.manifest, self.root)

if __name__ == "__main__":
    unittest.main()
