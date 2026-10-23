#!/usr/bin/env python3
"""V98 S source-only signed transport, chronology, determinism and hash tests."""
import csv
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from phase1069_s_sevenslot_source import ASSETS,compose_s
from phase1070_s_typed_native_mark import FIELDS
from phase1071_s_authenticated_source import attest,canonical_target
from test_phase1069_s_sevenslot_source import data

class SSourceAttestation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=data(n=1800)
        cls.arrays={k:f.to_numpy(float) for k,f in zip(('open','high','low','close','quote_volume'),cls.frames)}
        cls.rate=np.zeros((1800,4));cls.event=np.zeros((1800,4),bool)
        cls.mark=np.full((1800,4),np.nan)
        cls.idx=cls.frames[0].index;cls.years=cls.idx.year.to_numpy()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.csv=Path(self.tmp.name)/'native.csv'
        self.event=self.event.copy();self.rate=self.rate.copy();self.mark=self.mark.copy()
        for t,j,f,low,high in ((8,0,.0001,90.,110.),(16,1,-.0001,90.,110.)):
            self.event[t,j]=True;self.rate[t,j]=f;self.mark[t,j]=high if f>=0 else low
        with self.csv.open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=FIELDS);writer.writeheader()
            for t,j,low,high in ((8,0,90.,110.),(16,1,90.,110.)):
                writer.writerow(dict(asset=ASSETS[j],funding_slot_ms=int(self.idx[t].timestamp()*1000),
                    funding_time_ms=int(self.idx[t].timestamp()*1000)+9,funding_rate=self.rate[t,j],
                    mark_low=low,mark_high=high,conservative_mark=self.mark[t,j]))
    def tearDown(self):self.tmp.cleanup()
    def call(self,**kw):
        args=dict(arrays=self.arrays,rate=self.rate,conservative=self.mark,event=self.event,
                  years=self.years,idx=self.idx,bounds_csv=self.csv,full=False)
        args.update(kw);return attest(**args)
    def test_auth_and_repeated_hashes(self):
        a=self.call();b=self.call();self.assertEqual(a['canonical_sha256'],b['canonical_sha256'])
        self.assertEqual(a['typed_mark_shape'],[1800,4,2]);self.assertEqual(a['native_funding_events'],2)
        self.assertEqual(len(a['canonical_sha256']),5)
    def test_reject_untyped_conservative_mark(self):
        with self.assertRaises(ValueError):self.call(conservative=np.zeros((1800,4,2)))
    def test_reject_wrong_year(self):
        years=self.years.copy();years[100]=2025
        with self.assertRaises(ValueError):self.call(years=years)
    def test_reject_unattested_rate(self):
        rate=self.rate.copy();rate[8,0]*=-1
        with self.assertRaises(ValueError):self.call(rate=rate)
    def test_reject_event_missing(self):
        ev=self.event.copy();ev[16,1]=False
        with self.assertRaises(ValueError):self.call(event=ev)
    def test_reject_2025_calendar(self):
        idx=pd.date_range('2025-01-01',periods=1800,freq='h',tz='UTC')
        with self.assertRaises(ValueError):self.call(idx=idx,years=idx.year.to_numpy())
    def test_canonical_reject_nonquantized(self):
        x=compose_s(*self.frames)['S_full'].copy();x.iloc[1500,0]=.12345678
        with self.assertRaises(ValueError):canonical_target(x)
    def test_canonical_reject_gross(self):
        x=compose_s(*self.frames)['S_full'].copy();x.iloc[1500]=[.5,.5,.5,.5]
        with self.assertRaises(ValueError):canonical_target(x)
    def test_canonical_reject_nan(self):
        x=compose_s(*self.frames)['S_full'].copy();x.iloc[1500,0]=float('nan')
        with self.assertRaises(ValueError):canonical_target(x)

if __name__=='__main__':unittest.main()
