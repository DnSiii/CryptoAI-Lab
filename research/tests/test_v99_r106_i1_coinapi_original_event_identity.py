"""Original CoinAPI event-binding adversarial tests; synthetic, NO economics."""
import gzip
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from research.tools.v99_r106_i1_coinapi_derived_day_bridge import SCHEMA as DAY_SCHEMA
from research.tools.v99_r106_i1_coinapi_original_event_identity import audit_requests, audit
from research.tools.v99_r106_i1_native_coin_account_replay import Quote

DAY = "2021-12-09"
SYMBOL = "BTC-30DEC21-15000-P"
HEADER = "id_site_coinapi,time_exchange,time_coinapi,ask_px,ask_sx,bid_px,bid_sx\n"
T0 = int(datetime(2021, 12, 9, tzinfo=timezone.utc).timestamp() * 1000)


def quote(at=T0+1000):
    expiry = int(datetime(2021, 12, 30, 8, tzinfo=timezone.utc).timestamp()*1000)
    return Quote(asset="BTC", symbol=SYMBOL, expiry_ms=expiry,
                 strike_usd=Decimal("15000"),
                 bid_coin=Decimal("0.0045"), ask_coin=Decimal("0.0050"),
                 bid_native_lots=Decimal("3"), ask_native_lots=Decimal("2"),
                 venue_ms=T0, arrival_ms=T0, index_usd=Decimal("50000"))


class CoinapiOriginalEventIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.specs = root/"specs"
        self.original = root/"original"
        self.derived = root/"derived"
        for p in (self.specs, self.original, self.derived):
            p.mkdir()
        self.source = self.original/"BTC.csv.gz"
        self.spec = self.specs/(DAY+".json")
        self.key = ("T-QUOTES/D-20211209/E-DERIBIT/"
                    "IDDI-123+SC-DERIBIT_OPTION_BTC+S-"+SYMBOL+".csv.gz")
        self.write_source([
            ",2021-12-09T00:00:00.0000000,2021-12-09T00:00:00.0000001,0.0050,2,0.0045,3\n"
        ])

    def write_source(self, lines):
        data = gzip.compress((HEADER+"".join(lines)).encode())
        self.source.write_bytes(data)
        self.spec.write_text(json.dumps({
            "schema": DAY_SCHEMA, "day": DAY,
            "sources": [{
                "path": str(self.source), "source_key": self.key,
                "symbol": SYMBOL, "sha256": hashlib.sha256(data).hexdigest(),
            }],
        }), encoding="utf-8")

    def test_matches_exact_original_100ns_receipt(self):
        report = audit_requests(self.specs, self.original,
                                {(T0+1000, "BTC", SYMBOL): quote()})
        self.assertEqual(report["original_event_quote_identities_checked"], 1)
        self.assertEqual(report["original_symbol_day_files_replayed"], 1)
        self.assertFalse(report["economic_train_executed"])
        self.assertFalse(report["promotion_authorized"])

    def test_latest_invalid_original_book_revokes_earlier(self):
        self.write_source([
            ",2021-12-09T00:00:00.0000000,2021-12-09T00:00:00.0000001,0.0050,2,0.0045,3\n",
            ",2021-12-09T00:00:00.5000000,2021-12-09T00:00:00.5000001,0.0000,0,0.0000,0\n",
        ])
        with self.assertRaisesRegex(ValueError, "LATEST_ORIGINAL_RECEIPT_INVALID"):
            audit_requests(self.specs, self.original,
                           {(T0+1000, "BTC", SYMBOL): replace(quote(), venue_ms=T0+500, arrival_ms=T0+500)})

    def test_future_only_source_never_backfills(self):
        self.write_source([
            ",2021-12-09T00:00:01.0000000,2021-12-09T00:00:01.0000001,0.0050,2,0.0045,3\n"
        ])
        with self.assertRaisesRegex(ValueError, "MISSING_ORIGINAL_COINAPI_LAST_ASOF"):
            audit_requests(self.specs, self.original,
                           {(T0+1000, "BTC", SYMBOL): quote()})

    def test_previous_day_last_asof_survives_missing_next_day_contract(self):
        self.write_source([
            ",2021-12-09T23:59:59.9000000,2021-12-09T23:59:59.9000001,0.0050,2,0.0045,3\\n"
        ])
        next_spec = self.specs/"2021-12-10.json"
        next_spec.write_text(json.dumps({
            "schema": DAY_SCHEMA, "day": "2021-12-10", "sources": [],
        }))
        at = T0 + 86_400_000 + 500
        q = replace(quote(at), venue_ms=T0+86_399_900,
                    arrival_ms=T0+86_399_900)
        result = audit_requests(self.specs, self.original,
                                {(at, "BTC", SYMBOL): q})
        self.assertEqual(result["original_event_quote_identities_checked"], 1)
        self.assertEqual(result["original_symbol_day_files_replayed"], 1)

    def test_source_mutation_rejected(self):
        self.source.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "SOURCE_KEY_DAY_OR_ORIGINAL_SHA_MISMATCH"):
            audit_requests(self.specs, self.original,
                           {(T0+1000, "BTC", SYMBOL): quote()})

    def test_missing_contract_source_rejected(self):
        doc = json.loads(self.spec.read_text())
        doc["sources"] = []
        self.spec.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, "MISSING_ORIGINAL_COINAPI_LAST_ASOF"):
            audit_requests(self.specs, self.original,
                           {(T0+1000, "BTC", SYMBOL): quote()})

    def test_nonfixture_full_archive_and_license_are_mandatory(self):
        with self.assertRaisesRegex(ValueError, "WRITTEN_COINAPI_CHAIN_LICENSE_REQUIRED"):
            audit(self.specs, self.original, self.derived, {}, license_document=None)
        rights = self.specs.parent/"license.txt"
        rights.write_text("SYNTHETIC TEST ONLY, NOT A REAL LICENSE")
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_EXTRA_COINAPI_661D_SPEC_GRID"):
            audit(self.specs, self.original, self.derived, {}, license_document=rights)


if __name__ == "__main__":
    unittest.main()
