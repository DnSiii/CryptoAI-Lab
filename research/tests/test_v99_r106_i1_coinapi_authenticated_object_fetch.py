"""Adversarial source transport tests: synthetic bytes, never economics."""
from __future__ import annotations
import csv
import gzip
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from research.tools.v99_r106_i1_coinapi_authenticated_object_fetch import acquire

SYMBOL = "BTC-25FEB22-40000-P"
KEY = "T-QUOTES/D-20220123/E-DERIBIT/IDDI-test+SC-test+S-BTC__002D25FEB22__002D40000__002DP.csv.gz"
HEADER = ("id_site_coinapi", "time_exchange", "time_coinapi", "ask_px", "ask_sx", "bid_px", "bid_sx")


def original_gzip():
    text = io.StringIO(newline="")
    writer = csv.writer(text)
    writer.writerow(HEADER)
    writer.writerow(["", "2022-01-23T23:59:58.0000000Z",
                     "2022-01-23T23:59:58.1000000Z", "0.02", "2", "0.01", "3"])
    return gzip.compress(text.getvalue().encode(), mtime=0)


class FakeProvider:
    def __init__(self, content=None, *, size=None, get_error=False):
        self.content = original_gzip() if content is None else content
        self.size = len(self.content) if size is None else size
        self.get_error = get_error
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        assert kwargs["capture_output"] and kwargs["check"] is False
        assert "--key" in args and args[args.index("--key") + 1] == KEY
        if "head-object" in args:
            return subprocess.CompletedProcess(args, 0, json.dumps({
                "ContentLength": self.size, "ETag": '"not-sha256"'}), "")
        assert "get-object" in args
        if not self.get_error:
            Path(args[-1]).write_bytes(self.content)
        return subprocess.CompletedProcess(args, 1 if self.get_error else 0, "{}", "")


class CoinapiOriginalObjectFetchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.doc = self.root / "rights.txt"
        self.doc.write_text("TEST ONLY, NO REAL ENTITLEMENT", encoding="utf-8")
        self.digest = hashlib.sha256(self.doc.read_bytes()).hexdigest()
        self.output = self.root / "originals"

    def call(self, provider, **overrides):
        options = dict(license_document=self.doc, license_sha256=self.digest,
                       authorize_billable_read=True, api_key="synthetic-test-key",
                       runner=provider)
        options.update(overrides)
        return acquire(KEY, SYMBOL, self.output, **options)

    def test_no_key_never_issues_a_billable_request(self):
        provider = FakeProvider()
        result = self.call(provider, api_key="")
        self.assertEqual(result["status"], "BLOCKED_NO_COINAPI_API_KEY")
        self.assertEqual(provider.calls, [])
        self.assertFalse(self.output.exists())

    def test_no_explicit_authorization_never_issues_a_billable_request(self):
        provider = FakeProvider()
        result = self.call(provider, authorize_billable_read=False)
        self.assertEqual(result["status"], "BLOCKED_BILLABLE_PROVIDER_READ_NOT_AUTHORIZED")
        self.assertEqual(provider.calls, [])

    def test_exact_original_gzip_published_only_after_complete_intake(self):
        provider = FakeProvider()
        result = self.call(provider)
        self.assertEqual(result["status"], "ORIGINAL_PROVIDER_OBJECT_FORMAT_VERIFIED_NOT_ECONOMICS")
        self.assertEqual(result["original_rows"], 1)
        self.assertEqual(result["original_executable_depth_rows_not_fills"], 1)
        self.assertEqual(len(provider.calls), 2)
        raw = self.output / result["local_original_filename"]
        self.assertEqual(raw.read_bytes(), provider.content)
        self.assertEqual(result["original_gzip_sha256"], hashlib.sha256(provider.content).hexdigest())
        self.assertEqual(json.loads(Path(str(raw) + ".source.json").read_text()), result)
        self.assertFalse(result["economic_train_executed"])
        self.assertFalse(result["promotion_authorized"])
        with self.assertRaisesRegex(ValueError, "REFUSE_OVERWRITE_ORIGINAL_SOURCE"):
            self.call(FakeProvider())

    def test_head_oversize_fails_before_get(self):
        provider = FakeProvider(size=2_147_483_649)
        with self.assertRaisesRegex(ValueError, "OVERSIZED_ORIGINAL_OBJECT"):
            self.call(provider)
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(list(self.output.glob("*")), [])

    def test_get_length_mismatch_cannot_publish(self):
        provider = FakeProvider(size=len(original_gzip()) + 1)
        with self.assertRaisesRegex(ValueError, "HEAD_GET_LENGTH_MISMATCH"):
            self.call(provider)
        self.assertEqual(list(self.output.glob("*")), [])

    def test_corrupt_gzip_cannot_publish(self):
        provider = FakeProvider(content=b"not-gzip")
        with self.assertRaisesRegex(ValueError, "NOT_ORIGINAL_GZIP"):
            self.call(provider)
        self.assertEqual(list(self.output.glob("*")), [])

    def test_provider_get_denial_cannot_publish(self):
        provider = FakeProvider(get_error=True)
        result = self.call(provider)
        self.assertEqual(result["status"], "BLOCKED_PROVIDER_GET_OR_ENTITLEMENT")
        self.assertEqual(list(self.output.glob("*")), [])

    def test_license_digest_and_sealed_key_rejected_without_provider_call(self):
        provider = FakeProvider()
        with self.assertRaisesRegex(ValueError, "WRITTEN_LICENSE"):
            self.call(provider, license_sha256="0"*64)
        with self.assertRaisesRegex(ValueError, "SOURCE_KEY_OUTSIDE_SEALED_TRAIN"):
            acquire(KEY.replace("D-20220123", "D-20240201"), SYMBOL, self.output,
                    license_document=self.doc, license_sha256=self.digest,
                    api_key="test", authorize_billable_read=True, runner=provider)
        self.assertEqual(provider.calls, [])


if __name__ == "__main__":
    unittest.main()
