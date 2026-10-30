#!/usr/bin/env python3
"""Pre-economic AC finite-step actual-NAV governor and allocator tests."""
import unittest
import numpy as np
from phase1176_ac_discrete_allocator import (
    CORNERS, allocate, feasible, objective)


def fixture():
    return dict(old_units=np.zeros(4), price=np.full(4, 100.), equity=10000.,
                down=np.full(4, .2), up=np.full(4, .2),
                funding_bound=np.full(4, .0001), prior_quote=np.full(4, 1e8),
                min336_quote=np.full(4, 1e8))


class ACAllocatorTests(unittest.TestCase):
    def test_81_corners(self):
        self.assertEqual(CORNERS.shape, (81, 4))
        self.assertEqual(len({tuple(x) for x in CORNERS}), 81)

    def test_zero_survives(self):
        kw = fixture()
        self.assertTrue(feasible(np.zeros(4), **kw))

    def test_long_growth(self):
        kw = fixture()
        scores = np.array([4, 0, 0, 0])
        out = allocate(scores, np.eye(4)*.001, **kw)
        self.assertGreater(out[0], 0)
        self.assertTrue(feasible(out, **kw))
        self.assertGreater(objective(out, kw['old_units'], kw['price'], kw['equity'],
                                     scores, np.eye(4)*.001, kw['funding_bound']), 0)

    def test_short_growth(self):
        kw = fixture()
        out = allocate(np.array([-4, 0, 0, 0]), np.eye(4)*.001, **kw)
        self.assertLess(out[0], 0)
        self.assertTrue(feasible(out, **kw))

    def test_no_alpha_no_trade(self):
        kw = fixture()
        out = allocate(np.zeros(4), np.eye(4)*.001, **kw)
        np.testing.assert_array_equal(out, np.zeros(4))

    def test_order_capacity(self):
        kw = fixture()
        kw['prior_quote'] = np.full(4, 100.)
        self.assertFalse(feasible(np.array([1., 0, 0, 0]), **kw))

    def test_entry_exit_reserve(self):
        kw = fixture()
        kw['min336_quote'] = np.full(4, 100.)
        self.assertFalse(feasible(np.array([1., 0, 0, 0]), **kw))

    def test_net_and_asset_cap(self):
        kw = fixture()
        self.assertFalse(feasible(np.array([50., 0, 0, 0]), **kw))
        self.assertFalse(feasible(np.array([20., 20., 20., 20.]), **kw))

    def test_adverse_corner_survival(self):
        kw = fixture()
        kw['down'] = np.full(4, .95)
        self.assertFalse(feasible(np.array([20., 20., 20., 20.]), **kw))

    def test_no_free_exit_when_quote_zero(self):
        kw = fixture()
        kw['old_units'] = np.array([50., 0, 0, 0])
        kw['prior_quote'] = np.zeros(4)
        with self.assertRaisesRegex(ValueError, 'UNEXECUTABLE_CARRIED'):
            allocate(np.zeros(4), np.eye(4)*.001, **kw)

    def test_reproducible(self):
        kw = fixture()
        args=(np.array([4, -4, 2, -2]), np.eye(4)*.001)
        a = allocate(*args, **kw)
        b = allocate(*args, **kw)
        np.testing.assert_array_equal(a, b)

    def test_invalid_covariance_fails_closed(self):
        kw = fixture()
        with self.assertRaisesRegex(ValueError, 'COV_SCORE'):
            allocate(np.array([4, 0, 0, 0]), -np.eye(4), **kw)


if __name__ == '__main__':
    unittest.main(verbosity=2)
