"""Synthetic controls only; original TRAIN and independent oracle execute in GitHub CI."""
import math
import unittest
from research.tools.v99_r106_d3_relative_value_train import N, SAFETY, simulate

def fixture(variable=True):
    btc=[100.+.001*i for i in range(N)]
    ratio=[.03*math.sin(i*math.pi/150)+(.06 if i%251==0 else 0.)
           for i in range(N)] if variable else [0.]*N
    eth=[b*math.exp(r) for b,r in zip(btc,ratio)]
    return {"BTC-USDT":btc,"ETH-USDT":eth,
            "BTC-USDT-SWAP":btc[:],"ETH-USDT-SWAP":eth[:]}

class D3Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=fixture()
        cls.report=simulate(cls.source)

    def test_no_promotion_and_sealed_train(self):
        r=self.report
        self.assertEqual(r["original_train_hours"],N)
        self.assertFalse(r["original_price_receipts_verified"])
        for k in SAFETY:self.assertFalse(r[k],k)
        self.assertEqual(len(r["full_hourly_journal"]),N)
        self.assertIsNone(r["full_hourly_journal"][-1]["active"])

    def test_trade_and_scenario_fee_accounting(self):
        self.assertGreater(self.report["event_count"],0)
        for row in self.report["full_hourly_journal"]:
            self.assertAlmostEqual(row["fees"]["supersevere"],
                                   2*row["fees"]["severe"],places=11)
            if row["active"]:
                self.assertLessEqual(row["active"]["q_btc"]*row["active"]["q_eth"],0)
        self.assertLess(self.report["metrics"]["supersevere"]["roi_pre_funding"],
                        self.report["metrics"]["severe"]["roi_pre_funding"])

    def test_lagged_signal_is_independent_of_current_open(self):
        # A current-hour quote shock must not alter its t-1 signal.
        index=721
        z=self.report["full_hourly_journal"][index]["z_lagged"]
        r=[math.log(self.source["ETH-USDT-SWAP"][k]/
                    self.source["BTC-USDT-SWAP"][k]) for k in range(index-720,index)]
        mean=sum(r)/720
        std=math.sqrt(sum((x-mean)**2 for x in r)/720)
        self.assertAlmostEqual(z,(r[-1]-mean)/std,places=11)

    def test_missing_grid_fails_closed(self):
        broken=dict(self.source)
        broken["ETH-USDT-SWAP"]=broken["ETH-USDT-SWAP"][:-1]
        with self.assertRaisesRegex(ValueError,"D3_FULL_FOUR_LEG_TRAIN_GRID_REQUIRED"):
            simulate(broken)

    def test_flat_relative_value_has_no_trades(self):
        r=simulate(fixture(variable=False))
        self.assertEqual(r["event_count"],0)
        self.assertFalse(r["numeric_pass_both"])
        self.assertFalse(r["promotion_authorized"])

if __name__=="__main__":unittest.main()
