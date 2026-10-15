"""Adversarial offline GitHub receipt provenance tests (no network)."""
import unittest
from datetime import datetime, timedelta, timezone
from research.tools import v99_r106_durable_run_attestation as guard


class TestProvenance(unittest.TestCase):
    def setUp(self):
        self.bucket = "2026-10-15T13"
        self.report = {
            "schema": "V99_R106_DURABLE_PAIRED_SOURCE_CHAIN_V1",
            "economic_trials": 0,
            "promotion_authorized": False,
            "paper_publication_authorized": False,
            "market_recorded_run_ids": {self.bucket: "38744649527"},
            "terms_recorded_run_ids": {self.bucket: "38744809092"},
        }
        self.repo = "DnSiii/CryptoAI-Lab"

    def stub(self, path):
        run_id = int(path.split("/")[5])
        if path.endswith("/artifacts?per_page=100"):
            prefix = "v99-r106-okx-firstparty-" if run_id == 38744649527 else "v99-r106-okx-terms-"
            return {"artifacts": [{"name": prefix + str(run_id), "id": run_id,
                                   "expired": False, "workflow_run": {"id": run_id}}]}
        return {"id": run_id, "status": "completed", "conclusion": "success",
                "event": "schedule", "repository": {"full_name": self.repo},
                "created_at": "2026-10-15T13:27:00Z",
                "updated_at": "2026-10-15T13:45:00Z",
                "html_url": "https://github.com/DnSiii/CryptoAI-Lab/actions/runs/" + str(run_id)}

    def test_validated_metadata_does_not_promote_strategy(self):
        result = guard.attest(self.report, self.repo, self.stub)
        self.assertEqual(result["verified"], 2)
        self.assertFalse(result["authenticates_exchange_signed_source_or_first_seen"])
        self.assertFalse(result["promotion_authorized"])
        self.assertEqual(result["economic_trials"], 0)

    def test_invalid_run_fails(self):
        def invalid(path):
            j = self.stub(path)
            if "artifacts?" not in path:
                j["conclusion"] = "failure"
            return j
        with self.assertRaisesRegex(ValueError, "unverified_github_action_run"):
            guard.attest(self.report, self.repo, invalid)

    def test_expired_artifact_fails(self):
        def expired(path):
            j = self.stub(path)
            if path.endswith("artifacts?per_page=100"):
                j["artifacts"][0]["expired"] = True
            return j
        with self.assertRaisesRegex(ValueError, "missing_or_ambiguous"):
            guard.attest(self.report, self.repo, expired)

    def test_run_outside_bucket_rejected(self):
        def old(path):
            j = self.stub(path)
            if "artifacts?" not in path:
                j["created_at"] = "2026-10-10T00:00:00Z"
                j["updated_at"] = "2026-10-10T00:01:00Z"
            return j
        with self.assertRaisesRegex(ValueError, "run_outside_claimed_capture_hour"):
            guard.attest(self.report, self.repo, old)

    def test_unauthorized_report_rejected(self):
        self.report["promotion_authorized"] = True
        with self.assertRaisesRegex(ValueError, "non_data_only_chain"):
            guard.attest(self.report, self.repo, self.stub)


if __name__ == "__main__":
    unittest.main()
