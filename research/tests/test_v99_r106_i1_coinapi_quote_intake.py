"""Negative controls for a possible alternative archive; no market data or ROI."""
import gzip
import hashlib
import io
from contextlib import redirect_stdout
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from research.tools.v99_r106_i1_coinapi_quote_intake import inspect, microseconds, main

HEADER = "id_site_coinapi;time_exchange;time_coinapi;ask_px;ask_sx;bid_px;bid_sx\n"
ROW = ";2022-01-01T00:00:00.1140000;2022-01-01T00:00:00.2350440;0.0050;2;0.0045;3\n"
KEY = "T-QUOTES/D-20220101/E-DERIBIT/IDDI-123+SC-DERIBIT_OPTION_BTC+S-BTC-30DEC22-15000-P.csv.gz"

class TestCoinAPIIntake(unittest.TestCase):
    def test_strict_microsecond_precision(self):
        self.assertEqual(microseconds("2022-01-01T00:00:00.1140000"),1640995200114000)
        with self.assertRaisesRegex(ValueError,"SUBMICROSECOND"):
            microseconds("2022-01-01T00:00:00.1140001")
    def case(self, rows, *, licensed=True, venue="DERIBIT", symbol="BTC-30DEC22-15000-P", source_key=KEY):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.csv.gz"
            p.write_bytes(gzip.compress((HEADER+rows).encode()))
            return inspect(p, venue=venue, symbol=symbol, licensed=licensed, source_key=source_key)
    def test_large_original_is_streamed_and_original_hash_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"large.csv.gz"
            payload = (HEADER + ROW*25000).encode("utf-8")
            compressed = gzip.compress(payload)
            path.write_bytes(compressed)
            # Forbid the old memory-amplifying whole-file operations.
            with patch.object(Path, "read_bytes", side_effect=AssertionError("whole-file read")):
                with patch("gzip.decompress", side_effect=AssertionError("whole-file decompress")):
                    result = inspect(path, venue="DERIBIT",
                                     symbol="BTC-30DEC22-15000-P",
                                     licensed=True, source_key=KEY)
            self.assertEqual(result["rows"], 25000)
            self.assertEqual(result["original_sha256"], hashlib.sha256(compressed).hexdigest())
            self.assertEqual(result["original_bytes"], len(compressed))
            self.assertFalse(result["economic_train_executed"])

    def test_truncated_original_stream_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"truncated.csv.gz"
            path.write_bytes(gzip.compress((HEADER+ROW).encode())[:-4])
            with self.assertRaisesRegex(ValueError, "INVALID_ORIGINAL_GZIP"):
                inspect(path, venue="DERIBIT", symbol="BTC-30DEC22-15000-P",
                        licensed=True, source_key=KEY)

    def test_changed_original_during_stream_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"changed.csv.gz"
            path.write_bytes(gzip.compress((HEADER+ROW).encode()))
            with patch("research.tools.v99_r106_i1_coinapi_quote_intake._compressed_digest",
                       side_effect=[("a"*64, 123), ("b"*64, 123)]):
                with self.assertRaisesRegex(ValueError, "ORIGINAL_FILE_CHANGED_DURING_INTAKE"):
                    inspect(path, venue="DERIBIT", symbol="BTC-30DEC22-15000-P",
                            licensed=True, source_key=KEY)

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
    def test_original_site_uuid_allowed_not_instrument_identity(self):
        r=self.case(ROW.replace(";", "550e8400-e29b-41d4-a716-446655440000;",1))
        self.assertEqual(r["rows"],1)
        self.assertFalse(r["source_key_independently_verified"])
    def test_invalid_site_uuid_rejected(self):
        with self.assertRaisesRegex(ValueError,"RECEIVING_SITE_UUID"):
            self.case(ROW.replace(";", "not-a-uuid;",1))
    def test_wrong_original_key_symbol_rejected(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_KEY_DERIBIT_SYMBOL"):
            self.case(ROW,source_key=KEY.replace("S-BTC-", "S-ETH-"))
    def test_wrong_original_key_venue_rejected(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_KEY_DERIBIT_SYMBOL"):
            self.case(ROW,source_key=KEY.replace("E-DERIBIT","E-BINANCE"))
    def test_original_key_date_must_match_arrival(self):
        with self.assertRaisesRegex(ValueError,"PARTITION_TIMESTAMP"):
            self.case(ROW,source_key=KEY.replace("D-20220101","D-20220102"))
    def test_original_key_must_not_open_validation(self):
        with self.assertRaisesRegex(ValueError,"SEALED_TRAIN"):
            self.case(ROW,source_key=KEY.replace("D-20220101","D-20231001"))
    def test_real_cli_document_digest_and_source_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            quote=root/"source.csv.gz"
            quote.write_bytes(gzip.compress((HEADER+ROW).encode()))
            license_doc=root/"license.txt"
            license_doc.write_text("synthetic fixture rights, NOT a real license")
            digest=hashlib.sha256(license_doc.read_bytes()).hexdigest()
            args=[str(quote),"DERIBIT","BTC-30DEC22-15000-P",
                  "--source-key",KEY,"--license-document",str(license_doc),
                  "--license-sha256",digest]
            with redirect_stdout(io.StringIO()):
                result=main(args)
            self.assertEqual(result["rows"],1)
            self.assertFalse(result["license_document_independently_verified"])
            with self.assertRaisesRegex(ValueError,"LICENSE_DOCUMENT"):
                with redirect_stdout(io.StringIO()):
                    main(args[:-1]+["0"*64])

if __name__=="__main__": unittest.main()
