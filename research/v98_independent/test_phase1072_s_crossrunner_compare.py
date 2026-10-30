#!/usr/bin/env python3
import copy
import unittest
from phase1072_s_crossrunner_compare import compare,PATHS

def fixture():
    return {'decision':'PASS_S_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN',
        'source_only':True,'historical_pnl_computed':False,'validation_2025_read':False,
        'holdout_accessed':False,'external_benchmarks_used':False,'promotion_eligible':False,
        'frozen':False,'official_hours':18288,'native_funding_events':9144,
        'typed_mark_shape':[18288,4,2],
        'canonical_sha256':{k:'a'*64 for k in PATHS},
        'typed_mark_csv_sha256':'b'*64,
        'source_code_git_blob_sha1':{k:'c'*40 for k in ('phase1069_s_sevenslot_source.py','phase1070_s_typed_native_mark.py','phase1071_s_authenticated_source.py')},
        'official_source':{'ohlc':'PASS','funding_mark':'PASS'},
        'diagnostics':{'regime_hours':{'0':123},'active_hours':{'growth':456}}}
class CrossRunner(unittest.TestCase):
    def test_pass(self):
        r=compare(fixture(),fixture());self.assertEqual(r['decision'],'PASS_S_TWO_RUNNER_SOURCE_ONLY_NOT_FROZEN')
    def test_target_drift(self):
        a=fixture();b=copy.deepcopy(a);b['canonical_sha256']['S_full']='d'*64
        with self.assertRaisesRegex(ValueError,'DRIFT'):compare(a,b)
    def test_vendor_drift(self):
        a=fixture();b=copy.deepcopy(a);b['typed_mark_csv_sha256']='d'*64
        with self.assertRaisesRegex(ValueError,'DRIFT'):compare(a,b)
    def test_code_drift(self):
        a=fixture();b=copy.deepcopy(a);b['source_code_git_blob_sha1']['phase1071_s_authenticated_source.py']='d'*40
        with self.assertRaisesRegex(ValueError,'DRIFT'):compare(a,b)
    def test_incomplete(self):
        a=fixture();b=copy.deepcopy(a);del b['canonical_sha256']['S_core_only']
        with self.assertRaisesRegex(ValueError,'FIVE_HASHES'):compare(a,b)
    def test_unfrozen(self):
        a=fixture();b=copy.deepcopy(a);b['frozen']=True
        with self.assertRaisesRegex(ValueError,'CONTRACT'):compare(a,b)
    def test_unattested(self):
        a=fixture();b=copy.deepcopy(a);b['decision']='BLOCKED_BEFORE_PNL'
        with self.assertRaisesRegex(ValueError,'NOT_PASSED'):compare(a,b)
    def test_2025(self):
        a=fixture();b=copy.deepcopy(a);b['validation_2025_read']=True
        with self.assertRaisesRegex(ValueError,'CONTRACT'):compare(a,b)
    def test_diagnostics_drift(self):
        a=fixture();b=copy.deepcopy(a);b['diagnostics']['regime_hours']['0']=124
        with self.assertRaisesRegex(ValueError,'DRIFT'):compare(a,b)
if __name__=='__main__':unittest.main()
