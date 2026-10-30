"""V98 T canonical transport tests, pre-economic and synthetic only."""
import unittest
from test_phase1081_t_sevenslot_source import synthetic
from phase1081_t_sevenslot_source import compose_t,PATHS
from phase1082_t_authenticated_source import canonical_target

class TestCanonical(unittest.TestCase):
    def test_repeat(self):
        f=synthetic();a=compose_t(*f);b=compose_t(*f)
        self.assertEqual({k:canonical_target(v) for k,v in a.items()},
                         {k:canonical_target(v) for k,v in b.items()})
    def test_serialized(self):
        f=synthetic();a=compose_t(*f)
        self.assertEqual(set(a),set(PATHS))
        self.assertTrue(all(len(canonical_target(v))==64 for v in a.values()))
    def test_bad_caps(self):
        f=synthetic();a=compose_t(*f)['T_full'].copy()
        a.iloc[0,0]=.95
        with self.assertRaisesRegex(ValueError,'CAP'):canonical_target(a)
    def test_nonquantized(self):
        f=synthetic();a=compose_t(*f)['T_full'].copy()
        a.iloc[0,0]=.00000012345
        with self.assertRaisesRegex(ValueError,'NONQUANTIZED'):canonical_target(a)

if __name__=='__main__':unittest.main()
