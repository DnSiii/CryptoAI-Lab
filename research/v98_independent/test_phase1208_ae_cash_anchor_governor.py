import unittest
import numpy as np
from phase1208_ae_cash_anchor_governor import (
    CORNERS,project,audit,ASSET_CAP,GROSS_CAP,NET_CAP)


def inputs():
    return {'carried':np.zeros(4),'opening':np.full(4,100.),
            'equity':10000.,'down':np.full(4,.25),
            'up':np.full(4,.30),'funding_bound':np.full(4,.005),
            'prior_quote':np.full(4,1e9),'min_quote':np.full(4,1e9)}


class AECashAnchorGovernorTests(unittest.TestCase):
    def test_exact_81_signed_corners(self):
        self.assertEqual(CORNERS.shape,(81,4))
        self.assertEqual(len(set(map(tuple,CORNERS))),81)

    def test_maximal_growth_candidate_when_feasible(self):
        p=inputs()
        w=np.full(4,.10)
        r=project(w,**p)
        self.assertEqual(r['fraction'],1.)
        np.testing.assert_allclose(r['units'],w*p['equity']/p['opening'])
        self.assertTrue(r['flatten_verified'])

    def test_largest_feasible_fraction_not_minimum_risk(self):
        p=inputs()
        w=np.array([.80,0,0,0])
        r=project(w,**p)
        self.assertGreater(r['fraction'],0)
        self.assertLess(r['fraction'],1)
        self.assertTrue(audit(r['units'],p['carried'],p['opening'],p['equity'],
                              p['down'],p['up'],p['funding_bound'],
                              p['prior_quote'],p['min_quote'])['feasible'])
        higher=(r['fraction']+.01)*w*p['equity']/p['opening']
        self.assertFalse(audit(higher,p['carried'],p['opening'],p['equity'],
                               p['down'],p['up'],p['funding_bound'],
                               p['prior_quote'],p['min_quote'])['feasible'])

    def test_no_free_exit_if_carried_order_capacity_zero(self):
        p=inputs()
        p['carried'][0]=1.
        p['prior_quote'][0]=0
        with self.assertRaisesRegex(ValueError,'UNEXECUTABLE_CARRIED_EXIT_CURRENT_ORDER_CAPACITY'):
            project(np.zeros(4),**p)

    def test_cash_anchor_is_actual_charged_liquidation(self):
        p=inputs()
        p['carried'][0]=1.
        r=project(np.zeros(4),**p)
        self.assertEqual(r['fraction'],1.)
        np.testing.assert_array_equal(r['units'],np.zeros(4))
        self.assertGreater(r['audit']['current_fill_cost_reserve'],0)

    def test_future_exit_reserve_applies_to_existing_inventory(self):
        p=inputs()
        p['carried'][0]=.1
        p['min_quote'][0]=10000
        result=audit(p['carried'],p['carried'],p['opening'],p['equity'],
                     p['down'],p['up'],p['funding_bound'],
                     p['prior_quote'],p['min_quote'])
        self.assertEqual(result['reason'],'FUTURE_EXIT_RESERVE')

    def test_zero_quote_disallows_new_entry_without_hiding_failure(self):
        p=inputs()
        p['min_quote'][0]=0
        r=project(np.array([.1,0,0,0]),**p)
        self.assertEqual(r['fraction'],0.)
        np.testing.assert_array_equal(r['units'],np.zeros(4))

    def test_adverse_funding_reserve_reduces_worst_equity(self):
        p=inputs()
        n=np.full(4,3.)
        low=audit(n,p['carried'],p['opening'],p['equity'],
                  p['down'],p['up'],np.zeros(4),
                  p['prior_quote'],p['min_quote'])
        high=audit(n,p['carried'],p['opening'],p['equity'],
                   p['down'],p['up'],np.full(4,.05),
                   p['prior_quote'],p['min_quote'])
        self.assertTrue(low['feasible'])
        self.assertTrue(high['feasible'])
        self.assertLess(high['worst_corner_equity'],low['worst_corner_equity'])

    def test_deterministic_and_source_only(self):
        p=inputs()
        w=np.array([.1,-.1,.1,-.1])
        a=project(w,**p)
        b=project(w,**p)
        np.testing.assert_array_equal(a['units'],b['units'])
        self.assertEqual(a['audit'],b['audit'])
        self.assertFalse(a['historical_system_pnl_computed'])


if __name__=='__main__':unittest.main()
