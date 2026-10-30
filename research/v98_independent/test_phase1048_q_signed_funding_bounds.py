import unittest
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from phase1048_q_signed_funding_bounds import signed_bounds,adverse_debit,FIELDS

class QSignedBoundsTests(unittest.TestCase):
    def test_long_and_short_adverse_mark(self):
        u=np.array([1,-1,1,-1],float);r=np.array([.01,.01,-.01,-.01])
        mark=np.array([[90,110]]*4,float)
        # debit-high for positive u*r; credit-low for negative u*r
        self.assertAlmostEqual(adverse_debit(u,r,mark),.01*(110-90-90+110))
    def test_parser_and_time_guard(self):
        idx=pd.date_range('2023-01-01',periods=9,freq='h',tz='UTC')
        first=int(idx[0].timestamp()*1000)
        rows=['asset,funding_slot_ms,funding_time_ms,funding_rate,mark_low,mark_high,conservative_mark']
        rows.append(f'BTCUSDT,{first},{first},0.01,90,110,110')
        rows.append(f'ETHUSDT,{first},{first},-0.01,90,110,90')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bounds.csv';p.write_text('\n'.join(rows)+'\n')
            mark,rate,event=signed_bounds(p,idx,expected_events=2)
            self.assertEqual(int(event.sum()),2)
            self.assertEqual(mark[0,0,1],110)
            self.assertEqual(rate[0,1],-.01)
            with self.assertRaises(ValueError):signed_bounds(p,idx,expected_events=3)
    def test_future_rejected(self):
        idx=pd.date_range('2025-01-01',periods=9,freq='h',tz='UTC')
        with self.assertRaises(ValueError):signed_bounds('unused',idx,expected_events=0)

if __name__=='__main__':unittest.main()
