"""Adversarial source-only tests; no original licensed market data in fixtures."""
import csv
import gzip
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research_tools import v99_r106_tardis_full_day_source as m


def make(rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=[
        "exchange", "symbol", "timestamp", "local_timestamp",
        "bid_price", "ask_price", "bid_amount", "ask_amount"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return gzip.compress(output.getvalue().encode())


def sample():
    t = m.DAY_START + 1_000_000
    return [
        {"exchange": "deribit", "symbol": "BTC-24JUN22-20000-P",
         "timestamp": str(t), "local_timestamp": str(t + 100),
         "bid_price": "0.01", "ask_price": "0.02",
         "bid_amount": "1", "ask_amount": "2"},
        {"exchange": "deribit", "symbol": "ETH-24JUN22-1000-P",
         "timestamp": str(t + 1000), "local_timestamp": str(t + 1100),
         "bid_price": "0.02", "ask_price": "0.03",
         "bid_amount": "3", "ask_amount": "4"},
    ]


class LicensedDaySourceTest(unittest.TestCase):
    def test_fixture_is_never_original_economic_certification(self):
        raw = make(sample())
        result = m.inspect_gzip(io.BytesIO(raw), fixture=True)
        self.assertEqual(result["status"], "SYNTHETIC_FIXTURE_ONLY")
        self.assertEqual(result["original_compressed_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["original_quote_rows"], 2)
        self.assertEqual(result["asset_counts"]["BTC"]["valid_put_quotes"], 1)
        self.assertEqual(result["asset_counts"]["ETH"]["valid_put_quotes"], 1)
        self.assertFalse(result["promotion_authorized"])
        self.assertFalse(result["economic_train_executed"])
        self.assertFalse(result["complete_2021_2023_archive"])
        self.assertFalse(result["vendor_gap_certified"])

    def test_missing_key_makes_zero_network_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(m, "OUT", Path(tmp) / "out.json"), \
                 patch.dict(os.environ, {"TARDIS_API_KEY": ""}), \
                 patch.object(m, "urlopen", side_effect=AssertionError("NETWORK")):
                result = m.main()
                self.assertEqual(result["status"], "BLOCKED_NO_AUTHENTICATED_ENTITLEMENT")
                self.assertEqual(result["network_requests"], 0)
                self.assertFalse(json.loads(m.OUT.read_text())["promotion_authorized"])

    def test_invalid_or_truncated_gzip_rejected(self):
        for data in (b"not-gzip", make(sample())[:-4]):
            with self.subTest(data=data[:10]):
                with self.assertRaises(m.SourceBlock):
                    m.inspect_gzip(io.BytesIO(data), fixture=True)

    def test_missing_eth_rejected(self):
        with self.assertRaisesRegex(m.SourceBlock, "MISSING_BTC_ETH"):
            m.inspect_gzip(io.BytesIO(make(sample()[:1])), fixture=True)

    def test_future_exchange_clock_rejected(self):
        rows = sample()
        rows[1]["timestamp"] = str(int(rows[1]["local_timestamp"]) + 1)
        with self.assertRaisesRegex(m.SourceBlock, "FUTURE_OR_OUTSIDE"):
            m.inspect_gzip(io.BytesIO(make(rows)), fixture=True)

    def test_outside_day_rejected(self):
        rows = sample()
        rows[0]["local_timestamp"] = str(m.DAY_END)
        with self.assertRaisesRegex(m.SourceBlock, "FUTURE_OR_OUTSIDE"):
            m.inspect_gzip(io.BytesIO(make(rows)), fixture=True)

    def test_bad_eth_quote_cannot_count_as_coverage(self):
        rows = sample()
        rows[1]["bid_price"] = "0.04"
        with self.assertRaisesRegex(m.SourceBlock, "MISSING_BTC_ETH"):
            m.inspect_gzip(io.BytesIO(make(rows)), fixture=True)

    def test_reordered_arrival_rejected(self):
        rows = sample()
        rows[1]["timestamp"] = str(m.DAY_START + 10)
        rows[1]["local_timestamp"] = str(m.DAY_START + 20)
        with self.assertRaisesRegex(m.SourceBlock, "REORDERED"):
            m.inspect_gzip(io.BytesIO(make(rows)), fixture=True)

    def test_bounded_compressed_stream_fails_closed(self):
        with self.assertRaisesRegex(m.SourceBlock, "BYTE_LIMIT"):
            m.inspect_gzip(io.BytesIO(make(sample())), fixture=True, max_bytes=15)

    def test_row_limit_fails_closed(self):
        with self.assertRaisesRegex(m.SourceBlock, "ROW_LIMIT"):
            m.inspect_gzip(io.BytesIO(make(sample())), fixture=True, max_rows=1)

    def test_wrong_venue_rejected(self):
        rows = sample()
        rows[1]["exchange"] = "other"
        with self.assertRaisesRegex(m.SourceBlock, "WRONG_VENDOR_VENUE"):
            m.inspect_gzip(io.BytesIO(make(rows)), fixture=True)


if __name__ == "__main__":
    unittest.main()
