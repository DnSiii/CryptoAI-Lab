import unittest
from research.v98_independent.v98_b0_hourly_ledger import LedgerState, transition

class B0HourlyLedgerTests(unittest.TestCase):
    def test_flat_equity_no_cost(self):
        s = LedgerState(10000, 10000, {"BTC": 0.0})
        out, audit = transition(s, {"BTC": .1}, {"BTC": .01}, {"BTC": 0.0},
                                fee_rate=.001, slippage_rate=.001)
        self.assertEqual(out.equity, 10000)
        self.assertEqual(audit["turnover"], 0)

    def test_long_funding_and_price(self):
        s = LedgerState(10000, 10000, {"BTC": .5})
        out, audit = transition(s, {"BTC": .1}, {"BTC": .01}, {"BTC": .5},
                                fee_rate=0, slippage_rate=0)
        self.assertAlmostEqual(out.equity, 10450)
        self.assertAlmostEqual(audit["funding_return"], -.005)

    def test_short_receives_positive_funding(self):
        s = LedgerState(10000, 10000, {"BTC": -.5})
        out, audit = transition(s, {"BTC": 0}, {"BTC": .01}, {"BTC": -.5},
                                fee_rate=0, slippage_rate=0)
        self.assertAlmostEqual(out.equity, 10050)

    def test_costs_on_rebalance(self):
        s = LedgerState(10000, 10000, {"BTC": 0.0})
        out, audit = transition(s, {"BTC": 0}, {"BTC": 0}, {"BTC": .4},
                                fee_rate=.001, slippage_rate=.001)
        self.assertAlmostEqual(audit["turnover"], .4)
        self.assertAlmostEqual(out.equity, 9992)

    def test_reject_incomplete_grid(self):
        s = LedgerState(10000, 10000, {"BTC": .1})
        with self.assertRaises(ValueError):
            transition(s, {"BTC": 0}, {}, {"BTC": .1}, fee_rate=0, slippage_rate=0)

if __name__ == "__main__":
    unittest.main()
