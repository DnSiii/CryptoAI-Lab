#!/usr/bin/env python3
"""V98 Phase1009 source firewall and 90-cell dispatch synthetic-only tests."""
from __future__ import annotations
import unittest
from unittest.mock import patch
import numpy as np
import phase1009_o_90cell_training as m


class OTrainingGateTests(unittest.TestCase):
    def test_registry_exact_90(self):
        self.assertEqual(len(m.PATHS),5)
        self.assertEqual(len(m.FEE_TIERS),3)
        self.assertEqual(len(m.ORDERS),2)
        self.assertEqual(len(m.CAPITAL_MODES),3)
        self.assertEqual(len(m.PATHS)*len(m.FEE_TIERS)*len(m.ORDERS)*len(m.CAPITAL_MODES),90)

    def test_fail_closed_source_gate_before_any_ledger(self):
        with patch.object(m,"source_gate",side_effect=PermissionError("MOCK_SOURCE_DENIED")), \
             patch.object(m,"frozen_o_paths") as freeze, \
             patch.object(m,"complete_matrix_o") as economic:
            status=m.run()
            self.assertEqual(status,2)
            freeze.assert_not_called()
            economic.assert_not_called()
        self.assertFalse(m.OUT.read_text().find("BLOCKED_BEFORE_PNL") < 0)

    def test_source_only_failed_target_hash_blocks_economics(self):
        with patch.object(m,"source_gate",return_value={"source":"synthetic"}), \
             patch.object(m,"frozen_o_paths",side_effect=PermissionError("MOCK_HASH_DRIFT")), \
             patch.object(m,"complete_matrix_o") as economic:
            self.assertEqual(m.run(),2)
            economic.assert_not_called()

    def test_all_90_failure_cells_reported_without_cherry_pick(self):
        n=4
        paths={p:np.zeros((n,4)) for p in m.PATHS}
        prices={k:np.ones((n,4)) for k in ("open","high","low","close")}
        other=np.zeros((n,4))
        years=np.full(n,2023)
        with patch.object(m,"simulate_o_with_hourly",return_value={"survived":False,"reason":"SYNTHETIC_BREACH","breach_index":2}) as sim:
            matrix=m.complete_matrix_o(paths,prices,other,other,other,other,years)
        self.assertEqual(sim.call_count,90)
        self.assertEqual(matrix["cells_attempted"],90)
        self.assertEqual(matrix["cells_survived"],0)
        self.assertEqual(len(matrix["failures"]),90)
        self.assertFalse(m.growth_gate_o(matrix)["passed"])

    def test_missing_fold_rejected(self):
        cases={}
        for path in m.PATHS:
            cases[path]={}
            for tier in m.FEE_TIERS:
                cases[path][tier]={}
                for order in m.ORDERS:
                    cases[path][tier][order]={mode:{"survived":True,"folds":{}} for mode in m.CAPITAL_MODES}
        gate=m.growth_gate_o({"cells_attempted":90,"failures":[],"cases":cases})
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["reason"],"incomplete_chronological_folds")


if __name__=="__main__":
    unittest.main()
