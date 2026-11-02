"""CoinAPI original Sunday full-inventory cross-parser tests (synthetic only)."""
import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research.tools.v99_r106_i1_coinapi_derived_day_bridge import (
    SCHEMA as DAY_SCHEMA, convert,
)
from research.tools.v99_r106_i1_coinapi_full_entry_book_parity import (
    verify_sunday, build,
)

DAY = "2021-12-12"
CLOCK = int(datetime(2021, 12, 13, tzinfo=timezone.utc).timestamp() * 1000)
HEADER = "id_site_coinapi,time_exchange,time_coinapi,ask_px,ask_sx,bid_px,bid_sx\n"


class OriginalSundayFullEntryParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.specs, self.original, self.derived = (
            self.root / name for name in ("specs", "original", "derived"))
        for directory in (self.specs, self.original, self.derived):
            directory.mkdir()
        self.symbols = ("BTC-14JAN22-15000-P", "ETH-14JAN22-3000-P")
        self.spec = self.specs / (DAY + ".json")
        self.write_source(self.symbols[0], [
            ",2021-12-12T23:59:59.0000000,2021-12-12T23:59:59.0000001,0.0050,2,0.0045,3\n"
        ])
        self.write_source(self.symbols[1], [
            ",2021-12-12T23:59:59.0000000,2021-12-12T23:59:59.0000001,0.0070,4,0.0065,5\n"
        ])
        self.update_spec()

    def write_source(self, symbol, lines):
        data = gzip.compress((HEADER + "".join(lines)).encode("utf-8"))
        (self.original / (symbol + ".csv.gz")).write_bytes(data)

    def update_spec(self):
        sources = []
        for symbol in self.symbols:
            path = self.original / (symbol + ".csv.gz")
            sources.append({
                "path": str(path), "symbol": symbol,
                "source_key": ("T-QUOTES/D-20211212/E-DERIBIT/"
                               "IDDI-123+SC-DERIBIT_OPTION_BTC+S-"
                               + symbol + ".csv.gz"),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
        self.spec.write_text(json.dumps({
            "schema": DAY_SCHEMA, "day": DAY, "sources": sources,
        }), encoding="utf-8")

    def derive(self):
        return convert(self.spec, self.derived, fixture=True)

    def check(self):
        return verify_sunday(self.spec, self.original, self.derived, CLOCK)

    def test_two_asset_complete_original_books_equal_derived_parser(self):
        self.derive()
        report = self.check()
        self.assertEqual(report["original_partition_count"], 2)
        self.assertEqual(report["original_rows_scanned"], 2)
        self.assertEqual(len(report["books"]["BTC"]), 1)
        self.assertEqual(len(report["books"]["ETH"]), 1)
        self.assertFalse(report["original_vendor_day_manifest_created"])
        self.assertFalse(report["economic_train_executed"])

    def test_latest_zero_depth_revokes_earlier_executable_btc_book(self):
        self.write_source(self.symbols[0], [
            ",2021-12-12T23:59:59.0000000,2021-12-12T23:59:59.0000001,0.0050,2,0.0045,3\n",
            ",2021-12-12T23:59:59.5000000,2021-12-12T23:59:59.5000001,0,0,0,0\n",
        ])
        self.update_spec()
        self.derive()
        report = self.check()
        self.assertEqual(report["books"]["BTC"], [])
        self.assertEqual(report["invalid"]["BTC"], 1)
        self.assertEqual(len(report["books"]["ETH"]), 1)

    def test_original_mutation_after_derivation_is_rejected(self):
        self.derive()
        self.write_source(self.symbols[0], [
            ",2021-12-12T23:59:59.0000000,2021-12-12T23:59:59.0000001,0.5,2,0.4,3\n"
        ])
        with self.assertRaisesRegex(ValueError, "SOURCE_KEY_DAY_OR_ORIGINAL_SHA_MISMATCH"):
            self.check()

    def test_derived_byte_mutation_is_rejected(self):
        self.derive()
        path = self.derived / (DAY + ".csv.gz")
        path.write_bytes(path.read_bytes() + b"tampered")
        with self.assertRaisesRegex(ValueError, "UNBOUND_COINAPI_DERIVED_SUNDAY"):
            self.check()

    def test_original_book_changed_but_spec_and_derived_stale_is_rejected(self):
        self.derive()
        self.write_source(self.symbols[0], [
            ",2021-12-12T23:59:59.0000000,2021-12-12T23:59:59.0000001,0.0150,2,0.0145,3\n"
        ])
        self.update_spec()
        with self.assertRaisesRegex(ValueError, "UNBOUND_COINAPI_DERIVED_SUNDAY"):
            self.check()

    def test_nonfixed_decision_rejected(self):
        self.derive()
        with self.assertRaisesRegex(ValueError, "NONFIXED_OR_SEALED_COINAPI_ENTRY_DAY"):
            verify_sunday(self.spec, self.original, self.derived, CLOCK + 86400000)

    def test_full_257_contract_inventory_crosses_old_limit_with_exact_tie_order(self):
        # One real-day shaped but SYNTHETIC original file per contract.
        # 257 files must be streamed through multiple bounded merge batches.
        self.symbols = tuple(
            [f"BTC-14JAN22-{15000 + i}-P" for i in range(256)]
            + ["ETH-14JAN22-3000-P"]
        )
        for i, symbol in enumerate(self.symbols):
            # Same arrival tick for multiple contracts tests original-index ties;
            # interleaved tick values exercise the external merge ordering.
            tick = i % 3
            self.write_source(symbol, [
                f",2021-12-12T23:59:59.0000000,"
                f"2021-12-12T23:59:59.000000{tick},0.0050,2,0.0045,3\n"
            ])
        self.update_spec()
        report = self.derive()
        self.assertEqual(report["derived_rows"], 257)
        checked = self.check()
        self.assertEqual(checked["original_partition_count"], 257)
        self.assertEqual(checked["original_rows_scanned"], 257)
        self.assertEqual(len(checked["books"]["BTC"]), 256)
        self.assertEqual(len(checked["books"]["ETH"]), 1)
        with gzip.open(self.derived / (DAY + ".csv.gz"), "rt") as stream:
            rows = list(__import__("csv").DictReader(stream))
        self.assertEqual(len(rows), 257)
        self.assertEqual([int(row["local_timestamp"]) for row in rows],
                         sorted(int(row["local_timestamp"]) for row in rows))
        self.assertFalse(checked["economic_train_executed"])

    def test_4097_contract_spec_rejected_before_any_original_read(self):
        self.spec.write_text(json.dumps({
            "schema": DAY_SCHEMA, "day": DAY,
            "sources": [{}] * 4097,
        }), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "INVALID_DERIVED_DAY_SPECIFICATION"):
            self.derive()
        self.assertEqual(list(self.derived.iterdir()), [])


    def test_missing_license_never_reaches_economics(self):
        with self.assertRaisesRegex(ValueError, "WRITTEN_COINAPI_CHAIN_LICENSE_REQUIRED"):
            build(self.specs, self.original, self.derived, self.root / "signals.json")

    def test_license_string_without_661d_original_chain_is_not_enough(self):
        rights = self.root / "rights.txt"
        rights.write_text("SYNTHETIC ONLY", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_EXTRA_COINAPI_661D_SPEC_GRID"):
            build(self.specs, self.original, self.derived,
                  self.root / "signals.json", license_document=rights)


if __name__ == "__main__":
    unittest.main()
