import unittest
from research.v98_independent.v98_b0_next_open_execution import replay_next_open
from research.v98_independent.v98_b0_stream_integration import ASSETS

def bars(n=4, shock=1):
    return {a:[(100. if i<2 else shock, 100., 100., 100., 0.)
               for i in range(n)] for a in ASSETS}

def warmed_bars(n=2190):
    # Nonzero rolling volatility is required before the preregistered router
    # permits any exposure (13 x 168 completed returns + initial close).
    return {a:[(100. + (i % 2), 100., 100., 100. + (i % 2), 0.)
               for i in range(n)] for a in ASSETS}

class NextOpenTests(unittest.TestCase):
    def test_zero_signal_no_pnl(self):
        result, entries = replay_next_open(bars(),{a:{} for a in ASSETS},
            lambda h:{a:(0.,0.,0.,0.) for a in ASSETS})
        self.assertEqual(result["final_equity"],10000.)
        self.assertEqual(len(entries),3)

    def test_no_current_close_leak(self):
        observed=[]
        def spy(h):
            observed.append(len(h["BTCUSDT"]))
            return {a:(0.,0.,0.,0.) for a in ASSETS}
        replay_next_open(bars(),{a:{} for a in ASSETS},spy)
        self.assertEqual(observed,[1,2,3])

    def test_costs_nonzero_when_rebalanced(self):
        def sleeve(h):
            return {a:(.2,0.,0.,0.) for a in ASSETS}
        result, entries=replay_next_open(warmed_bars(),{a:{} for a in ASSETS},sleeve)
        self.assertTrue(any(e["cost_return"]>0 for e in entries))
        baseline,_=replay_next_open(warmed_bars(),{a:{} for a in ASSETS},sleeve, cost_scale=0.)
        self.assertLess(result["final_equity"],baseline["final_equity"])

    def test_final_mark_insolvency_fails_closed(self):
        # No fill after the final open; an adverse final close must not
        # produce a negative equity curve disguised as a valid backtest.
        def sleeve(h):
            return {a:(1.,0.,0.,0.) for a in ASSETS}
        series = warmed_bars(2190)
        for a in ASSETS:
            op, hi, lo, _, vol = series[a][-1]
            series[a][-1] = (op, hi, lo, float("nan"), vol)
        # A nonfinite final close must fail closed, not produce NaN PnL.
        with self.assertRaisesRegex(ValueError, "INSOLVENT_FINAL_MARK"):
            replay_next_open(series, {a:{} for a in ASSETS}, sleeve)

    def test_reject_invalid_costs_and_funding(self):
        base = bars()
        funding = {a:{} for a in ASSETS}
        zero = lambda h:{a:(0.,0.,0.,0.) for a in ASSETS}
        for kwargs in ({"fee_rate":-.001}, {"slippage_rate":float("nan")},
                       {"cost_scale":float("inf")}, {"initial_equity":float("nan")}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, "INVALID_ACCOUNT"):
                replay_next_open(base, funding, zero, **kwargs)
        invalid = {a:{} for a in ASSETS}
        invalid["BTCUSDT"][1] = float("nan")
        with self.assertRaisesRegex(ValueError, "INVALID_NATIVE_FUNDING"):
            replay_next_open(base, invalid, zero)
        with self.assertRaisesRegex(ValueError, "INVALID_CLEAN4_ASSETS"):
            replay_next_open(base, {"BTCUSDT":{}}, zero)

    def test_position_ledger_and_pre_fill_equity(self):
        sleeve = lambda h:{a:(.2,0.,0.,0.) for a in ASSETS}
        _, entries = replay_next_open(warmed_bars(), {a:{} for a in ASSETS}, sleeve)
        self.assertEqual(len(entries), 2189)
        for e in entries:
            self.assertEqual(set(e["weights_before_fill"]), set(ASSETS))
            self.assertEqual(set(e["weights_after_fill"]), set(ASSETS))
            self.assertAlmostEqual(e["equity"], e["pre_fill_equity"]*(1-e["cost_return"]))
            self.assertAlmostEqual(e["turnover"], sum(abs(e["weights_after_fill"][a]-e["weights_before_fill"][a]) for a in ASSETS))

    def test_funding_signed(self):
        def sleeve(h):
            return {a:(.2,0.,0.,0.) for a in ASSETS}
        result,_=replay_next_open(warmed_bars(),{a:{2187:.01} for a in ASSETS},sleeve)
        baseline,_=replay_next_open(warmed_bars(),{a:{} for a in ASSETS},sleeve)
        self.assertLess(result["final_equity"],baseline["final_equity"])

if __name__=="__main__":
    unittest.main()
