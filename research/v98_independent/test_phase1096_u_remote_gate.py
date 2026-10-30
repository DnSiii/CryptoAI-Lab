"""V98 U 90-cell SYNTHETIC smoke and safety; never economic evidence."""
import itertools
import unittest
import numpy as np
from phase1095_u_integrated_ledger import simulate_synthetic_u,FEE_TIERS,ORDERS,CAPITAL_MODES
from phase1093_u_contingent_execution import plan, audit_bracket_paths
from phase1096_u_safety_oracle import require_full_stop_coverage,realized_funding_buffer

class URemoteGate(unittest.TestCase):
    def fixture(self,n=40):
        o=np.full((n,4),100.);h=o*1.001;l=o*.999;c=o.copy()
        q=np.full((n,4),1e9);r=np.zeros((n,4))
        mk=np.full((n,4,2),np.nan);ev=np.zeros((n,4),bool)
        dn=np.full((n,4),.02);up=np.full((n,4),.02)
        return [o,h,l,c,q,r,mk,ev,dn,up]
    def test_90_synthetic_cells_no_false_profit(self):
        vectors=((.03,0,0,0),(.04,.02,0,0),(.04,0,0,0),
                 (0,.02,0,0),(.04,0,0,.01))
        n=40;data=self.fixture(n);survivors=0
        for vec,fee,order,mode in itertools.product(vectors,FEE_TIERS.values(),ORDERS,CAPITAL_MODES):
            target=np.zeros((n,4));target[1:]=vec
            z=simulate_synthetic_u(target,*data,fee=fee,order=order,mode=mode)
            self.assertTrue(z['survived'],(vec,fee,order,mode,z['reason']))
            self.assertFalse(z['historical_pnl_validated'])
            self.assertFalse(z['authenticated_source'])
            self.assertGreater(z['fees_usd'],0)
            self.assertLess(z['terminal_usd'],z['initial_usd'])
            survivors+=1
        self.assertEqual(survivors,90)
    def test_unprotected_quantity_is_rejected(self):
        p=np.full(4,100.);q=np.full(4,1e7)
        b=plan(p,np.array([5.,0,0,0]),np.full(4,.05),np.full(4,.05),q)
        self.assertEqual(require_full_stop_coverage(b,np.array([20.,0,0,0])),
                         'U_UNPROTECTED_STOP_QUANTITY')
    def test_realized_funding_cannot_hide_path_breach(self):
        p=np.full(4,100.);q=np.full(4,1e7)
        u=np.array([7.435,0,0,0]);b=plan(p,u,np.full(4,.05),np.full(4,.05),q)
        hi=np.array([110.,101.,101.,101.]);lo=np.full(4,99.)
        self.assertTrue(audit_bracket_paths(b,1000,u,p,hi,lo,.0007)['ok'])
        mk=np.full((4,2),np.nan);mk[0]=[100,100]
        reserve=realized_funding_buffer(u,u,np.array([.001,0,0,0]),
                      np.array([True,False,False,False]),mk)
        a=audit_bracket_paths(b,1000,u,p,hi,lo,.0007,buffer=reserve)
        self.assertFalse(a['ok']);self.assertEqual(a['reason'],'U_PATH_ASSET')

    def test_preplaced_signed_reversal_fails_closed(self):
        n=40;data=self.fixture(n)
        target=np.zeros((n,4));target[1:15,0]=.05;target[15:,0]=-.05
        z=simulate_synthetic_u(target,*data)
        self.assertFalse(z['survived'])
        self.assertEqual(z['reason'],'U_UNSUPPORTED_PREPLACED_REVERSAL')
    def test_invalid_event_mark_rejected(self):
        n=40;data=self.fixture(n)
        data[7][10,0]=True;data[5][10,0]=.001
        target=np.zeros((n,4));target[1:,0]=.03
        with self.assertRaisesRegex(ValueError,'FUNDING'):
            simulate_synthetic_u(target,*data)
    def test_signed_short_funding_debit(self):
        n=40;data=self.fixture(n)
        data[7][10,0]=True;data[5][10,0]=-.001
        data[6][10,0]=[99.,101.]
        target=np.zeros((n,4));target[1:,0]=-.03
        z=simulate_synthetic_u(target,*data)
        self.assertTrue(z['survived'],z['reason'])
        self.assertGreater(z['funding_debit_usd'],0)

if __name__=='__main__':unittest.main()
