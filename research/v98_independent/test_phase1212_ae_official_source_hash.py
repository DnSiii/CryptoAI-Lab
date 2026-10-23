import csv
import tempfile
import unittest
from pathlib import Path
import numpy as np
from test_phase1205_ae_breakout_source import sample
from phase1205_ae_breakout_source import ae_breakout_source
from phase1212_ae_official_source_hash import (
    PATHS,MODES,FIELDS,static_hash,parse_native)


def native_rows(index,duplicate=False,asset='BTCUSDT',mark='101'):
    slot=int(index[0].timestamp()*1000)
    row=dict(asset=asset,funding_slot_ms=str(slot),
             funding_time_ms=str(slot+10),funding_rate='.0001',
             mark_low='99',mark_high='101',conservative_mark=mark)
    return [row,row.copy()] if duplicate else [row]


class AEOfficialSourceStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames=sample(900)
        cls.outputs=ae_breakout_source(*cls.frames)
        cls.index=cls.frames[0].index

    def test_fifteen_path_mode_hashes_distinct(self):
        hashes=[static_hash(self.index,self.outputs,p,m)
                for p in PATHS for m in MODES]
        self.assertEqual(len(hashes),15)
        self.assertEqual(len(set(hashes)),15)
        self.assertTrue(all(len(h)==64 for h in hashes))

    def test_hash_determinism_and_path_independence(self):
        a=static_hash(self.index,self.outputs,'AE_full','immediate')
        b=static_hash(self.index,self.outputs,'AE_full','immediate')
        self.assertEqual(a,b)
        self.assertNotEqual(a,static_hash(self.index,self.outputs,
                                         'AE_core_only','immediate'))

    def test_invalid_path_rejected(self):
        with self.assertRaisesRegex(ValueError,'PATH_MODE'):
            static_hash(self.index,self.outputs,'AD_full','immediate')

    def write_native(self,rows):
        f=tempfile.NamedTemporaryFile(mode='w',suffix='.csv',delete=False,newline='')
        with f:
            writer=csv.DictWriter(f,fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        self.addCleanup(lambda:Path(f.name).unlink(missing_ok=True))
        return f.name

    def test_native_signed_event_parser(self):
        p=self.write_native(native_rows(self.index))
        rate,event,lo,hi=parse_native(self.index,p,strict=False)
        self.assertEqual(int(event.to_numpy().sum()),1)
        self.assertAlmostEqual(rate.iloc[0,0],.0001)
        self.assertAlmostEqual(lo[0,0],99)
        self.assertAlmostEqual(hi[0,0],101)
        self.assertTrue(np.isnan(lo[1,0]))

    def test_duplicate_native_event_rejected(self):
        p=self.write_native(native_rows(self.index,duplicate=True))
        with self.assertRaisesRegex(ValueError,'DUPLICATE_NATIVE_EVENT'):
            parse_native(self.index,p,strict=False)

    def test_non_clean4_or_bad_signed_mark_rejected(self):
        p=self.write_native(native_rows(self.index,asset='XRPUSDT'))
        with self.assertRaisesRegex(ValueError,'NON_CLEAN4'):
            parse_native(self.index,p,strict=False)
        p=self.write_native(native_rows(self.index,mark='99'))
        with self.assertRaisesRegex(ValueError,'NATIVE_SIGNED_MARK'):
            parse_native(self.index,p,strict=False)


if __name__=='__main__':unittest.main()
