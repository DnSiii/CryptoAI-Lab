#!/usr/bin/env python3
"""V98 Phase1010 synthetic-only cross-run forensic classifier tests."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from phase1010_cross_runner_numeric_forensic import compare
from phase1008_o_frozen_paths import PATHS, FROZEN_O


def build(root, perturb=0.):
    root=Path(root)
    for tag in ("a","b"):
        d=root/tag
        d.mkdir()
        arr={p:np.zeros((18288,4)) for p in PATHS}
        for p in PATHS:
            arr[p][:,0]=.35
        if tag=="b":
            arr["O_full"][1000,0]+=perturb
        np.savez_compressed(d/f"phase1010_o_targets_{tag}.npz",**arr)
        hashes={p:{str(n):"hash" for n in (12,10,8,6)} for p in PATHS}
        rec={"canonical_source_sha256":{"BTCUSDT":"fixed"},
             "frozen_target_sha256":FROZEN_O,"observed_display_hashes":hashes,
             "exact_12g_match_frozen":True,"cpu_model":"synthetic"}
        (d/f"phase1010_o_{tag}.json").write_text(json.dumps(rec))


class CrossRunnerTests(unittest.TestCase):
    def test_exact_arrays_pass(self):
        with tempfile.TemporaryDirectory() as d:
            build(d,0.)
            compare(Path(d))
            r=json.loads((Path(d)/"phase1010_cross_runner_comparison.json").read_text())
            self.assertEqual(r["decision"],"REPRODUCIBLE_EXACT")

    def test_tiny_float_drift_is_quarantined(self):
        with tempfile.TemporaryDirectory() as d:
            build(d,1e-12)
            compare(Path(d))
            r=json.loads((Path(d)/"phase1010_cross_runner_comparison.json").read_text())
            self.assertEqual(r["decision"],"FLOAT_SERIALIZATION_DRIFT_QUARANTINE")
            self.assertFalse(r["economic_clearance"])

    def test_material_drift_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            build(d,.01)
            compare(Path(d))
            r=json.loads((Path(d)/"phase1010_cross_runner_comparison.json").read_text())
            self.assertEqual(r["decision"],"ECONOMIC_TARGET_DRIFT_UNRESOLVED")


if __name__=="__main__":
    unittest.main()
