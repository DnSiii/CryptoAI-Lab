import unittest
import numpy as np
import pandas as pd
from phase1043_q_source_auth_and_canonical import canonicalize

class QCanonical(unittest.TestCase):
    def test_quantization_deterministic(self):
        i=pd.date_range('2023-01-01',periods=2,freq='h',tz='UTC')
        x=pd.DataFrame([[.1,-.1,0,0],[.12345678912,-.2,0,0]],index=i,columns=['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT'])
        a,h=canonicalize(x);b,k=canonicalize(x)
        self.assertEqual(h,k);self.assertEqual(a.to_csv(float_format='%.8f'),b.to_csv(float_format='%.8f'))
        self.assertEqual(a.iloc[1,0],.12345679)
    def test_caps_rejected(self):
        i=pd.date_range('2023-01-01',periods=1,freq='h',tz='UTC')
        x=pd.DataFrame([[.6,0,0,0]],index=i,columns=['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT'])
        with self.assertRaises(ValueError):canonicalize(x)

if __name__=='__main__':unittest.main()
