#!/usr/bin/env python3
"""Y authenticated source canonical 6-decimal serialization fail-closed tests."""
import unittest
import numpy as np
import pandas as pd
from phase1130_y_authenticated_source import canonical_target,attest,ASSETS

class TestYSourceCanonical(unittest.TestCase):
    def test_quantized_roundtrip_allows_binary_ulp_not_economic_drift(self):
        idx=pd.date_range('2022-12-01',periods=2,freq='h',tz='UTC')
        x=np.array([[.123456,-.123456,0,0],[.111111,.111111,0,0]])
        f=pd.DataFrame(x,index=idx,columns=ASSETS)
        g=f.copy()
        g.iloc[0,0]=np.nextafter(g.iloc[0,0],np.inf)
        self.assertEqual(canonical_target(f),canonical_target(g))
    def test_unquantized_rejected(self):
        idx=pd.date_range('2022-12-01',periods=1,freq='h',tz='UTC')
        f=pd.DataFrame([[.123456789,0,0,0]],index=idx,columns=ASSETS)
        with self.assertRaises(ValueError):canonical_target(f)
    def test_unsafe_target_rejected(self):
        idx=pd.date_range('2022-12-01',periods=1,freq='h',tz='UTC')
        f=pd.DataFrame([[.9,0,0,0]],index=idx,columns=ASSETS)
        with self.assertRaises(ValueError):canonical_target(f)
    def test_incomplete_source_rejected_before_mark_read(self):
        idx=pd.date_range('2022-12-01',periods=10,freq='h',tz='UTC')
        arrays={k:np.ones((10,4)) for k in ('open','high','low','close','quote_volume')}
        with self.assertRaises(ValueError):
            attest(arrays,np.zeros((10,4)),np.ones((10,4)),np.zeros((10,4),bool),
                   idx.year,idx,'/nonexistent-v98-y-mark.csv')
if __name__=='__main__':unittest.main()
