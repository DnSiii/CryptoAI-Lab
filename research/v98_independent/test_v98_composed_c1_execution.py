"""C1 causal next-open integration smoke tests; synthetic data only."""
import unittest
from research.v98_independent.phase243_native_funding_cashflow import ASSETS
from research.v98_independent.v98_composed_c1 import composed_c1_sleeves
from research.v98_independent.v98_b0_next_open_execution import replay_next_open

class C1ExecutionTests(unittest.TestCase):
    def test_nonzero_composed_exposure_and_cost_stress(self):
        n=2400
        bars={a:[(100*(1+.0003*(k+1))**i,)*4+(1000.,) for i in range(n)]
              for k,a in enumerate(ASSETS)}
        funding={a:{} for a in ASSETS}
        cheap, ledger=replay_next_open(bars,funding,composed_c1_sleeves(),cost_scale=1.)
        severe,_=replay_next_open(bars,funding,composed_c1_sleeves(),cost_scale=4.)
        self.assertEqual(len(ledger),n-1)
        self.assertTrue(any(sum(row["weights_after_fill"].values())>0 for row in ledger))
        self.assertLessEqual(severe["final_equity"],cheap["final_equity"])
        self.assertGreater(cheap["total_turnover"],0)
        self.assertTrue(all(sum(row["weights_after_fill"].values())<=0.75+1e-10 for row in ledger))
    def test_future_close_does_not_change_prior_fills(self):
        n=2400
        bars={a:[(100*(1+.0002*(k+1))**i,)*4+(1000.,) for i in range(n)]
              for k,a in enumerate(ASSETS)}
        funding={a:{} for a in ASSETS}
        _,first=replay_next_open(bars,funding,composed_c1_sleeves())
        altered={a:list(v) for a,v in bars.items()}
        a=ASSETS[0]
        op,hi,lo,cl,vol=altered[a][-1]
        altered[a][-1]=(op,hi,lo,cl*2,vol)
        _,second=replay_next_open(altered,funding,composed_c1_sleeves())
        self.assertEqual([r["weights_after_fill"] for r in first],
                         [r["weights_after_fill"] for r in second])
if __name__=="__main__":
    unittest.main()
