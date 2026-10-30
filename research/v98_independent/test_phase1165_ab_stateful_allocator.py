import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
import numpy as np
from phase1165_ab_stateful_allocator import gate,allocate,CORNERS

def inputs():
    return dict(price=np.full(4,100.),equity=10000.,down=np.full(4,.1),
        up=np.full(4,.2),funding=np.full(4,.001),quote=np.full(4,1e7),
        min336=np.full(4,1e7))
class TestABAllocator(unittest.TestCase):
    def test_actual_units_and_corners(self):
        a=inputs();self.assertEqual(len(CORNERS),81)
        self.assertTrue(gate(np.array([10.,-10.,0,0]),np.zeros(4),**a))
        self.assertFalse(gate(np.array([100.,0,0,0]),np.zeros(4),**a))
    def test_stateful_equity_changes_decision(self):
        a=inputs();mu=np.array([.05,-.03,.01,0]);s=np.eye(4)*.01
        x=allocate(mu,s,np.zeros(4),**a)
        a['equity']=100000.
        y=allocate(mu,s,np.zeros(4),**a)
        self.assertFalse(np.array_equal(x,y))
        self.assertTrue(gate(x,np.zeros(4),**inputs()))
    def test_safe_carry_under_quote_collapse(self):
        a=inputs();old=np.array([1.,0,0,0])
        a['quote']=np.zeros(4);a['min336']=np.zeros(4)
        self.assertTrue(gate(old,old,**a))
        out=allocate(np.ones(4),np.eye(4)*.01,old,**a)
        self.assertTrue(np.array_equal(out,old))
    def test_unsafe_carry_without_liquidity_blocks(self):
        a=inputs();old=np.array([60.,0,0,0]);a['quote']=np.zeros(4)
        with self.assertRaisesRegex(ValueError,'UNEXECUTABLE_SURVIVAL_REDUCTION'):
            allocate(np.zeros(4),np.eye(4)*.01,old,**a)
    def test_entry_liquidity_restricts_growth_not_return_ceiling(self):
        a=inputs();a['min336']=np.full(4,100.)
        out=allocate(np.ones(4),np.eye(4)*.01,np.zeros(4),**a)
        self.assertTrue(gate(out,np.zeros(4),**a))
        self.assertTrue(np.all(np.abs(out)*100*1.2<=.0025*100+1e-8))
if __name__=='__main__':unittest.main()
