import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
from phase1171_ab_fifo_tradebook import Tradebook
class TestFIFO(unittest.TestCase):
    def test_long_fee_funding(self):
        b=Tradebook();b.trade(0,2,100,2);b.funding(0,-1)
        r=b.trade(0,-2,110,2)[0]
        self.assertAlmostEqual(r['gross_pnl'],20)
        self.assertAlmostEqual(r['net_pnl'],15)
        self.assertEqual(b.metrics()['closed_trades'],1)
    def test_short_and_crossing(self):
        b=Tradebook();b.trade(0,-2,100,2)
        r=b.trade(0,3,90,3)
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]['direction'],'SHORT')
        self.assertAlmostEqual(r[0]['gross_pnl'],20)
        self.assertAlmostEqual(b.position(0),1)
        self.assertAlmostEqual(b.lots[0][0]['fee'],1)
    def test_fifo_partial_and_reconciliation(self):
        b=Tradebook();b.trade(0,1,100,1);b.trade(0,2,105,2)
        r=b.trade(0,-2,110,2)
        self.assertEqual(len(r),2)
        self.assertAlmostEqual(sum(x['net_pnl'] for x in r),10+5-4)
        self.assertAlmostEqual(b.position(0),1)
        self.assertAlmostEqual(b.lots[0][0]['entry'],105)
    def test_no_fake_funding(self):
        b=Tradebook()
        with self.assertRaisesRegex(ValueError,'WITHOUT_INVENTORY'):b.funding(0,1)
    def test_profit_factor_and_win_rate(self):
        b=Tradebook();b.trade(0,1,100,0);b.trade(0,-1,110,0)
        b.trade(0,1,100,0);b.trade(0,-1,95,0)
        x=b.metrics();self.assertEqual(x['closed_trades'],2)
        self.assertAlmostEqual(x['profit_factor'],2.)
        self.assertAlmostEqual(x['win_rate'],.5)
if __name__=='__main__':unittest.main()
