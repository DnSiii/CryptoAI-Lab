#!/usr/bin/env python3
"""V98 S typed vendor mark schema, sign, event and shape tests."""
import csv
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from phase1070_s_typed_native_mark import signed_mark_bounds,FIELDS
from phase1069_s_sevenslot_source import ASSETS


def fixture():
    idx=pd.date_range('2022-12-01',periods=100,freq='h',tz='UTC')
    rate=np.zeros((100,4));event=np.zeros((100,4),bool);mark=np.full((100,4),np.nan)
    rate[8,0]=.001;event[8,0]=True;mark[8,0]=101.
    rate[16,1]=-.002;event[16,1]=True;mark[16,1]=99.
    rows=[]
    for t,j,lo,hi in ((8,0,99.,101.),(16,1,99.,101.)):
        rows.append(dict(asset=ASSETS[j],funding_slot_ms=int(idx[t].timestamp()*1000),
                         funding_time_ms=int(idx[t].timestamp()*1000)+10,funding_rate=rate[t,j],
                         mark_low=lo,mark_high=hi,conservative_mark=mark[t,j]))
    return idx,rate,event,mark,rows

class STypedMarkTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'mark.csv'
        self.idx,self.rate,self.event,self.mark,self.rows=fixture();self.write(self.rows)
    def tearDown(self):self.tmp.cleanup()
    def write(self,rows):
        with self.path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    def runcheck(self):return signed_mark_bounds(self.path,self.idx,self.rate,self.event,self.mark,require_full=False)
    def test_signed_bounds(self):
        b=self.runcheck();self.assertEqual(b.shape,(100,4,2));self.assertEqual(b[8,0].tolist(),[99.,101.]);self.assertEqual(b[16,1].tolist(),[99.,101.])
    def test_reject_duplicate(self):
        self.write(self.rows+self.rows[:1]);
        with self.assertRaises(ValueError):self.runcheck()
    def test_reject_missing(self):
        self.write(self.rows[:1]);
        with self.assertRaises(ValueError):self.runcheck()
    def test_reject_sign(self):
        rows=[dict(r) for r in self.rows];rows[1]['conservative_mark']=101.;self.write(rows)
        with self.assertRaises(ValueError):self.runcheck()
    def test_reject_wrong_shape(self):
        with self.assertRaises(ValueError):signed_mark_bounds(self.path,self.idx,self.rate,self.event,np.zeros((100,4,2)),require_full=False)
    def test_reject_future(self):
        idx=pd.date_range('2025-01-01',periods=100,freq='h',tz='UTC')
        with self.assertRaises(ValueError):signed_mark_bounds(self.path,idx,self.rate,self.event,self.mark,require_full=False)

if __name__=='__main__':unittest.main()
