"""V98 C2 deterministic causal/portfolio invariants, no future data."""
import unittest
from research.v98_independent.v98_composed_c2 import composed_c2_sleeves
from research.v98_independent.phase243_native_funding_cashflow import ASSETS

class C2Tests(unittest.TestCase):
    def history(self,n=1100):
        return {a:tuple(100*(1+.00015*(k+1)*j) for j in range(n))
                for k,a in enumerate(ASSETS)}
    def test_prefix_and_budget(self):
        h=self.history()
        f=composed_c2_sleeves()
        g=composed_c2_sleeves()
        for n in range(1,1101):
            p={a:h[a][:n] for a in ASSETS}
            x=f(p)
            self.assertEqual(x,g(p))
            self.assertEqual(set(x),set(ASSETS))
            self.assertTrue(all(len(v)==4 and all(0<=z<=.42 for z in v) for v in x.values()))
            self.assertLessEqual(sum(map(sum,x.values())),.75+1e-10)
    def test_invalid(self):
        with self.assertRaisesRegex(ValueError,"C2_CLEAN4_ONLY"):
            composed_c2_sleeves()({"BTCUSDT":(1.,)})
    def test_prefix_future_independence(self):
        h=self.history()
        f=composed_c2_sleeves()
        for n in (673,841,1009):
            prefix={a:h[a][:n] for a in ASSETS}
            expected=f(prefix)
            altered={a:h[a][:n]+(1e9,) for a in ASSETS}
            other=composed_c2_sleeves()
            self.assertEqual(expected,other(prefix))
            other(altered)
            self.assertEqual(expected,f(prefix))
if __name__=="__main__":
    unittest.main()
