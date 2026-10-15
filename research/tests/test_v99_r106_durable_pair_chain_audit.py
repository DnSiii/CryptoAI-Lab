"""Synthetic cases; live read-only audit runs separately against original GitHub receipts."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research.tools import v99_r106_durable_pair_chain_audit as audit


def fake(*hours):
    return {value: {"verified": {"time": value}, "claimed_run_id": str(10000000 + i)}
            for i, value in enumerate(hours)}


class TestDurableSourceChain(unittest.TestCase):
    def test_market_only_and_terms_only_are_not_filled_in(self):
        report = audit.summarize(
            fake("2026-10-15T13", "2026-10-15T18"),
            fake("2026-10-15T13", "2026-10-15T17"))
        self.assertEqual(report["paired_hours"], 1)
        self.assertEqual(report["total_utc_hours"], 6)
        self.assertEqual(len(report["missing_paired_hours"]), 5)
        self.assertEqual(report["market_only_hours"], ["2026-10-15T18"])
        self.assertEqual(report["terms_only_hours"], ["2026-10-15T17"])
        self.assertEqual(report["verified_adjacent_links"], 0)
        self.assertFalse(report["paper_publication_authorized"])

    def test_clean_adjacent_pair_never_promotes_economic_model(self):
        good = {"status": "SOURCE_CONTINUITY_OBSERVED_ONLY",
                "issues": [], "revised_confirmed_hours": 0, "overlap_observations": 20}
        market = fake("2026-10-15T13", "2026-10-15T14")
        terms = fake("2026-10-15T13", "2026-10-15T14")
        with patch.object(audit.continuity, "evaluate", return_value=good):
            report = audit.summarize(market, terms)
        self.assertEqual(report["verified_adjacent_links"], 1)
        self.assertEqual(report["status"], "DATA_ONLY_SOURCE_CONTINUITY_OBSERVED_ONLY")
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["holdout_accessed"])
        self.assertEqual(report["economic_trials"], 0)

    def test_revision_never_counts_as_valid_link(self):
        revised = {"status": "DATA_ONLY_HOLD_CONTINUITY",
                   "issues": ["CONFIRMED_SOURCE_REVISIONS:5"],
                   "revised_confirmed_hours": 5, "overlap_observations": 20}
        market = fake("2026-10-15T13", "2026-10-15T14")
        terms = fake("2026-10-15T13", "2026-10-15T14")
        with patch.object(audit.continuity, "evaluate", return_value=revised):
            report = audit.summarize(market, terms)
        self.assertEqual(report["verified_adjacent_links"], 0)
        self.assertEqual(report["adjacent_audits"][0]["revisions"], 5)
        self.assertEqual(report["status"], "DATA_ONLY_HOLD_NO_CONSECUTIVE_PAIRS")

    def test_bucket_naming_and_missing_chain_fail_closed(self):
        for bucket in ("2026-10-15T24", "2026-10-15T5", "2026-02-30T10", "../x"):
            with self.subTest(bucket=bucket):
                with self.assertRaises(ValueError):
                    audit.parse_bucket(bucket)
        with self.assertRaisesRegex(ValueError, "empty_durable"):
            audit.summarize({}, {})

    def test_extraneous_file_rejected_before_source_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "manifest.json").write_text("{}")
            (folder / audit.PROOF).write_text("{}")
            (folder / "unapproved.txt").write_text("x")
            with self.assertRaisesRegex(ValueError, "missing_or_extra"):
                audit.verify_original(folder, ("manifest.json",), lambda _: {})

    def test_manifest_provenance_tampering_fails_closed(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "manifest.json").write_text("{}")
            manifest = {"last_received_utc": "2026-10-15T13:40:00+00:00",
                        "economic_trials": 0, "holdout_accessed": False}
            (folder / audit.PROOF).write_text(json.dumps({
                "run_id": "38744649527", "acquired_utc": manifest["last_received_utc"],
                "immutable_bucket_utc": "2026-10-15T13",
                "manifest_sha256": "0" * 64, "paper_or_model_changes_allowed": False}))
            with self.assertRaisesRegex(ValueError, "provenance_digest"):
                audit.verify_proof(folder, manifest, "2026-10-15T13", "market")

    def test_bucket_label_alone_cannot_pass_crosssource_gate(self):
        original={"status":"DATA_ONLY_HOLD","promotion_authorized":False,
                  "paper_publication_authorized":False,"holdout_accessed":False,
                  "economic_trials":0,"assets":{}}
        with patch.object(audit.pair_gate, "audit", return_value=original):
            with self.assertRaisesRegex(ValueError, "crosssource_gate_failed"):
                audit.verify_aligned_source_pairs(Path("/sample"),
                    fake("2026-10-15T20"), fake("2026-10-15T20"))

    def test_native_source_pair_requires_no_trading_claims(self):
        original={
            "status":"TWO_FIRST_PARTY_SOURCE_STREAMS_CONSISTENT_DATA_ONLY",
            "promotion_authorized":False,"paper_publication_authorized":False,
            "holdout_accessed":False,"economic_trials":0,
            "market_source_run":"38804778835","terms_source_run":"38804778835",
            "earliest_safe_decision_utc":"2026-10-15T22:00:00+00:00",
            "assets":{key:{} for key in audit.okx.INSTS},
        }
        with patch.object(audit.pair_gate, "audit", return_value=original):
            pairs=audit.verify_aligned_source_pairs(Path("/sample"),
                fake("2026-10-15T20"), fake("2026-10-15T20"))
        self.assertEqual(len(pairs),1)
        self.assertFalse(pairs["2026-10-15T20"]["funding_cashflows_proven"])



if __name__ == "__main__":
    unittest.main()
