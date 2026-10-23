#!/usr/bin/env python3
"""S freeze enforcement and economic grid shape, no vendor or PnL."""
import unittest
from unittest.mock import patch
from pathlib import Path
from phase1075_s_training_path import verify_freeze,FROZEN_FILES,run
from phase1074_s_funded_ledger import FEE_TIERS,ORDERS,CAPITAL_MODES
from phase1069_s_sevenslot_source import PATHS
class STrainingGate(unittest.TestCase):
    def test_five_paths_90_cells(self):self.assertEqual(len(PATHS)*len(FEE_TIERS)*len(ORDERS)*len(CAPITAL_MODES),90)
    def test_freeze_requires_manifest(self):
        with patch('phase1075_s_training_path.MANIFEST',Path('/tmp/nonexistent_s_manifest_v98_2026.json')):
            with self.assertRaises(FileNotFoundError):verify_freeze()
    def test_unknown_path_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNKNOWN'):run('S_wrong')
    def test_freeze_files(self):self.assertEqual(len(FROZEN_FILES),7)
if __name__=='__main__':unittest.main()
