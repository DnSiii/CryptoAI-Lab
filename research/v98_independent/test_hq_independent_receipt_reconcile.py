"""Synthetic-only independent HQ receipt falsification; no market downloads."""
import hashlib
import unittest
from unittest.mock import patch
import hq_independent_receipt_reconcile as audit


def fake_reports():
    months = [(2022, 12)] + [(y, m) for y in (2023, 2024) for m in range(1, 13)]
    old = []
    hq = []
    manifest = []
    for asset in audit.ASSETS:
        for year, month in months:
            mm = f"{year}-{month:02d}"
            name = f"{asset}-1h-{mm}.zip"
            digest = hashlib.sha256(name.encode()).hexdigest()
            next_month = (year + 1, 1) if month == 12 else (year, month + 1)
            from datetime import datetime, timezone
            hours = int((datetime(*next_month, tzinfo=timezone.utc) -
                         datetime(year, month, 1, tzinfo=timezone.utc)).total_seconds() // 3600)
            missing = ["2023-03-24T13:00:00+00:00"] if mm == "2023-03" else []
            old.append({"archive": name, "provider_sha256": digest,
                        "rows": hours - len(missing), "expected_rows": hours,
                        "missing_utc": missing, "unexpected_utc": [],
                        "duplicate_timestamps": 0, "strictly_increasing": True})
            hq.append({"asset": asset, "month": mm, "sha256": digest,
                       "observed": hours - len(missing), "masked": len(missing)})
            manifest.append(f"{asset}|{mm}|{digest}\n")
    pin = hashlib.sha256("".join(manifest).encode()).hexdigest()
    inventory = {
        "decision": audit.STRICT_REJECTION, "holdout_2025_read": False,
        "historical_system_pnl_computed": False,
        "archive_count": 100, "provider_sha256_verified": 100,
        "expected_asset_hours": 73152, "observed_asset_hours": 73148,
        "defective_archives": 4, "archives": old,
    }
    masked = {
        "decision": audit.HQ_SOURCE_PASS,
        "complete_grid_source_rejection_still_active": True,
        "validation_2025_read": False, "data_2026_read": False,
        "historical_system_pnl_computed": False, "trading_authorized": False,
        "publisher_checksums_verified": 100, "calendar_asset_hours": 73152,
        "observed_asset_hours": 73148, "masked_asset_hours": 4,
        "two_pass_identical": True, "publisher_manifest_sha256": pin,
        "canonical_sha256": "a" * 64, "archives": hq,
    }
    return inventory, masked, pin


class HQIndependentReconcileTests(unittest.TestCase):
    def test_complete_matching_reports_pass(self):
        a, b, pin = fake_reports()
        with patch.object(audit, "PINNED_MANIFEST", pin):
            result = audit.reconcile(a, b)
        self.assertEqual(result["archive_pairs"], 100)
        self.assertEqual(result["masked_asset_hours"], 4)
        self.assertTrue(result["strict_complete_grid_source_still_rejected"])

    def test_tampered_archive_checksum_fails(self):
        a, b, pin = fake_reports()
        b["archives"][5]["sha256"] = "0" * 64
        with patch.object(audit, "PINNED_MANIFEST", pin):
            with self.assertRaisesRegex(ValueError, "HASH_DIVERGENCE"):
                audit.reconcile(a, b)

    def test_holdout_or_pnl_access_fails(self):
        a, b, pin = fake_reports()
        b["validation_2025_read"] = True
        with patch.object(audit, "PINNED_MANIFEST", pin):
            with self.assertRaisesRegex(ValueError, "FIREWALL"):
                audit.reconcile(a, b)

    def test_strict_rejection_cannot_be_rehabilitated(self):
        a, b, pin = fake_reports()
        a["decision"] = "PASS"
        with patch.object(audit, "PINNED_MANIFEST", pin):
            with self.assertRaisesRegex(ValueError, "STRICT_REJECTION"):
                audit.reconcile(a, b)

    def test_extra_gap_fails(self):
        a, b, pin = fake_reports()
        a["archives"][0]["missing_utc"] = ["2022-12-01T00:00:00+00:00"]
        with patch.object(audit, "PINNED_MANIFEST", pin):
            with self.assertRaisesRegex(ValueError, "UNEXPECTED_GAP"):
                audit.reconcile(a, b)


if __name__ == "__main__":
    unittest.main()
