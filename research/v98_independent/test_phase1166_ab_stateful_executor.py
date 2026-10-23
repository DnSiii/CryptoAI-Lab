import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
import numpy as np
from phase1166_ab_stateful_executor import execute_hour,signed_mark,actual_corners

def args(**kw):
    a=dict(prior=np.full(4,100.),opening=np.full(4,100.),
        high=np.full(4,101.),low=np.full(4,99.),closing=np.full(4,100.),
        carried_units=np.zeros(4),cash=10000.,intent=np.array([.05,-.05,0,0]),
        cov=np.eye(4)*.01,prior_down=np.full(4,.15),prior_up=np.full(4,.15),
        prior_funding_bound=np.full(4,.001),prior_quote=np.full(4,1e8),
        prior_min336=np.full(4,1e8),fee=.0007,order='new_after_fill',
        funding_rate=np.zeros(4),funding_mark_bounds=np.full((4,2),np.nan),
        funding_event=np.zeros(4,bool),rebalance=True)
    a.update(kw);return a
class TestABExecutor(unittest.TestCase):
    def test_self_financing(self):
        x=execute_hour(**args());self.assertTrue(x['ok'],x.get('reason'))
        self.assertAlmostEqual(x['equity'],x['cash']+np.dot(x['units'],np.full(4,100.)),places=7)
        self.assertGreater(x['fees'],0)
    def test_81_corner_failure(self):
        x=actual_corners(0.,np.array([1.,0,0,0]),np.array([50,100,100,100]),
                         np.full(4,100.),np.array([150,100,100,100]),100.,0.)
        self.assertFalse(x['ok'])
    def test_signed_native_funding(self):
        marks=np.array([[99,101],[99,101],[np.nan,np.nan],[np.nan,np.nan]])
        m=signed_mark(np.array([1,-1,0,0]),np.array([.01,.01,0,0]),
                      marks,np.array([True,True,False,False]),np.full(4,100.))
        self.assertEqual(m.tolist()[:2],[101,99])
    def test_gap_exit_capacity_fail_closed(self):
        x=execute_hour(**args(carried_units=np.array([10.,0,0,0]),
            opening=np.array([70.,100,100,100]),low=np.array([69.,99,99,99]),
            high=np.full(4,101.),closing=np.array([75.,100,100,100]),
            prior_quote=np.full(4,1.),rebalance=False))
        self.assertIn(x['reason'],('AB1166_UNEXECUTABLE_GAP_EXIT',
                                  'AB1165_UNEXECUTABLE_SURVIVAL_REDUCTION'))
    def test_t_minus_one_intent(self):
        x=execute_hour(**args())
        y=execute_hour(**args(high=np.full(4,105.),low=np.full(4,95.)))
        self.assertTrue(np.array_equal(x['opening_fill'],y['opening_fill']))
    def test_safe_carry_with_zero_quote(self):
        x=execute_hour(**args(carried_units=np.array([1.,0,0,0]),
            prior_quote=np.zeros(4),prior_min336=np.zeros(4),rebalance=False))
        self.assertTrue(x['ok'],x.get('reason'))
        self.assertEqual(x['units'][0],1.)
if __name__=='__main__':unittest.main()
