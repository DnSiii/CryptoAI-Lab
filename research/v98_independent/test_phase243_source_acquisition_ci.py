"""V98 Phase243 offline source falsification; fixtures are synthetic, never market data."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile
from urllib.error import HTTPError
import pandas as pd
from phase243_source_acquisition import acquire_one, BASE, _fetch_with_retry

class AcquisitionCI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'v98_independent'/'archives'
        self.asset, self.month = 'BTCUSDT', '2023-01'
        self.name = f'{self.asset}-1h-{self.month}.zip'
        self.url = f'{BASE}/{self.asset}/1h/{self.name}'
        idx = pd.date_range('2023-01-01T00:00:00Z', periods=744, freq='h')
        ts = idx.as_unit('ns').asi8//1_000_000
        frame = pd.DataFrame({'open_time':ts,'open':100.,'high':101.,'low':99.,'close':100.5,
            'volume':10.,'close_time':ts+3599999,'quote_volume':1000.,'trade_count':50,
            'taker_buy_base':5.,'taker_buy_quote':500.,'ignore':0})
        p = Path(self.tmp.name)/self.name
        with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(self.name.replace('.zip','.csv'),frame.to_csv(index=False,header=False))
        self.raw = p.read_bytes()
        self.sidecar = (hashlib.sha256(self.raw).hexdigest()+'  '+self.name+'\n').encode()
    def getter(self,url,limit):
        if url==self.url:return self.raw
        if url==self.url+'.CHECKSUM':return self.sidecar
        raise AssertionError('unexpected network target')
    def test_download_then_verified_cache(self):
        a=acquire_one(self.root,self.asset,self.month,getter=self.getter)
        self.assertEqual((a['rows'],a['status']),(744,'VERIFIED_DOWNLOAD'))
        b=acquire_one(self.root,self.asset,self.month,getter=lambda u,n:self.sidecar if u.endswith('.CHECKSUM') else self.fail('cache redownload'))
        self.assertEqual(b['status'],'VERIFIED_CACHE')
    def test_bad_sidecar_fails_closed(self):
        def bad(u,n):return b'bad' if u.endswith('.CHECKSUM') else self.raw
        with self.assertRaises(ValueError):acquire_one(self.root,self.asset,self.month,getter=bad)
    def test_corrupted_cache_is_replaced(self):
        acquire_one(self.root,self.asset,self.month,getter=self.getter)
        path=self.root/'klines'/self.asset/'1h'/self.name
        path.write_bytes(b'corrupt')
        self.assertEqual(acquire_one(self.root,self.asset,self.month,getter=self.getter)['status'],'VERIFIED_DOWNLOAD')
        self.assertEqual(path.read_bytes(),self.raw)
    def test_holdout_firewall(self):
        with self.assertRaises(ValueError):acquire_one(self.root,self.asset,'2026-01',getter=self.getter)
    def test_404_is_permanent(self):
        seen=[]
        def missing(u,n):
            seen.append(u);raise HTTPError(u,404,'not found',{},None)
        with self.assertRaises(HTTPError):_fetch_with_retry(missing,self.url,100,attempts=3,sleeper=lambda x:self.fail('must not retry'))
        self.assertEqual(len(seen),1)

if __name__=='__main__':unittest.main()
