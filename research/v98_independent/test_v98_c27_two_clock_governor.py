"""Deterministic C27 causal governor checks; not an economic backtest."""
import unittest
from .v98_c27_two_clock_governor import (
    planned_trim, queue_sell_fractions, execute_queued_units,
    two_clock_step, breach,
)

class C27TwoClockTests(unittest.TestCase):
    def test_sell_only_and_both_caps(self):
        w={"BTCUSDT":.4525,"ETHUSDT":.30,"BNBUSDT":.20,"SOLUSDT":.10}
        t=planned_trim(w)
        self.assertFalse(breach(t))
        self.assertTrue(all(0<=t[a]<=w[a] for a in w))
        self.assertAlmostEqual(sum(t.values()),.90)

    def test_no_same_open_lookahead(self):
        w={"BTCUSDT":.4525,"ETHUSDT":.2,"BNBUSDT":.1,"SOLUSDT":.1}
        first=two_clock_step(w,{a:0. for a in w})
        self.assertEqual(first["post_fill_pre_cost_weights"],w)
        self.assertTrue(first["post_fill_cap_breach"])
        self.assertTrue(first["needs_next_open_trim"])
        second=two_clock_step(w,first["next_open_sell_fractions"])
        self.assertFalse(second["post_fill_cap_breach"])

    def test_gap_can_break_cap(self):
        w={"BTCUSDT":.4525,"ETHUSDT":.2,"BNBUSDT":.1,"SOLUSDT":.1}
        q=queue_sell_fractions(w)
        gap={"BTCUSDT":.70,"ETHUSDT":.10,"BNBUSDT":.05,"SOLUSDT":.05}
        filled=execute_queued_units(gap,q)
        self.assertTrue(breach(filled),
                        "A prior-open queue cannot guarantee cap across gaps")

    def test_no_unplanned_buy(self):
        w={"BTCUSDT":.25,"ETHUSDT":.20,"BNBUSDT":.10,"SOLUSDT":.05}
        self.assertTrue(all(f==0 for f in queue_sell_fractions(w)))

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            planned_trim({"BTCUSDT":float("nan")})
        with self.assertRaises(ValueError):
            execute_queued_units({"BTCUSDT":.2},{"ETHUSDT":.1})

if __name__=="__main__":
    unittest.main()
