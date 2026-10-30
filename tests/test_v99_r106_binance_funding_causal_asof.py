"""Synthetic causal boundary regression only; real source replay runs in CI separately."""
import unittest

from research.tools.v99_r106_binance_funding_causal_asof import select_asof


class TestCausalFundingAsOf(unittest.TestCase):
    def test_exact_decision_event_is_not_visible(self):
        events = [(1000, 0.01), (2000, 0.02)]
        self.assertEqual(select_asof(events, 2000), (1000, 0.01))
        self.assertEqual(select_asof(events, 2001), (2000, 0.02))

    def test_positive_millisecond_residual_is_not_backdated(self):
        events = [(1000, 0.01), (2000 + 31, 0.02)]
        self.assertEqual(select_asof(events, 2000), (1000, 0.01))
        self.assertEqual(select_asof(events, 2031), (1000, 0.01))
        self.assertEqual(select_asof(events, 2032), (2031, 0.02))

    def test_no_source_before_first_observation(self):
        self.assertIsNone(select_asof([(2000, 0.02)], 2000))
        self.assertIsNone(select_asof([(2000, 0.02)], 1999))

    def test_no_future_source_even_if_timestamp_is_close(self):
        events = [(1000, 0.01), (2001, 0.02), (2002, 0.03)]
        self.assertEqual(select_asof(events, 2001), (1000, 0.01))


if __name__ == "__main__":
    unittest.main()
