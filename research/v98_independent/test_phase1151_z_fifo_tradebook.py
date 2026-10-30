import unittest
import numpy as np
import pandas as pd
from phase1151_z_fifo_tradebook import TradeBook

class TestFIFO(unittest.TestCase):
    def setUp(self):
        self.t=pd.Timestamp('2023-01-01T00:00Z')
    def test_long_and_short_fee_realization(self):
        b=TradeBook(10000)
        b.fill(0,2,100,.2,self.t)
        b.fill(0,-2,110,.22,self.t)
        self.assertAlmostEqual(b.closed[0]['pnl_usd'],19.58)
        b.fill(1,-1,100,.1,self.t)
        b.fill(1,1,90,.09,self.t)
        self.assertAlmostEqual(b.closed[1]['pnl_usd'],9.81)
        self.assertTrue(np.allclose(b.units(),0))
    def test_funding_while_open(self):
        b=TradeBook(10000);b.fill(0,1,100,.1,self.t)
        b.funding(0,-.5,self.t)
        self.assertAlmostEqual(b.total_pnl(np.full(4,100.)),-.6)
    def test_funding_after_close_same_hour(self):
        b=TradeBook(10000);b.fill(0,1,100,0,self.t)
        b.fill(0,-1,101,0,self.t)
        b.funding(0,-.2,self.t)
        self.assertAlmostEqual(b.closed[0]['pnl_usd'],.8)
    def test_unattributed_funding_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNATTRIBUTABLE'):
            TradeBook(10000).funding(0,-1,self.t)
    def test_schema_rejected(self):
        with self.assertRaisesRegex(ValueError,'SCHEMA'):
            TradeBook(10000).apply_hour([{'asset':0}],np.zeros(4),self.t,'new_after_fill')

if __name__=='__main__':unittest.main()
