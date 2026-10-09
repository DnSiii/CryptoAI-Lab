"""V98 Independent Phase243 synthetic ZIP contract tests."""
import unittest
import tempfile
import zipfile
from pathlib import Path
import pandas as pd
from phase243_binance_archive_ingest import _parse_month

class ArchiveGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'BTCUSDT-1h-2023-01.zip'
    def tearDown(self):
        self.tmp.cleanup()
    def fixture(self, corrupt=False):
        idx=pd.date_range('2023-01-01T00:00:00Z', '2023-01-31T23:00:00Z', freq='h')
        ts=idx.as_unit('ns').asi8//1000000
        df=pd.DataFrame({'open_time':ts,'open':100.,'high':101.,'low':99.,
            'close':100.5,'volume':10.,'close_time':ts+3599999,
            'quote_volume':1000.,'trade_count':50,'taker_buy_base':9.9 if corrupt else 5.,
            'taker_buy_quote':980.1 if corrupt else 500.,'ignore':0})
        with zipfile.ZipFile(self.path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('BTCUSDT-1h-2023-01.csv',df.to_csv(index=False,header=False))
    def test_valid(self):
        self.fixture()
        rows,manifest=_parse_month(self.path,'BTCUSDT','2023-01')
        self.assertEqual(len(rows),744)
        self.assertEqual(len(manifest['archive_sha256']),64)
    def test_invalid_seller(self):
        self.fixture(corrupt=True)
        with self.assertRaisesRegex(ValueError,'seller VWAP'):
            _parse_month(self.path,'BTCUSDT','2023-01')

if __name__=='__main__':
    unittest.main()
