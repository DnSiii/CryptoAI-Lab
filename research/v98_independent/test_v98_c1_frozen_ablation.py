"""Frozen C1 ablation contract: zero only one slot, never renormalize."""
import unittest
from research.v98_independent.phase243_native_funding_cashflow import ASSETS
from research.v98_independent.v98_composed_c1 import composed_c1_sleeves
from research.v98_independent.v98_c1_frozen_ablation import SLOTS, removed_sleeve

class FrozenC1AblationTests(unittest.TestCase):
    def test_slot_removal_is_exact_and_does_not_reallocate(self):
        history={a:tuple(100*(1+0.0002*(j+1))**i for i in range(721))
                 for j,a in enumerate(ASSETS)}
        for slot in SLOTS:
            original=composed_c1_sleeves()(history)
            altered=removed_sleeve(slot)(history)
            index=SLOTS.index(slot)
            for a in ASSETS:
                self.assertEqual(len(altered[a]),4)
                for j in range(4):
                    self.assertEqual(altered[a][j],0. if j==index else original[a][j])
    def test_invalid_slot_rejected(self):
        with self.assertRaises(ValueError):
            removed_sleeve("unknown")
    def test_deterministic_rebalance_and_no_lookahead(self):
        history={a:tuple(100*(1+0.0002*(j+1))**i for i in range(800))
                 for j,a in enumerate(ASSETS)}
        for slot in SLOTS:
            f=removed_sleeve(slot)
            before=f({a:history[a][:721] for a in ASSETS})
            after=f({a:history[a][:722] for a in ASSETS})
            self.assertEqual(before,after)

if __name__=="__main__":
    unittest.main()
