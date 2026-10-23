import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
import numpy as np
from phase1160_aa_inventory_executor import execute_hour,corners,signed_mark

def args(**kw):
    a=dict(prior=np.full(4,100.),opening=np.full(4,100.),high=np.full(4,101.),
        low=np.full(4,99.),closing=np.full(4,100.),carried_units=np.zeros(4),
        desired_weights=np.array([.1,-.1,0.,0.]),cash=10000.,
        prior_down=np.full(4,.15),prior_up=np.full(4,.15),
        prior_funding_bound=np.full(4,.001),prior_quote=np.full(4,1e8),
        prior_min72_quote=np.full(4,1e8),fee=.0007,order='new_after_fill',
        funding_rate=np.zeros(4),funding_mark_bounds=np.full((4,2),np.nan),
        funding_event=np.zeros(4,bool),rebalance=True)
    a.update(kw);return a

class TestAAInventory(unittest.TestCase):
    def test_self_financing_and_fee(self):
        x=execute_hour(**args());self.assertTrue(x['ok'],x.get('reason'))
        self.assertEqual(len(x['events']),2)
        self.assertAlmostEqual(x['equity'],x['cash']+np.sum(x['units']*100),places=8)
        self.assertGreater(x['fees'],0)
    def test_open_and_exit_capacity(self):
        self.assertEqual(execute_hour(**args(prior_quote=np.zeros(4)))['reason'],
                         'AA1160_UNEXECUTABLE_TARGET')
        self.assertEqual(execute_hour(**args(prior_min72_quote=np.full(4,1.)))['reason'],
                         'AA1160_UNEXECUTABLE_TARGET')
    def test_signed_funding(self):
        marks=np.array([[99,101],[99,101],[np.nan,np.nan],[np.nan,np.nan]])
        m=signed_mark(np.array([1,-1,0,0]),np.array([.01,.01,0,0]),
                      marks,np.array([True,True,False,False]),np.full(4,100.))
        self.assertEqual(m.tolist()[:2],[101,99])
    def test_81_corner_fail_closed(self):
        x=corners(0.,np.array([1.,0,0,0]),np.array([50.,100,100,100]),
                  np.full(4,100.),np.array([150.,100,100,100]),100.)
        self.assertFalse(x['ok'])
    def test_gap_no_fabricated_exit(self):
        x=execute_hour(**args(carried_units=np.array([1.,0,0,0]),
            opening=np.array([80.,100,100,100]),low=np.array([79.,99,99,99]),
            high=np.full(4,101.),closing=np.array([85.,100,100,100]),
            desired_weights=np.array([.3,.2,0,0]),prior_down=np.full(4,.1)))
        self.assertTrue(x['ok'],x.get('reason'))
        self.assertTrue(x['basket_stop'])
        self.assertTrue(np.allclose(x['units'],0))
    def test_t_plus_one_targets_ignore_current_bar(self):
        x=execute_hour(**args())
        y=execute_hour(**args(high=np.full(4,110.),low=np.full(4,90.)))
        self.assertTrue(np.array_equal(x['planned_units'],y['planned_units']))
if __name__=='__main__':unittest.main()
