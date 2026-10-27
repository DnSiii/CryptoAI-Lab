"""V98 Independent Phase243 synthetic ZIP contract tests."""
import unittest
import tempfile
import zipfile
from pathlib import Path
import pandas as pd
from phase243_binance_archive_ingest import _parse_month
# Reuse the existing V98-only Phase243 CI runner for HQ offline source-contract fixtures.
# This imports tests only; it never downloads spot archives, opens holdout or runs PnL.
from test_hq_gap_aware_spot_source import HQSourceFixtures
from test_hq_independent_receipt_reconcile import HQIndependentReconcileTests

class ArchiveGateTests(unittest.TestCase):
    def test_hq_training_only_firewall_and_quarantined_xrp(self):
        from hq_gap_aware_spot_source import ASSETS, MONTHS
        self.assertEqual(ASSETS, ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT'))
        self.assertEqual(MONTHS[0], (2022, 12))
        self.assertEqual(MONTHS[-1], (2024, 12))
        self.assertEqual(len(MONTHS), 25)

    def test_hq_mask_is_explicit_and_cannot_promote_old_grid(self):
        from hq_gap_aware_spot_source import ASSETS, KNOWN_GAPS, GAP, PINNED_100_SHA_MANIFEST
        self.assertEqual(KNOWN_GAPS, {(asset, GAP) for asset in ASSETS})
        self.assertEqual(len(PINNED_100_SHA_MANIFEST), 64)
        self.assertNotEqual(PINNED_100_SHA_MANIFEST, "0" * 64)

    def test_hq_independent_receipt_and_source_pins_agree(self):
        from hq_gap_aware_spot_source import PINNED_100_SHA_MANIFEST
        from hq_independent_receipt_reconcile import PINNED_MANIFEST
        self.assertEqual(PINNED_100_SHA_MANIFEST, PINNED_MANIFEST)

    def test_hq_partial_close_pins_match_independent_forensic(self):
        from hq_gap_aware_spot_source import PINNED_PARTIAL_CLOSE, PARTIAL_OPEN, GAP
        from hq_independent_receipt_reconcile import PINNED_PARTIAL_CLOSE as AUDIT_PIN
        self.assertEqual(PINNED_PARTIAL_CLOSE, AUDIT_PIN)
        self.assertEqual(PARTIAL_OPEN + 3600000, GAP)
        self.assertEqual(len(PINNED_PARTIAL_CLOSE), 4)

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
    def _with_header(self, header, *, bom=False):
        self.fixture()
        with zipfile.ZipFile(self.path,'r') as z:
            raw=z.read('BTCUSDT-1h-2023-01.csv')
        prefix=b'\xef\xbb\xbf' if bom else b''
        with zipfile.ZipFile(self.path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('BTCUSDT-1h-2023-01.csv',prefix+(','.join(header)+'\n').encode()+raw)

    def test_usdm_historical_header(self):
        header=('open_time','open','high','low','close','volume','close_time',
                'quote_asset_volume','count','taker_buy_volume','taker_buy_quote_volume','ignore')
        self._with_header(header)
        rows,ev=_parse_month(self.path,'BTCUSDT','2023-01')
        self.assertEqual(len(rows),744)
        self.assertTrue(ev['header_present'])

    def test_usdm_quote_volume_header_with_bom(self):
        header=('open_time','open','high','low','close','volume','close_time',
                'quote_volume','count','taker_buy_volume','taker_buy_quote_volume','ignore')
        self._with_header(header,bom=True)
        rows,ev=_parse_month(self.path,'BTCUSDT','2023-01')
        self.assertEqual(len(rows),744)
        self.assertTrue(ev['header_present'])

    def test_usdm_header_reordering_rejected(self):
        header=('open_time','open','high','low','close','volume','close_time',
                'quote_asset_volume','taker_buy_volume','count','taker_buy_quote_volume','ignore')
        self._with_header(header)
        with self.assertRaisesRegex(ValueError,'unrecognized or reordered CSV header'):
            _parse_month(self.path,'BTCUSDT','2023-01')

    def test_usdm_unknown_header_rejected(self):
        header=('open_time','open','high','low','close','volume','close_time',
                'quote_asset_volume','count','mystery','taker_buy_quote_volume','ignore')
        self._with_header(header)
        with self.assertRaisesRegex(ValueError,'unrecognized or reordered CSV header'):
            _parse_month(self.path,'BTCUSDT','2023-01')

    def test_quote_volume_violation_has_bounded_source_witness(self):
        self.fixture()
        with zipfile.ZipFile(self.path,'r') as z:
            raw=z.read('BTCUSDT-1h-2023-01.csv')
        lines=raw.decode().splitlines()
        first=lines[0].split(',')
        first[7]='2000'
        lines[0]=','.join(first)
        with zipfile.ZipFile(self.path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('BTCUSDT-1h-2023-01.csv','\n'.join(lines)+'\n')
        with self.assertRaisesRegex(ValueError,'row=0 .*base=10 .*quote=2000 .*violations=1'):
            _parse_month(self.path,'BTCUSDT','2023-01')

    def test_invalid_seller(self):
        self.fixture(corrupt=True)
        with self.assertRaisesRegex(ValueError,'seller VWAP'):
            _parse_month(self.path,'BTCUSDT','2023-01')

if __name__=='__main__':
    unittest.main()
