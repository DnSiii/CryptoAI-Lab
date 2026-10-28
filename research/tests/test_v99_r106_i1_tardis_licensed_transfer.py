"""Offline-only tests of licensed-transfer preflight; synthetic bytes are NOT market evidence."""
import csv
import gzip
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.tools.v99_r106_i1_tardis_licensed_transfer import transfer

DAY = datetime(2021, 12, 9, tzinfo=timezone.utc)
DAY_US = int(DAY.timestamp() * 1_000_000)


def fake_gzip():
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(("exchange", "symbol", "timestamp", "local_timestamp",
                     "bid_price", "ask_price", "bid_amount", "ask_amount"))
    expiry = (DAY + timedelta(days=28)).strftime("%d%b%y").upper()
    for i, asset, strike in ((1, "BTC", 30000), (2, "ETH", 2000)):
        writer.writerow(("deribit", f"{asset}-{expiry}-{strike}-P",
                         DAY_US+i*1_000_000, DAY_US+i*1_000_000,
                         "0.02", "0.025", "1", "1"))
    return gzip.compress(buffer.getvalue().encode())


def scope_bytes(valid=True):
    return json.dumps([{"exchange": "deribit", "from": "2021-01-01T00:00:00Z",
                        "to": "2024-01-01T00:00:00Z",
                        "dataPlan": "options" if valid else "perpetuals",
                        "symbols": ["OPTIONS"]}]).encode()


class Response:
    def __init__(self, body, *, status=200, content_type="application/gzip"):
        self.body = io.BytesIO(body)
        self.status = status
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.body.close()
    def read(self, n=-1):
        return self.body.read(n)


class Opener:
    def __init__(self, *, valid_scope=True, body=None, content_type="application/gzip"):
        self.valid_scope = valid_scope
        self.body = fake_gzip() if body is None else body
        self.content_type = content_type
        self.urls = []
    def __call__(self, request, timeout=None):
        self.urls.append(request.full_url)
        if request.full_url.endswith("api-key-info"):
            return Response(scope_bytes(self.valid_scope), content_type="application/json")
        if not request.full_url.endswith("/2021/12/09/OPTIONS.csv.gz"):
            raise AssertionError("UNEXPECTED_OR_SEALED_NETWORK_REQUEST")
        return Response(self.body, content_type=self.content_type)


class LicensedTransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "original"
        self.license = Path(self.tmp.name) / "vendor-grant.txt"
        self.license.write_text("OFFLINE TEST PLACEHOLDER NOT A REAL LICENSE")
    def call(self, opener, **kw):
        return transfer(self.root, execute=True, max_days=1, key="test-secret",
                        license_evidence=self.license, opener=opener, **kw)

    def test_default_dry_run_no_key_no_network(self):
        def no_network(*args, **kwargs):
            raise AssertionError("DRY_RUN_MADE_NETWORK_REQUEST")
        report = transfer(self.root, opener=no_network)
        self.assertEqual(report["planned_train_days"], 1)
        self.assertFalse(report["economic_train_executed"])
        self.assertFalse(self.root.exists())

    def test_missing_key_and_license_refused_before_network(self):
        opener = Opener()
        with self.assertRaisesRegex(ValueError, "API_KEY_NOT_CONFIGURED"):
            transfer(self.root, execute=True, key="", license_evidence=self.license, opener=opener)
        with self.assertRaisesRegex(ValueError, "LICENSE_EVIDENCE_REQUIRED"):
            transfer(self.root, execute=True, key="test-secret", opener=opener)
        self.assertEqual(opener.urls, [])

    def test_entitlement_must_cover_original_options(self):
        opener = Opener(valid_scope=False)
        with self.assertRaisesRegex(ValueError, "ENTITLEMENT_UNVERIFIED"):
            self.call(opener)
        self.assertEqual(len(opener.urls), 1)
        self.assertFalse(self.root.exists())

    def test_atomic_transfer_then_valid_existing_skip(self):
        opener = Opener()
        first = self.call(opener)
        self.assertEqual(first["downloaded_days"], 1)
        self.assertFalse(first["vendor_gap_attestation_verified"])
        self.assertFalse(first["promotion_authorized"])
        self.assertEqual((self.root / "2021-12-09.csv.gz").read_bytes(), fake_gzip())
        self.assertFalse((self.root / "manifest.json").exists())
        self.assertEqual(len(list(self.root.glob("*.part"))), 0)
        again = self.call(opener)
        self.assertEqual(again["downloaded_days"], 0)
        self.assertEqual(again["preexisting_valid_days"], 1)
        self.assertEqual(len(opener.urls), 3)

    def test_html_disguised_as_success_refused(self):
        opener = Opener(body=b"<html>paywall</html>", content_type="text/html")
        with self.assertRaisesRegex(ValueError, "NOT_GZIP"):
            self.call(opener)
        self.assertFalse((self.root / "2021-12-09.csv.gz").exists())
        self.assertEqual(len(list(self.root.glob("*.part"))), 0)

    def test_corrupt_gzip_crc_refused(self):
        damaged = fake_gzip()[:-5] + b"xxxxx"
        with self.assertRaises(ValueError):
            self.call(Opener(body=damaged))
        self.assertFalse((self.root / "2021-12-09.csv.gz").exists())

    def test_existing_invalid_file_never_overwritten(self):
        self.root.mkdir()
        dest = self.root / "2021-12-09.csv.gz"
        dest.write_bytes(b"protected-invalid-original")
        with self.assertRaises(ValueError):
            self.call(Opener())
        self.assertEqual(dest.read_bytes(), b"protected-invalid-original")

    def test_byte_cap_fails_without_partial_published(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_TOO_LARGE"):
            self.call(Opener(), max_day_bytes=10)
        self.assertFalse((self.root / "2021-12-09.csv.gz").exists())

    def test_never_request_sealed_or_extra_day(self):
        with self.assertRaisesRegex(ValueError, "INVALID_BOUNDED"):
            transfer(self.root, execute=True, max_days=662,
                     key="test-secret", license_evidence=self.license,
                     opener=Opener())


if __name__ == "__main__":
    unittest.main()
