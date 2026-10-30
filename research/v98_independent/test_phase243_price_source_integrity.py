"""Adversarial synthetic V98-only canonical price source tests."""
import tempfile
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from phase243_price_source_integrity import ASSETS,audit_price_panel

class PricePanelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='v98_price_panel_')
        self.root=Path(self.tmp.name)
        self.start=pd.Timestamp('2025-01-01T00:00:00Z')
        self.cut=self.start+pd.Timedelta(days=3)
        self.warmup=24
        self.idx=pd.date_range(self.start-pd.Timedelta(hours=self.warmup),
                               self.cut-pd.Timedelta(hours=1),freq='h')
        self.write()
    def tearDown(self):self.tmp.cleanup()
    def write(self, edit=None):
        for j,a in enumerate(ASSETS):
            d=pd.DataFrame({'open_time':self.idx,'open':100+j,
                            'high':101+j,'low':99+j,'close':100.5+j,
                            'quote_volume':100000+j,'volume':(100000+j)/(100+j)},index=range(len(self.idx)))
            if edit:d=edit(a,d)
            d.to_csv(self.root/f'{a}_1h.csv',index=False)
    def run_gate(self):
        return audit_price_panel(self.root,self.start,self.cut,warmup_hours=self.warmup)
    def test_valid_panel_sha_and_schema(self):
        x=self.run_gate()
        self.assertEqual(len(x['opens']),96)
        self.assertEqual(len(x['manifest']['assets']),5)
        self.assertFalse(x['manifest']['holdout_accessed'])
        self.assertEqual(x['manifest']['assets']['BTCUSDT']['quote_volume_column'],'quote_volume')
    def test_deterministic_panel_hash(self):
        self.assertEqual(self.run_gate()['manifest']['panel_sha256'],self.run_gate()['manifest']['panel_sha256'])
    def test_missing_bar(self):
        self.write(lambda a,d:d.drop(index=9) if a=='BTCUSDT' else d)
        with self.assertRaisesRegex(ValueError,'hourly price bar'):self.run_gate()
    def test_duplicate_bar(self):
        self.write(lambda a,d:pd.concat([d,d.iloc[[4]]]).sort_values('open_time') if a=='ETHUSDT' else d)
        with self.assertRaisesRegex(ValueError,'duplicate'):self.run_gate()
    def test_future_row(self):
        self.write(lambda a,d:pd.concat([d,d.iloc[[-1]].assign(open_time=pd.Timestamp('2026-01-01T00:00:00Z'))]) if a=='SOLUSDT' else d)
        with self.assertRaisesRegex(ValueError,'holdout'):self.run_gate()
    def test_bad_candle_geometry(self):
        self.write(lambda a,d:d.assign(high=90) if a=='XRPUSDT' else d)
        with self.assertRaisesRegex(ValueError,'OHLC'):self.run_gate()
    def test_negative_quote_volume(self):
        self.write(lambda a,d:d.assign(quote_volume=-1) if a=='BNBUSDT' else d)
        with self.assertRaisesRegex(ValueError,'quote volume'):self.run_gate()
    def test_missing_quote_volume(self):
        self.write(lambda a,d:d.drop(columns='quote_volume') if a=='BNBUSDT' else d)
        with self.assertRaisesRegex(ValueError,'quote volume'):self.run_gate()
    def test_nonfinite_close(self):
        self.write(lambda a,d:d.assign(close=np.nan) if a=='SOLUSDT' else d)
        with self.assertRaisesRegex(ValueError,'nonfinite'):self.run_gate()
    def test_holdout_cut_requested(self):
        with self.assertRaisesRegex(ValueError,'holdout'):
            audit_price_panel(self.root,self.start,pd.Timestamp('2026-01-02T00:00:00Z'),warmup_hours=self.warmup)
    def test_out_of_order(self):
        self.write(lambda a,d:d.iloc[::-1] if a=='BTCUSDT' else d)
        with self.assertRaisesRegex(ValueError,'unordered'):self.run_gate()
    def test_quote_volume_alias(self):
        self.write(lambda a,d:d.rename(columns={'quote_volume':'quote_asset_volume'}))
        self.assertEqual(self.run_gate()['manifest']['assets']['BTCUSDT']['quote_volume_column'],'quote_asset_volume')
    def test_warmup_gap(self):
        self.write(lambda a,d:d.drop(index=0) if a=='BTCUSDT' else d)
        with self.assertRaisesRegex(ValueError,'hourly price bar'):self.run_gate()
    def test_missing_base_volume_rejected(self):
        self.write(lambda a,d:d.drop(columns='volume') if a=='BTCUSDT' else d)
        with self.assertRaisesRegex(ValueError,'base volume required'):self.run_gate()
    def test_quote_base_unit_swap_rejected(self):
        self.write(lambda a,d:d.assign(volume=d.quote_volume) if a=='BTCUSDT' else d)
        with self.assertRaisesRegex(ValueError,'unit inconsistency'):self.run_gate()
    def test_base_volume_alias_passes(self):
        self.write(lambda a,d:d.rename(columns={'volume':'base_asset_volume'}))
        self.assertEqual(self.run_gate()['manifest']['assets']['BTCUSDT']['base_volume_column'],'base_asset_volume')
    def test_zero_quote_volume_allowed_but_counted(self):
        self.write(lambda a,d:d.assign(quote_volume=0,volume=0) if a=='SOLUSDT' else d)
        self.assertEqual(self.run_gate()['manifest']['assets']['SOLUSDT']['zero_quote_volume_bars'],96)

if __name__=='__main__':unittest.main(verbosity=2)
