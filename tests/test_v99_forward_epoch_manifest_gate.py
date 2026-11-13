"""Adversarial, offline, fail-closed checks for the R106 forward-epoch manifest."""
import copy
import hashlib
import unittest
from scripts.validate_v99_forward_epoch_manifest import validate

H = hashlib.sha256(b"immutable predecessor bytes").hexdigest()
R = hashlib.sha256(b"original exchange receipt bytes").hexdigest()

def good():
    return {
        "mode": "RESEARCH_ONLY", "real_orders_enabled": False,
        "economics_status": "UNVERIFIED", "epoch_id": "forward-20261113-a",
        "output_namespace": "research-forward-epochs/forward-20261113-a",
        "variants": ["F1", "F12", "F3", "F7", "R98"],
        "predecessor": {"ledger_sha256": H, "commit_sha": "a" * 40, "immutable_source": "historical-paper"},
        "start_after_utc": "2026-11-13T10:00:00Z",
        "last_historical_reference_by_variant": {v: "2026-11-13T09:00:00Z" for v in ("F1", "F12", "F3", "F7", "R98")},
        "receipts": [{
            "source": "exchange-original", "captured_at_utc": "2026-11-13T10:02:00Z",
            "event_at_utc": "2026-11-13T10:01:00Z", "instrument": "BTC-USDT",
            "units": "BTC", "quantity": "0.001", "price": "90000",
            "fee_currency": "USDT", "fee_amount": "0.01",
            "settled_funding": "0", "raw_sha256": R
        }]
    }

class ManifestGate(unittest.TestCase):
    def test_valid_structure_is_not_economic_certification(self):
        r = validate(good())
        self.assertTrue(r["validated_manifest_structure"])
        self.assertFalse(r["original_receipts_independently_verified"])
        self.assertFalse(r["economic_validation"])

    def test_adversarial_rejections(self):
        mutations = [
            lambda m: m.update(real_orders_enabled=True),
            lambda m: m.update(mode="LIVE"),
            lambda m: m.update(economics_status="VERIFIED"),
            lambda m: m["variants"].append("F1"),
            lambda m: m.update(output_namespace="paper-results/overwrite"),
            lambda m: m["predecessor"].update(ledger_sha256="0" * 63),
            lambda m: m.update(start_after_utc="2026-11-13T09:00:00Z"),
            lambda m: m["receipts"][0].update(event_at_utc="2026-11-13T10:00:00Z"),
            lambda m: m["receipts"][0].update(captured_at_utc="2026-11-13T09:59:00Z"),
            lambda m: m["receipts"][0].update(raw_sha256="f" * 63),
            lambda m: m["receipts"][0].pop("fee_amount"),
            lambda m: m["receipts"].append(copy.deepcopy(m["receipts"][0])),
            lambda m: m.update(output_namespace="research-forward-epochs/../paper-results"),
            lambda m: m.update(output_namespace="research-forward-epochs/another-epoch"),
            lambda m: m["receipts"][0].update(quantity="NaN"),
            lambda m: m["receipts"][0].update(price="Infinity"),
            lambda m: m["receipts"][0].update(quantity="0"),
            lambda m: m["receipts"][0].update(price="-1"),
            lambda m: m["receipts"][0].update(fee_amount="-0.01"),
            lambda m: m.update(epoch_id="../escape"),
            lambda m: m.update(epoch_id="epoch with spaces"),
            lambda m: m["receipts"][0].update(source=""),
            lambda m: m["receipts"][0].update(instrument="  "),
            lambda m: m["receipts"][0].update(units=None),
            lambda m: m["receipts"][0].update(fee_currency=""),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(case=i):
                m = good()
                mutate(m)
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    validate(m)

if __name__ == "__main__":
    unittest.main()
