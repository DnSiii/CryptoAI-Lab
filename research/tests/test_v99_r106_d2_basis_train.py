"""D2 synthetic-only invariants; real original TRAIN and independent oracle run in CI."""
import math
import unittest
from research.tools.v99_r106_d2_basis_train import HOURS, simulate, NO_PROMOTION

def synthetic(*, oscillate=True):
    btc=[100.+.003*i for i in range(HOURS)]
    eth=[50.+.001*i for i in range(HOURS)]
    if oscillate:
        btc_basis=[.01+.001*math.sin(i*math.pi/36)+(.015 if i%101==0 else 0) for i in range(HOURS)]
        eth_basis=[.009+.001*math.sin(i*math.pi/43)+(.015 if i%113==0 else 0) for i in range(HOURS)]
    else:
        btc_basis=[.01]*HOURS
        eth_basis=[.01]*HOURS
    return {"BTC-USDT":btc,"BTC-USDT-SWAP":[x*(1+b) for x,b in zip(btc,btc_basis)],
            "ETH-USDT":eth,"ETH-USDT-SWAP":[x*(1+b) for x,b in zip(eth,eth_basis)]}

class D2Adversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=synthetic()
        cls.report=simulate(cls.data,source_verified=False)

    def test_no_forged_certification(self):
        for flag in NO_PROMOTION:
            self.assertFalse(self.report[flag],flag)
        self.assertFalse(self.report["source_verified"])
        self.assertEqual(self.report["original_train_hours"],HOURS)

    def test_independent_cost_paths_share_events_and_pnl(self):
        self.assertGreater(self.report["event_count"],0)
        for row in self.report["full_hourly_journal"]:
            self.assertGreaterEqual(row["fees"]["supersevere"],row["fees"]["severe"])
            self.assertAlmostEqual(row["fees"]["supersevere"],
                                   2*row["fees"]["severe"],places=12)
            self.assertLessEqual(len(row["active"]),2)
        self.assertLess(self.report["metrics"]["supersevere"]["roi_pre_funding"],
                        self.report["metrics"]["severe"]["roi_pre_funding"])

    def test_exact_train_grid_and_terminal_flatten(self):
        rows=self.report["full_hourly_journal"]
        self.assertEqual(len(rows),HOURS)
        self.assertEqual(rows[-1]["active"],{})
        self.assertEqual(rows[0]["events"],[])
        self.assertTrue(all(r["fold"] in (1,2,3,4,5) for r in rows))

    def test_noncausal_input_rejected(self):
        bad=dict(self.data)
        bad["BTC-USDT"]=bad["BTC-USDT"][:-1]
        with self.assertRaisesRegex(ValueError,"D2_FULL_TRAIN_PRICE_GRID_REQUIRED"):
            simulate(bad)

    def test_no_variance_means_no_fabricated_trades(self):
        report=simulate(synthetic(oscillate=False))
        self.assertEqual(report["event_count"],0)
        self.assertFalse(report["numeric_pass_both"])
        self.assertFalse(report["promotion_authorized"])

if __name__=="__main__":
    unittest.main()
