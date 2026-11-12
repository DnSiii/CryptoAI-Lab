"""C1 prefix invariance and allocator state regressions; training-only synthetic data."""
import unittest

from research.v98_independent.phase243_native_funding_cashflow import ASSETS
from research.v98_independent.v98_composed_c1 import composed_c1_sleeves


class C1PrefixInvariance(unittest.TestCase):
    def history(self, n=900):
        return {
            a: tuple(100.0 * (1 + (k + 1) * 0.0002 * j) for j in range(n))
            for k, a in enumerate(ASSETS)
        }

    def test_future_shock_does_not_rewrite_past_decisions(self):
        baseline = self.history()
        shocked = {a: list(v) for a, v in baseline.items()}
        for a in ASSETS:
            for j in range(800, 900):
                shocked[a][j] *= 0.25 if a == ASSETS[0] else 3.0
        normal = composed_c1_sleeves()
        altered = composed_c1_sleeves()
        for n in range(1, 900):
            original = normal({a: baseline[a][:n] for a in ASSETS})
            changed = altered({a: shocked[a][:n] for a in ASSETS})
            if n <= 800:
                self.assertEqual(original, changed, f"future leak at prefix {n}")

    def test_separate_replays_do_not_share_allocator_state(self):
        history = self.history()
        first = composed_c1_sleeves()
        for n in range(1, 900):
            first({a: history[a][:n] for a in ASSETS})
        second = composed_c1_sleeves()
        fresh = composed_c1_sleeves()
        for n in range(1, 900):
            prefix = {a: history[a][:n] for a in ASSETS}
            self.assertEqual(second(prefix), fresh(prefix))


if __name__ == "__main__":
    unittest.main()
