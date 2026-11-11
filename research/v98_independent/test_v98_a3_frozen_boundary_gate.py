import json
import tempfile
import unittest
from pathlib import Path
from research.v98_independent.v98_a3_frozen_boundary_gate import verify, FROZEN_COMMIT, TRAINING_END_MS

class FrozenBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="v98_independent_")
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "lock.json"
        self.lock = {
            "candidate_commit": FROZEN_COMMIT,
            "status": "A3_REPRODUCIBILITY_LOCK_ONLY_UNVALIDATED",
            "holdout_accessed": False, "independent_validation": False,
            "promotion_eligible": False, "training_end": "2025-12-31T23:00:00Z",
            "source_sha256": {"source": "a"*64},
            "slots_sha256": "b"*64, "price_manifest_sha256": "c"*64,
            "funding_manifest_sha256": "d"*64, "replay_summary_sha256": "e"*64,
            "ledger_sha256": {s: "f"*64 for s in ("1.0","2.0","4.0")}
        }
    def check(self, start=None):
        self.path.write_text(json.dumps(self.lock))
        return verify(self.path, start)
    def test_valid_boundary_does_not_claim_validation(self):
        self.assertFalse(self.check(TRAINING_END_MS+3600000)["independent_validation"])
    def test_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, "OVERLAPS"):
            self.check(TRAINING_END_MS)
    def test_candidate_swap_rejected(self):
        self.lock["candidate_commit"] = "0"*40
        with self.assertRaisesRegex(ValueError, "COMMIT_MISMATCH"):
            self.check()
    def test_false_promotion_rejected(self):
        self.lock["promotion_eligible"] = True
        with self.assertRaisesRegex(ValueError, "FALSE_VALIDATION"):
            self.check()
    def test_missing_cost_scenario_rejected(self):
        del self.lock["ledger_sha256"]["4.0"]
        with self.assertRaisesRegex(ValueError, "COST_SCENARIOS"):
            self.check()

if __name__ == "__main__":
    unittest.main()
