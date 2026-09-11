import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class FrozenV16Tests(unittest.TestCase):
    def test_v16_strategy_and_dependencies_match_owner_freeze(self):
        lock=json.loads((ROOT/'config/frozen_v16_manifest.json').read_text())
        self.assertTrue(lock['paper_continues'])
        for name,expected in lock['sha256'].items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,
                                 'V16 is frozen; implement reconstruction changes in V17.')

    def test_v17_has_separate_identity_without_paper_or_live_promotion(self):
        cfg=json.loads((ROOT/'config/candidate_v17_research.json').read_text())
        self.assertEqual(cfg['mode'],'RESEARCH_ONLY')
        self.assertFalse(cfg['real_orders'])
        self.assertFalse(cfg['paper_enabled'])
        self.assertEqual(cfg['approval'],'NOT_APPROVED')
        self.assertAlmostEqual(sum(cfg['comparison']['combined_reference'].values()),1)


if __name__=='__main__': unittest.main()
