#!/usr/bin/env python3
"""AC official dispatcher preflight only: no vendor downloads or historical PnL."""
import unittest
import numpy as np
import pandas as pd
from phase1182_ac_official_training import fold_metrics, causal_risk, FROZEN_HASHES, FROZEN_BLOBS
from test_phase1174_ac_discrete_intents import sample


class ACOfficialPreflight(unittest.TestCase):
    def test_frozen_15_hash_contract(self):
        self.assertEqual(len(FROZEN_HASHES),15)
        self.assertEqual(len(FROZEN_BLOBS),5)
        self.assertEqual(len(set(FROZEN_HASHES.values())),15)

    def test_causal_risk_geometry(self):
        frames=sample()
        data={name:frame for name,frame in zip(
            ('open','high','low','close','quote_volume','funding'),frames)}
        risk=causal_risk(data,np.zeros((1300,4)))
        down,up,qmin,fbound,cov=risk
        self.assertEqual(down.shape,(1300,4))
        self.assertEqual(qmin.shape,(1300,4))
        self.assertIn(744,cov)
        self.assertEqual(cov[744].shape,(4,4))
        self.assertTrue(np.isfinite(cov[744]).all())
        self.assertTrue((down[744]>=.25).all())
        self.assertTrue((up[744]>=.30).all())
        self.assertTrue((fbound[744]>=.001).all())

    def test_fold_metrics_positive_and_negative(self):
        idx=pd.date_range('2023-01-01T00:00:00Z',periods=17544,freq='h')
        nav=np.r_[np.linspace(10000,12000,8760),np.linspace(12000,9000,8784)]
        r=fold_metrics(idx,nav,10000.)
        self.assertGreater(r['2023']['cagr_annualized'],0)
        self.assertLess(r['2024']['cagr_annualized'],0)
        self.assertEqual(r['2023']['hours'],8760)
        self.assertEqual(r['2024']['hours'],8784)
        self.assertLess(r['2024']['max_drawdown'],0)
        self.assertEqual(r['2023']['trade_level_pf_payoff_win_rate'],
                         'PENDING_SEPARATE_FROZEN_FIFO_AUDIT')

    def test_invalid_nav_rejected(self):
        idx=pd.date_range('2023-01-01T00:00:00Z',periods=3,freq='h')
        with self.assertRaisesRegex(ValueError,'INVALID_NAV'):
            fold_metrics(idx,[10000,float('nan'),10000],10000.)


if __name__=='__main__':
    unittest.main(verbosity=2)
