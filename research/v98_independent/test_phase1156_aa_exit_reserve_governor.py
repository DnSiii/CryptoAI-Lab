import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
import numpy as np
from phase1156_aa_exit_reserve_governor import gate,allocate,CORNERS

class TestExitReserve(unittest.TestCase):
    def setup_args(self):
        z=np.zeros(4)
        return dict(carried=z,down=np.full(4,.1),up=np.full(4,.2),
            funding=np.full(4,.001),entry_quote=np.full(4,1e6),
            minimum_72h_quote=np.full(4,1e6),capital=10000.)
    def test_81_and_exit_reserve(self):
        a=self.setup_args();self.assertEqual(len(CORNERS),81)
        self.assertTrue(gate(np.array([.1,0,0,0]),**a))
        self.assertFalse(gate(np.array([.6,0,0,0]),**a))
    def test_exit_failure_not_silent(self):
        a=self.setup_args();a['carried']=np.array([.2,0,0,0])
        a['entry_quote']=np.full(4,1.)
        a['minimum_72h_quote']=np.full(4,1e4)
        with self.assertRaisesRegex(ValueError,'UNEXECUTABLE_PRIOR_EXIT'):
            allocate(np.zeros(4),np.eye(4)*.01,**a)
    def test_reduce_only_is_charged_against_original_inventory(self):
        a=self.setup_args();a['carried']=np.array([.2,0,0,0])
        a['minimum_72h_quote']=np.full(4,1e4)
        a['entry_quote']=np.full(4,1e6)
        w=allocate(np.zeros(4),np.eye(4)*.01,**a)
        self.assertTrue(gate(w,**a))
        self.assertLess(abs(w[0]),abs(a['carried'][0]))
    def test_capital_modes_and_zero_liquidity(self):
        a=self.setup_args()
        for cap in (10000.,1e6,1e7):
            a['capital']=cap
            w=allocate(np.array([.05,-.05,.02,0]),np.eye(4)*.01,**a)
            self.assertTrue(gate(w,**a))
            self.assertTrue(np.all(np.abs(w)*1.2<=.006*1e6/cap+1e-10))
        a['entry_quote']=np.zeros(4)
        self.assertTrue(np.array_equal(allocate(np.ones(4),np.eye(4)*.01,**a),np.zeros(4)))
    def test_no_free_quantized_fills(self):
        a=self.setup_args();a['entry_quote']=np.full(4,1.)
        w=allocate(np.ones(4),np.eye(4)*.01,**a)
        self.assertTrue(gate(w,**a))
        self.assertTrue(np.all(np.abs(w)<=.01/(10000*1.002)+1e-10))

if __name__=='__main__':unittest.main()
