"""Negative controls for a possible alternative archive; no market data or ROI."""
import gzip
import tempfile
import unittest
from pathlib import Path
from research.tools.v99_r106_i1_coinapi_quote_intake import inspect, microseconds

HEADER = "id_site_coinapi;time_exchange;time_coinapi;ask_px;ask_sx;bid_px;bid_sx\n"
ROW = ";2022-01-01T00:00:00.1140000;2022-01-01T00:00:00.2350440;0.0050;2;0.0045;3\n"

class TestCoinAPIIntake(unittest.TestCase):
    def test_strict_microsecond_precision(self):
        self.assertEqual(microseconds("2022-01-01T00:00:00.1140000"),1640995200114000)
        with self.assertRaisesRegex(ValueError,"SUBMICROSECOND"):
            microseconds("2022-01-01T00:00:00.1140001")
    def case(self, rows, *, licensed=True, venue="DERIBIT", symbol="BTC-30DEC22-15000-P"):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.csv.gz"
            p.write_bytes(gzip.compress((HEADER+rows).encode()))
            return inspect(p, venue=venue, symbol=symbol, licensed=licensed)
    def test_qualified_format_not_certification(self):
        r=self.case(ROW)
        self.assertEqual(r["rows"],1)
        self.assertFalse(r["economic_train_executed"])
        self.assertFalse(r["complete_21_45d_lifecycles_certified"])
        self.assertFalse(r["source_quote_size_units_certified_as_native_contracts"])
    def test_unlicensed_rejected(self):
        with self.assertRaisesRegex(ValueError,"LICENSE"):
            self.case(ROW, licensed=False)
    def test_wrong_venue_rejected(self):
        with self.assertRaisesRegex(ValueError,"SYMBOL"):
            self.case(ROW, venue="OKX")
    def test_arrival_before_exchange_rejected(self):
        with self.assertRaisesRegex(ValueError,"NONCAUSAL"):
            self.case(ROW.replace("00:00:00.2350440","00:00:00.1000000"))
    def test_bad_depth_rejected(self):
        with self.assertRaisesRegex(ValueError,"NONPOSITIVE"):
            self.case(ROW.replace(";0.0045;3",";0.0045;0"))
    def test_locked_book_rejected(self):
        with self.assertRaisesRegex(ValueError,"CROSSED"):
            self.case(ROW.replace(";0.0045;3",";0.0050;3"))
    def test_reordered_arrival_rejected(self):
        with self.assertRaisesRegex(ValueError,"OUT_OF_ORDER"):
            self.case(ROW+ROW.replace("00:00:00.2350440","00:00:00.2000000"))
    def test_empty_rejected(self):
        with self.assertRaisesRegex(ValueError,"EMPTY"):
            self.case("")
if __name__=="__main__": unittest.main()
