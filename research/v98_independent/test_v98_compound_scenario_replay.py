import unittest
from research.v98_independent.v98_compound_scenario_replay import replay

ASSETS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")
T = 1672531200000
H = 3600000

def fixture():
    bars = {a: [(100., 110., 90., 110., 1.), (120., 125., 115., 120., 1.),
                (120., 125., 115., 120., 1.)] for a in ASSETS}
    funding = {a: {} for a in ASSETS}
    decisions = [{"hour_open_ms": T+i*H, "decision_time_ms": T+(i-1)*H,
                  "weights": {a: (.5 if a == "BTCUSDT" else 0.) for a in ASSETS}}
                 for i in range(3)]
    return decisions, bars, funding

class CompoundReplayTest(unittest.TestCase):
    def test_compounding_and_independent_costs(self):
        d,b,f = fixture()
        r = replay(d,b,f,first_hour_ms=T,initial_equity_usd=1000.,
                   fee_bps=10.,slippage_bps=0.)
        self.assertEqual(set(r), {"1.0","2.0","3.0"})
        self.assertEqual([len(x) for x in r.values()], [3,3,3])
        self.assertGreater(r["1.0"][0]["ending_equity_usd"], 1049.)
        self.assertGreater(r["1.0"][1]["gap_pnl_usd"], 40.)
        self.assertGreater(r["1.0"][-1]["ending_equity_usd"],r["3.0"][-1]["ending_equity_usd"])
        self.assertNotEqual(r["1.0"][1]["turnover_usd"],r["3.0"][1]["turnover_usd"])

    def test_funding_pretrade_only(self):
        d,b,f = fixture()
        f["BTCUSDT"][T+H] = .01
        r = replay(d,b,f,first_hour_ms=T,initial_equity_usd=1000.,
                   fee_bps=0.,slippage_bps=0.,multipliers=(1.,))
        self.assertEqual(r["1.0"][0]["funding_cashflow_usd"],0.)
        self.assertLess(r["1.0"][1]["funding_cashflow_usd"],0.)

    def test_reject_future_decision_and_partial_grid(self):
        d,b,f = fixture()
        d[1]["decision_time_ms"] = T+H
        with self.assertRaises(ValueError):
            replay(d,b,f,first_hour_ms=T,initial_equity_usd=1000.,fee_bps=0.,slippage_bps=0.)
        d,b,f = fixture()
        del b["SOLUSDT"]
        with self.assertRaises(ValueError):
            replay(d,b,f,first_hour_ms=T,initial_equity_usd=1000.,fee_bps=0.,slippage_bps=0.)

if __name__ == "__main__":
    unittest.main()
