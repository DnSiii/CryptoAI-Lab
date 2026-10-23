#!/usr/bin/env python3
"""V98 Phase1017 canonical O economic firewall tests, no historical PnL."""
from __future__ import annotations
import unittest
from unittest.mock import patch
import phase1017_o_canonical_90cell_training as m


class CanonicalEconomicGateTests(unittest.TestCase):
    def test_exact_five_canonical_pins(self):
        self.assertEqual(len(m.FROZEN_CANONICAL_O),5)
        self.assertEqual(len(set(m.FROZEN_CANONICAL_O.values())),5)

    def test_source_failure_prevents_all_target_and_ledger_calls(self):
        with patch.object(m,"source_gate",side_effect=PermissionError("MOCK_BAD_VENDOR_SOURCE")), \
             patch.object(m,"frozen_canonical_o_paths") as frozen, \
             patch.object(m,"complete_matrix_o") as ledger:
            self.assertEqual(m.run(),2)
            frozen.assert_not_called()
            ledger.assert_not_called()

    def test_canonical_hash_failure_prevents_all_economics(self):
        with patch.object(m,"source_gate",return_value={"synthetic":"receipt"}), \
             patch.object(m,"frozen_canonical_o_paths",side_effect=PermissionError("MOCK_CPU_DRIFT")), \
             patch.object(m,"complete_matrix_o") as ledger:
            self.assertEqual(m.run(),2)
            ledger.assert_not_called()


if __name__=="__main__":
    unittest.main()
