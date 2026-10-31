"""Offline adversarial tests only; no historical source certification."""
import csv
import gzip
import json
import tempfile
import unittest
from pathlib import Path

from research.tools.v99_r106_i1_options_chain_reference import scan, LOWER, FIELDS
from research.verification.independent_v99_r106_i1_options_chain_reference import verify


class OriginalChainReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw = Path(self.tmp.name) / "sample.csv.gz"
        self.report = Path(self.tmp.name) / "report.json"
        self.rows = [
            {"exchange": "deribit", "symbol": "BTC-24JUN22-30000-P",
             "timestamp": str(LOWER + 10), "local_timestamp": str(LOWER + 20),
             "type": "put", "bid_price": "0.001", "ask_price": "0.002",
             "bid_amount": "1", "ask_amount": "2", "underlying_index": "SYN.BTC-24JUN22",
             "underlying_price": "30000"},
            {"exchange": "deribit", "symbol": "ETH-24JUN22-1800-P",
             "timestamp": str(LOWER + 100), "local_timestamp": str(LOWER + 110),
             "type": "put", "bid_price": "0.01", "ask_price": "0.02",
             "bid_amount": "5", "ask_amount": "6", "underlying_index": "ETH-USD",
             "underlying_price": "1800"},
        ]
        self.write()

    def write(self):
        with gzip.open(self.raw, "wt", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(FIELDS))
            writer.writeheader()
            writer.writerows(self.rows)

    def report_source(self):
        result = scan(self.raw)
        self.report.write_text(json.dumps(result))
        return result

    def test_original_shaped_source_and_independent_replay(self):
        result = self.report_source()
        self.assertEqual(result["assets"]["BTC"]["same_row_underlying_bbo_rows"], 1)
        self.assertEqual(result["assets"]["BTC"]["index_labels"]["SYN"], 1)
        self.assertEqual(result["assets"]["ETH"]["index_labels"]["OTHER"], 1)
        verify(self.raw, self.report)

    def test_forbidden_certification_fails_independent(self):
        doc = self.report_source()
        doc["promotion_authorized"] = 1
        self.report.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, "CERTIFICATION"):
            verify(self.raw, self.report)

    def test_forged_source_metrics_fail_independent(self):
        doc = self.report_source()
        doc["assets"]["ETH"]["same_row_underlying_bbo_rows"] += 1
        self.report.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, "METRIC"):
            verify(self.raw, self.report)

    def test_noncausal_arrival_rejected(self):
        self.rows[1]["local_timestamp"] = str(LOWER - 1)
        self.write()
        with self.assertRaisesRegex(ValueError, "NONCAUSAL"):
            scan(self.raw)

    def test_missing_original_column_rejected(self):
        with gzip.open(self.raw, "wt", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["exchange", "symbol"])
            writer.writeheader()
        with self.assertRaisesRegex(ValueError, "COLUMNS"):
            scan(self.raw)

    def test_invalid_last_book_is_not_counted(self):
        self.rows[0]["bid_price"] = "0.03"
        self.write()
        doc = self.report_source()
        self.assertEqual(doc["assets"]["BTC"]["same_row_underlying_bbo_rows"], 0)
        verify(self.raw, self.report)


if __name__ == "__main__":
    unittest.main()
