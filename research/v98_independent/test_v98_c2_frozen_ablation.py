"""C2 frozen ablation structural tests; never access future data."""
import unittest
from research.v98_independent.phase243_native_funding_cashflow import ASSETS
from research.v98_independent.v98_c2_frozen_ablation import SLOTS, removed_sleeve
from research.v98_independent.v98_composed_c2 import composed_c2_sleeves

class FrozenC2AblationTests(unittest.TestCase):
    def test_exact_one_slot_removed_without_redistribution(self):
        history={a:tuple(100*(1+.00015*(k+1)*j) for j in range(1010))
                 for k,a in enumerate(ASSETS)}
        baseline=composed_c2_sleeves()(history)
        for slot in SLOTS:
            index=SLOTS.index(slot)
            altered=removed_sleeve(slot)(history)
            for a in ASSETS:
                self.assertEqual(len(altered[a]),4)
                self.assertEqual(altered[a][index],0.)
                for j in range(4):
                    if j!=index:
                        self.assertEqual(altered[a][j],baseline[a][j])
            self.assertLessEqual(sum(map(sum,altered.values())),sum(map(sum,baseline.values()))+1e-12)
    def test_unknown_slot_fails(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_C2_SLOT"):
            removed_sleeve("regime_router")
if __name__=="__main__":
    unittest.main()
