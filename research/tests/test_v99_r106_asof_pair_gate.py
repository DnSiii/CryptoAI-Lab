"""DATA_ONLY paired market+contract source receipt integrity, all synthetic."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from research.tools import v99_r106_asof_pair_gate as gate
from research.tools import v99_r106_receipt_append as price
from research.tools import v99_r106_terms_append as terms
from research.tests.test_v99_r106_receipt_append import source as mkprices
from research.tests.test_v99_r106_terms_append import prepare as mkterms

class PairedSource(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d=Path(self.tmp.name)
        self.ps=self.d/"p_src";self.ts=self.d/"t_src"
        mkprices(self.ps);mkterms(self.ts)
        self.pdir=self.d/"evidence"/"prices"
        self.tdir=self.d/"evidence"/"terms"
        price.append(self.ps,self.pdir,"38630865416")
        terms.append(self.ts,self.tdir,"38631825856")
        self.p=self.pdir/"2026-10-14T20"
        self.t=self.tdir/"2026-10-14T20"

    def test_realistic_pair_structure_is_not_paper_authorization(self):
        report=gate.audit(self.p,self.t)
        self.assertEqual(report["status"],"TWO_FIRST_PARTY_SOURCE_STREAMS_CONSISTENT_DATA_ONLY")
        self.assertEqual(report["market_source_run"],"38630865416")
        self.assertEqual(report["terms_source_run"],"38631825856")
        self.assertEqual(len(report["assets"]),5)
        self.assertEqual(report["earliest_safe_decision_utc"],"2026-10-14T22:00:00+00:00")
        for flag in ("paper_publication_authorized","promotion_authorized",
                     "exchange_signed_source_time","continuous_forward_pnl_ledger",
                     "native_fee_tiers_attested","funding_settlements_attested",
                     "holdout_accessed"):
            self.assertFalse(report[flag],flag)

    def test_immutable_provenance_hash_rechecked(self):
        f=self.p/"manifest.json"
        f.write_bytes(f.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"archived manifest"):
            gate.audit(self.p,self.t)

    def test_raw_price_tamper_rejected(self):
        f=self.p/"BTC-USDT-SWAP.raw.json"
        f.write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,"tampered"):
            gate.audit(self.p,self.t)

    def test_raw_funding_tamper_rejected(self):
        f=self.t/"funding_ETH-USDT-SWAP.raw.json"
        f.write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,"SHA256"):
            gate.audit(self.p,self.t)

    def test_missing_provenance_fails_closed(self):
        (self.t/"receipt_commit_provenance.json").unlink()
        with self.assertRaisesRegex(ValueError,"provenance missing"):
            gate.audit(self.p,self.t)

    def test_wrong_bucket_rejected(self):
        moved=self.tdir/"2026-10-14T19"
        self.t.rename(moved)
        with self.assertRaisesRegex(ValueError,"wrong UTC bucket"):
            gate.audit(self.p,moved)

    def test_native_contracts_are_not_binance_fees(self):
        r=gate.audit(self.p,self.t)
        self.assertEqual(r["venue"],"OKX_NOT_BINANCE")
        self.assertFalse(r["binance_r106_sleeve_transfer_validated"])
        self.assertEqual(r["assets"]["BTC-USDT-SWAP"]["contract_native_value"],"0.1")

if __name__=="__main__":
    unittest.main()
