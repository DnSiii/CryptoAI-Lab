#!/usr/bin/env python3
"""JQ source-only deterministic parser/chronology/checksum/1h reconciliation tests."""
from __future__ import annotations
import calendar,csv,hashlib,io,unittest,zipfile
from datetime import datetime,timezone
import numpy as np
from jq_native_5m_path_source import parse_month,verify_archive,compare_1h,RAW

ASSET="BTCUSDT";MONTH="2022-12"
NAME=f"{ASSET}-5m-{MONTH}.zip"

def synthetic(header=True):
    first=int(datetime(2022,12,1,tzinfo=timezone.utc).timestamp()*1000)
    n=calendar.monthrange(2022,12)[1]*24*12
    rows=[]
    for i in range(n):
        op=100.+i*.0001;cl=op+.00005
        rows.append([first+i*300000,op,op+.0001,op-.0001,cl,1.,
                     first+i*300000+299999,100.,1,0.5,50.,"0"])
    out=io.StringIO();w=csv.writer(out)
    if header:w.writerow(RAW)
    w.writerows(rows)
    return rows,out.getvalue().encode()

def zipped(data):
    f=io.BytesIO()
    with zipfile.ZipFile(f,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(NAME[:-4]+".csv",data)
    return f.getvalue()

class JQNativePathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.data=synthetic()
    def test_vendor_sha_and_source_features(self):
        raw=zipped(self.data)
        sidecar=(hashlib.sha256(raw).hexdigest()+"  "+NAME+"\n").encode()
        data,sha,member=verify_archive(raw,sidecar,NAME)
        self.assertEqual(sha,hashlib.sha256(raw).hexdigest())
        self.assertEqual(member,hashlib.sha256(data).hexdigest())
        ts,hourly,features=parse_month(data,ASSET,MONTH)
        self.assertEqual(len(ts),744)
        self.assertEqual(hourly.shape,(744,5))
        self.assertEqual(features.shape,(744,6))
        self.assertTrue(np.isfinite(features).all())
        self.assertTrue(np.allclose(features[:,4:],.5))
        self.assertEqual(compare_1h(hourly,hourly.copy()),[0.]*5)
        with self.assertRaisesRegex(ValueError,"JQ_PINNED_1H_RECONCILIATION"):
            altered=hourly.copy();altered[15,4]+=100.
            compare_1h(hourly,altered)
    def test_bad_vendor_sha_rejected(self):
        raw=zipped(self.data)
        with self.assertRaisesRegex(ValueError,"JQ_VENDOR_SHA256_MISMATCH"):
            verify_archive(raw,("0"*64+"  "+NAME).encode(),NAME)
    def test_missing_or_reordered_5m_rejected(self):
        rows=self.rows.copy()
        rows[25],rows[26]=rows[26],rows[25]
        buf=io.StringIO();w=csv.writer(buf);w.writerow(RAW);w.writerows(rows)
        with self.assertRaisesRegex(ValueError,"JQ_5M_UTC_ORDER"):
            parse_month(buf.getvalue().encode(),ASSET,MONTH)
        rows=self.rows[:-1]
        buf=io.StringIO();w=csv.writer(buf);w.writerow(RAW);w.writerows(rows)
        with self.assertRaisesRegex(ValueError,"JQ_5M_UTC_ORDER"):
            parse_month(buf.getvalue().encode(),ASSET,MONTH)
    def test_no_header_and_invalid_geometry(self):
        rows,raw=synthetic(header=False)
        self.assertEqual(parse_month(raw,ASSET,MONTH)[2].shape,(744,6))
        rows[40][3]=rows[40][2]+1
        buf=io.StringIO();w=csv.writer(buf);w.writerows(rows)
        with self.assertRaisesRegex(ValueError,"JQ_NATIVE_5M_GEOMETRY"):
            parse_month(buf.getvalue().encode(),ASSET,MONTH)
    def test_future_mutation_does_not_change_completed_hour(self):
        ts,ohlc,feat=parse_month(self.data,ASSET,MONTH)
        rows=self.rows.copy();rows[-1]=rows[-1].copy()
        rows[-1][1]=150.;rows[-1][2]=151.;rows[-1][3]=149.;rows[-1][4]=150.
        buf=io.StringIO();w=csv.writer(buf);w.writerow(RAW);w.writerows(rows)
        changed=parse_month(buf.getvalue().encode(),ASSET,MONTH)
        self.assertTrue(np.array_equal(feat[:-1],changed[2][:-1],equal_nan=True))
        self.assertFalse(np.array_equal(feat[-1],changed[2][-1]))
if __name__=="__main__":
    unittest.main()
