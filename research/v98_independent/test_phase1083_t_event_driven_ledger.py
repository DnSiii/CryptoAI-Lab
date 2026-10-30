"""V98 T pre-economic signed ledger synthetic tests."""
import unittest
from unittest.mock import patch
import numpy as np
from phase1083_t_event_driven_ledger import simulate_t,prior_shocks

class LedgerTests(unittest.TestCase):
    def test_preflight_rejects_future(self):
        n=1600;z=np.ones((n,4));rate=np.zeros_like(z);event=np.zeros_like(z,dtype=bool)
        marks=np.full((n,4,2),np.nan);years=np.full(n,2026)
        with self.assertRaisesRegex(ValueError,'TRAINING_CELL'):
            simulate_t(np.zeros_like(z),z,z,z,z,z,rate,marks,event,np.zeros_like(z),np.zeros_like(z),.0007,
                       order='carried_before_fill',mode='immediate',years=years)
    def test_preflight_rejects_invalid_target(self):
        n=1600;z=np.ones((n,4));rate=np.zeros_like(z);event=np.zeros_like(z,dtype=bool)
        marks=np.full((n,4,2),np.nan);years=np.full(n,2023)
        with self.assertRaisesRegex(ValueError,'TARGET'):
            simulate_t(np.full_like(z,3.),z,z,z,z,z,rate,marks,event,np.zeros_like(z),np.zeros_like(z),.0007,
                       order='carried_before_fill',mode='immediate',years=years)
    def test_prior_shocks_backward_only(self):
        n=1600;o=np.full((n,4),100.);h=o*1.01;l=o*.99
        d,u=prior_shocks(o,h,l);h2=h.copy();h2[-1]=200
        d2,u2=prior_shocks(o,h2,l)
        np.testing.assert_array_equal(u[:-1],u2[:-1])
    def test_no_trade_when_flat(self):
        n=1600;z=np.full((n,4),100.);q=np.full((n,4),1e9)
        event=np.zeros((n,4),dtype=bool);rate=np.zeros((n,4));mark=np.full((n,4,2),np.nan)
        years=np.full(n,2023);d=np.zeros((n,4));u=np.zeros((n,4))
        # Incomplete synthetic year must fail fold gate, but no unnecessary trade.
        with patch('phase1083_t_event_driven_ledger.execute',side_effect=AssertionError('UNNECESSARY_TRADE')) as trade:
            with self.assertRaisesRegex(ValueError,'INCOMPLETE_CHRONOLOGICAL_FOLD'):
                simulate_t(np.zeros((n,4)),z,z,z,z,q,rate,mark,event,d,u,.0007,
                           order='carried_before_fill',mode='immediate',years=years)
            trade.assert_not_called()

if __name__=='__main__':unittest.main()
