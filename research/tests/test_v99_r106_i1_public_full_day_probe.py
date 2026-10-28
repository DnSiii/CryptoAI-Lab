"""OFFLINE negative controls only; no vendor evidence or economic performance."""
import csv
import gzip
import io
import unittest
from datetime import datetime, timedelta, timezone

from research.tools.v99_r106_i1_public_full_day_probe import probe, URL


class Response:
    def __init__(self, body, *, status=200, headers=None):
        self.status = status
        self.body = io.BytesIO(body)
        self.headers = headers or {
            "Content-Type": "application/gzip", "Content-Length": str(len(body))}
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.body.close()
    def read(self, n=-1):
        return self.body.read(n)


def day_gzip(*, day=datetime(2022, 6, 1, tzinfo=timezone.utc), eth=True):
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(("exchange", "symbol", "timestamp", "local_timestamp",
                     "bid_price", "ask_price", "bid_amount", "ask_amount"))
    for i, asset in enumerate(("BTC", "ETH") if eth else ("BTC",)):
        expiry = (day + timedelta(days=28)).strftime("%d%b%y").upper()
        us = int(day.timestamp()*1_000_000) + (i+1)*1_000_000
        writer.writerow(("deribit", f"{asset}-{expiry}-2000-P", us, us,
                         "0.02", "0.025", "1", "1"))
    return gzip.compress(out.getvalue().encode())


class PublicFullDayTests(unittest.TestCase):
    def call(self, body=None, *, headers=None, status=200, max_bytes=4096):
        seen = []
        body = day_gzip() if body is None else body
        def opener(request, timeout):
            seen.append(request)
            return Response(body, status=status, headers=headers)
        report = probe(opener, max_bytes=max_bytes)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].full_url, URL)
        self.assertNotIn("Authorization", dict(seen[0].header_items()))
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["economic_train_executed"])
        self.assertFalse(report["holdout_opened"])
        self.assertFalse(report["real_full_day_original_quote_scan_passed"])
        return report

    def test_full_day_valid_offline_fixture_not_certified(self):
        result = self.call()
        self.assertEqual(result["status"], "OFFLINE_FIXTURE_FULL_DAY_PASS_NOT_MARKET_EVIDENCE")
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["qualifying_put_rows_by_asset"], {"BTC": 1, "ETH": 1})
        self.assertEqual(len(result["sha256"]), 64)

    def test_wrong_utc_day_rejected(self):
        result = self.call(day_gzip(day=datetime(2022, 7, 1, tzinfo=timezone.utc)))
        self.assertEqual(result["status"], "PUBLIC_DAY_ORIGINAL_SCAN_FAILED")

    def test_missing_eth_not_full_source(self):
        result = self.call(day_gzip(eth=False))
        self.assertEqual(result["status"], "PUBLIC_DAY_ORIGINAL_SCAN_FAILED")

    def test_invalid_gzip_or_html_rejected(self):
        self.assertEqual(self.call(b"<html>login</html>")["status"], "PUBLIC_DAY_NOT_GZIP")
        self.assertEqual(self.call(day_gzip()[:-4]+b"xxxx")["status"],
                         "PUBLIC_DAY_ORIGINAL_SCAN_FAILED")

    def test_bounded_size_and_incomplete_transfer(self):
        self.assertEqual(self.call(max_bytes=10)["status"], "BOUNDED_REAL_SOURCE_INCOMPLETE")
        body = day_gzip()
        headers = {"Content-Type": "application/gzip", "Content-Length": str(len(body)+5)}
        self.assertEqual(self.call(body, headers=headers)["status"], "PUBLIC_DAY_TRUNCATED")

    def test_http_and_content_type_fail_closed(self):
        self.assertEqual(self.call(status=403)["status"], "PUBLIC_DAY_HTTP_NOT_200")
        headers = {"Content-Type": "text/html", "Content-Length": "20"}
        self.assertEqual(self.call(b"<html>login</html>", headers=headers)["status"],
                         "PUBLIC_DAY_NOT_GZIP")

    def test_invalid_request_limit(self):
        with self.assertRaisesRegex(ValueError, "INVALID_BOUNDED"):
            probe(lambda *a, **kw: None, max_bytes=True)


if __name__ == "__main__":
    unittest.main()
