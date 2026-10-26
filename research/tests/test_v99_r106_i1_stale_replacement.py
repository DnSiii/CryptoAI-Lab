"""Precommitted adversarial tests for original I1 as-of book revocation.

Synthetic microfixtures exercise code semantics only; no original fills or ROI.
"""
import unittest
from datetime import datetime, timezone, timedelta

from research.tools.v99_r106_i1_original_signal_option_join import source_ready
from research.verification.independent_v99_r106_i1_original_signal_option_oracle import _ready

T = int(datetime(2022, 1, 3, tzinfo=timezone.utc).timestamp() * 1_000_000)
MS = T // 1000
A = "BTC-28JAN22-40000-P"
B = "BTC-28JAN22-42000-P"


def quote(symbol, arrival_before_seconds, event_before_seconds=None, bid="0.001", ask="0.002"):
    if event_before_seconds is None:
        event_before_seconds = arrival_before_seconds + 0.1
    arrival = T - int(arrival_before_seconds * 1_000_000)
    event = T - int(event_before_seconds * 1_000_000)
    row = {"symbol": symbol, "bid_price": bid, "ask_price": ask,
           "bid_amount": "1", "ask_amount": "1"}
    return arrival, event, row


class LatestPredecisionRevocation(unittest.TestCase):
    def check(self, records, expected):
        self.assertIs(source_ready(records, MS, "BTC"), expected)
        self.assertIs(_ready(records, MS, "BTC"), expected)

    def base(self):
        return [quote(A, 20), quote(B, 20.2)]

    def test_two_valid_fresh_legs(self):
        self.check(self.base(), True)

    def test_newer_crossed_update_revokes(self):
        self.check(self.base() + [quote(A, 5, bid="0.003", ask="0.002")], False)

    def test_newer_stale_exchange_event_revokes(self):
        # This is the regression: 5s-old arrival but 600s-old event.
        # The former implementation discarded this row before latest selection,
        # wrongly preserving the 20s-old book.
        self.check(self.base() + [quote(A, 5, event_before_seconds=600)], False)

    def test_newer_old_arrival_revokes(self):
        self.check(self.base() + [quote(A, 10, event_before_seconds=360)], False)

    def test_postdecision_update_does_not_revoke(self):
        self.check(self.base() + [quote(A, -1, event_before_seconds=-0.5)], True)

    def test_other_symbol_does_not_revoke(self):
        self.check(self.base() + [quote("ETH-28JAN22-3000-P", 5, event_before_seconds=600)], True)

    def test_one_strike_not_two(self):
        self.check([quote(A, 20), quote(A, 19)], False)

    def test_equal_arrival_last_capture_revokes(self):
        self.check(self.base() + [quote(A, 20, event_before_seconds=600)], False)

    def test_expired_or_out_of_window_is_not_eligible(self):
        self.check([quote("BTC-07JAN22-40000-P", 20), quote("BTC-07JAN22-42000-P", 20.2)], False)


if __name__ == "__main__":
    unittest.main()
