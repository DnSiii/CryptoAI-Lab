import csv
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from phase1190_ad_authenticated_core_source import parse_native, FIELDS, ASSETS


class NativeParserTests(unittest.TestCase):
    def setUp(self):
        self.idx=pd.date_range('2022-12-01T00:00:00Z',periods=24,freq='h')
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'native.csv'
        self.rows=[]
        for a in ASSETS:
            for t in (0,8,16):
                slot=int(self.idx[t].timestamp()*1000)
                self.rows.append([a,slot,slot,.0001,99,101,101])
        self.write()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self):
        with self.path.open('w',newline='') as stream:
            w=csv.writer(stream);w.writerow(FIELDS);w.writerows(self.rows)

    def test_exact_native_events(self):
        funding,event=parse_native(self.idx,self.path,strict=False)
        self.assertEqual(int(event.to_numpy().sum()),12)
        self.assertEqual(float(funding.iloc[8,0]),.0001)

    def test_duplicate_rejected(self):
        self.rows.append(self.rows[0]);self.write()
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):
            parse_native(self.idx,self.path,strict=False)

    def test_wrong_mark_sign_rejected(self):
        self.rows[0][-1]=99;self.write()
        with self.assertRaisesRegex(ValueError,'SIGNED'):
            parse_native(self.idx,self.path,strict=False)

    def test_invalid_clock_rejected(self):
        self.rows[0][1]+=3_600_000;self.write()
        with self.assertRaisesRegex(ValueError,'CLOCK'):
            parse_native(self.idx,self.path,strict=False)

    def test_wrong_asset_rejected(self):
        self.rows[0][0]='XRPUSDT';self.write()
        with self.assertRaisesRegex(ValueError,'NON_CLEAN4'):
            parse_native(self.idx,self.path,strict=False)

    def test_official_coverage_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'COVERAGE'):
            parse_native(self.idx,self.path,strict=True)


if __name__=='__main__':unittest.main()
