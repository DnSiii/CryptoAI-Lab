import json,unittest
from pathlib import Path
from phase1143_z_sevenslot_source import PATHS,CAPITAL
from phase1148_z_pre_economic_lock import lock

class TestFreeze(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).resolve().parent
        self.r={'decision':'PASS_Z_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN',
            'historical_pnl_computed':False,'validation_2025_read':False,
            'holdout_accessed':False,'external_benchmarks_used':False,
            'official_hours':18288,'native_funding_events':9144,
            'typed_mark_shape':[18288,4,2],
            'canonical_sha256':{p+'__'+m:'a'*64 for p in PATHS for m in CAPITAL},
            'typed_mark_csv_sha256':'b'*64,'diagnostics':{'regime_hours':{}},
            'governor_calls':{}}
    def test_four_identical_pre_economic_receipts(self):
        m=lock([self.r.copy() for _ in range(4)],self.root)
        self.assertEqual(len(m['canonical_sha256']),15)
        self.assertFalse(m['historical_pnl_computed'])
        self.assertEqual(len(m['code_blob_sha1']),5)
    def test_mismatch_rejected(self):
        other=json.loads(json.dumps(self.r));other['canonical_sha256']['Z_full__immediate']='c'*64
        with self.assertRaisesRegex(PermissionError,'RUNNER_DRIFT'):
            lock([self.r,self.r,other,self.r],self.root)
    def test_missing_receipt_rejected(self):
        with self.assertRaisesRegex(PermissionError,'FOUR'):
            lock([self.r]*3,self.root)
    def test_future_access_rejected(self):
        other=dict(self.r,validation_2025_read=True)
        with self.assertRaisesRegex(PermissionError,'PROVENANCE'):
            lock([self.r,self.r,other,self.r],self.root)
    def test_non_namespaced_code_rejected(self):
        with self.assertRaisesRegex(PermissionError,'NON_NAMESPACED'):
            lock([self.r]*4,self.root,('../v99.py',))

if __name__=='__main__':unittest.main()
