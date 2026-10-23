import unittest
import numpy as np
from phase1220_af_sell_buy_governor import (
    CORNERS,plan,audit,FEE,SLIPPAGE)


def inputs():
    return dict(carried=np.zeros(4),opening=np.full(4,100.),cash=10000.,
        down=np.full(4,.35),up=np.full(4,.45),
        funding_bound=np.full(4,.006),
        prior_quote=np.full(4,1e9),min_quote=np.full(4,1e9))


class AFSellBuyGovernorTests(unittest.TestCase):
    def test_exact_81_intrabar_corners(self):
        self.assertEqual(CORNERS.shape,(81,4))
        self.assertEqual(len(set(map(tuple,CORNERS))),81)

    def test_fully_funded_growth_buy_when_feasible(self):
        p=inputs()
        r=plan(np.array([.10,.10,0,0]),**p)
        self.assertEqual(r['fraction'],1.)
        self.assertTrue(r['fully_collateralized'])
        self.assertGreaterEqual(r['cash'],0)
        np.testing.assert_allclose(r['units'],[10,10,0,0])

    def test_real_sell_proceeds_less_fees_and_slippage(self):
        p=inputs()
        p['cash']=9000.
        p['carried'][0]=10.
        r=plan(np.zeros(4),**p)
        self.assertAlmostEqual(r['cash'],9000+1000*(1-FEE-SLIPPAGE))
        self.assertAlmostEqual(r['fees'],1000*FEE)
        self.assertAlmostEqual(r['slippage'],1000*SLIPPAGE)
        np.testing.assert_array_equal(r['units'],np.zeros(4))

    def test_unexitable_carried_inventory_fails_closed(self):
        p=inputs()
        p['carried'][0]=1.
        p['prior_quote'][0]=0
        with self.assertRaisesRegex(ValueError,'UNEXECUTABLE_CARRIED_EXIT'):
            plan(np.zeros(4),**p)

    def test_largest_feasible_growth_buy(self):
        p=inputs()
        w=np.array([.80,0,0,0])
        r=plan(w,**p)
        self.assertGreater(r['fraction'],0)
        self.assertLess(r['fraction'],1)
        higher=(r['fraction']+.01)*w*p['cash']/p['opening']
        free=p['cash']-float(higher@p['opening'])*(1+FEE+SLIPPAGE)
        if free>=0:
            check=audit(higher,free,p['opening'],p['cash'],
                        p['down'],p['up'],p['funding_bound'],
                        p['prior_quote'],p['min_quote'],higher)
            self.assertFalse(check['feasible'])

    def test_zero_entry_quote_means_cash_not_fictional_fill(self):
        p=inputs()
        p['min_quote'][0]=0
        r=plan(np.array([.10,0,0,0]),**p)
        self.assertEqual(r['fraction'],0.)
        self.assertEqual(r['units'].sum(),0.)
        self.assertEqual(r['cash'],p['cash'])

    def test_no_borrowing_when_cash_empty(self):
        p=inputs()
        p['cash']=0.
        with self.assertRaisesRegex(ValueError,'INSOLVENCY'):
            plan(np.array([.5,0,0,0]),**p)

    def test_no_short_or_overgross_target(self):
        p=inputs()
        with self.assertRaisesRegex(ValueError,'COLLATERAL_OR_TARGET'):
            plan(np.array([-.1,0,0,0]),**p)
        with self.assertRaisesRegex(ValueError,'COLLATERAL_OR_TARGET'):
            plan(np.ones(4)*.3,**p)

    def test_adverse_funding_reduces_corner_equity(self):
        p=inputs()
        n=np.full(4,3.)
        x=audit(n,8800.,p['opening'],p['cash'],p['down'],p['up'],
                np.zeros(4),p['prior_quote'],p['min_quote'],n)
        y=audit(n,8800.,p['opening'],p['cash'],p['down'],p['up'],
                np.full(4,.05),p['prior_quote'],p['min_quote'],n)
        self.assertTrue(x['feasible'])
        self.assertTrue(y['feasible'])
        self.assertLess(y['worst_corner_equity'],x['worst_corner_equity'])

    def test_deterministic_source_only(self):
        p=inputs()
        w=np.array([.1,.1,.1,0])
        a=plan(w,**p)
        b=plan(w,**p)
        np.testing.assert_array_equal(a['units'],b['units'])
        self.assertEqual(a['audit'],b['audit'])
        self.assertFalse(a['historical_system_pnl_computed'])


if __name__=='__main__':unittest.main()
