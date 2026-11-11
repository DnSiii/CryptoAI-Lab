import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from research.v98_independent.v98_a3_frozen_boundary_gate import FROZEN_COMMIT
from research.v98_independent.v98_a3_material_evidence_gate import verify_material

class MaterialEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="v98_material_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.lock_path = self.root / "lock.json"
        self.map_path = self.root / "mapping.json"
        self.lock = {
            "candidate_commit": FROZEN_COMMIT,
            "status": "A3_REPRODUCIBILITY_LOCK_ONLY_UNVALIDATED",
            "holdout_accessed": False, "independent_validation": False,
            "promotion_eligible": False, "training_end": "2025-12-31T23:00:00Z",
            "source_sha256": {"a": ""}, "slots_sha256": "",
            "price_manifest_sha256": "", "funding_manifest_sha256": "",
            "replay_summary_sha256": "",
            "ledger_sha256": {"1.0": "", "2.0": "", "4.0": ""}
        }
        self.mapping = {}
        for key in ("slots_sha256", "price_manifest_sha256",
                    "funding_manifest_sha256", "replay_summary_sha256"):
            self._write(key, key, b"test:" + key.encode())
        for group in ("source_sha256", "ledger_sha256"):
            for name in self.lock[group]:
                self._write(f"{group}/{name}", (group + "_" + name), name.encode())
        self._save()

    def _write(self, key, filename, data):
        (self.root / filename).write_bytes(data)
        self.mapping[key] = filename
        digest = hashlib.sha256(data).hexdigest()
        if "/" in key:
            group, name = key.split("/", 1)
            self.lock[group][name] = digest
        else:
            self.lock[key] = digest

    def _save(self):
        self.lock_path.write_text(json.dumps(self.lock))
        self.map_path.write_text(json.dumps(self.mapping))

    def check(self):
        return verify_material(self.lock_path, self.root, self.map_path)

    def test_all_material_bytes_verified_without_promotion(self):
        result = self.check()
        self.assertEqual(result["material_hashes_verified"], 8)
        self.assertFalse(result["independent_validation"])

    def test_modified_bytes_rejected(self):
        (self.root / self.mapping["slots_sha256"]).write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA256_MISMATCH"):
            self.check()

    def test_missing_mapping_rejected(self):
        del self.mapping["slots_sha256"]
        self._save()
        with self.assertRaisesRegex(ValueError, "MAPPING_INCOMPLETE"):
            self.check()

    def test_path_escape_rejected(self):
        self.mapping["slots_sha256"] = "../outside"
        self._save()
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.check()

    def test_reused_file_rejected(self):
        self.mapping["slots_sha256"] = self.mapping["price_manifest_sha256"]
        self._save()
        with self.assertRaisesRegex(ValueError, "SHA256_MISMATCH|REUSE"):
            self.check()

if __name__ == "__main__":
    unittest.main()
