import unittest
from research.v98_independent.v98_causal_compound_sizing import size_at_open


class CausalCompoundSizingTest(unittest.TestCase):
    def setUp(self):
        self.w = {"BTCUSDT": .6, "ETHUSDT": -.2}
        self.u = {"BTCUSDT": 2., "ETHUSDT": -1.}
        self.opens = {"BTCUSDT": 110., "ETHUSDT": 90.}
        self.closes = {"BTCUSDT": 100., "ETHUSDT": 100.}
        self.funding = {"BTCUSDT": .01, "ETHUSDT": -.02}

    def test_gap_funding_and_compounding(self):
        r = size_at_open(self.w, self.u, self.opens, self.closes,
                         self.funding, 1000.)
        self.assertAlmostEqual(r["gap_pnl_usd"], 30.)
        self.assertAlmostEqual(r["funding_cashflow_usd"], -4.)
        self.assertAlmostEqual(r["available_equity_usd"], 1026.)
        self.assertAlmostEqual(r["target_notional_usd"]["BTCUSDT"], 615.6)
        self.assertAlmostEqual(r["pre_trade_notional_usd"]["ETHUSDT"], -90.)

    def test_cost_scenarios_must_size_independently(self):
        a = size_at_open(self.w, self.u, self.opens, self.closes, self.funding, 1000.)
        b = size_at_open(self.w, self.u, self.opens, self.closes, self.funding, 900.)
        self.assertNotEqual(a["target_notional_usd"], b["target_notional_usd"])
        self.assertAlmostEqual(a["target_notional_usd"]["BTCUSDT"] -
                               b["target_notional_usd"]["BTCUSDT"], 60.)

    def test_fails_closed(self):
        for weights, equity in (({"BTCUSDT": 1., "ETHUSDT": 1.}, 1000.),
                                (self.w, 0.), (self.w, float("nan"))):
            with self.assertRaises(ValueError):
                size_at_open(weights, self.u, self.opens, self.closes,
                             self.funding, equity)


if __name__ == "__main__":
    unittest.main()
