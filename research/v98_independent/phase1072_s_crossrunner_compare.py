#!/usr/bin/env python3
"""V98 Independent S strict two-OS receipt comparison, no PnL or freeze.

A successful runner alone never licenses a freeze; both official source runs
must independently attest identical typed vendor data and target bytes.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

PATHS=('S_core_only','S_full','S_minus_opportunity','S_minus_relative_value','S_minus_recovery')
REQUIRED={'source_only':True,'historical_pnl_computed':False,'validation_2025_read':False,
          'holdout_accessed':False,'external_benchmarks_used':False,
          'promotion_eligible':False,'frozen':False,'official_hours':18288,
          'native_funding_events':9144,'typed_mark_shape':[18288,4,2]}
def compare(a,b):
    for label,x in (('first',a),('second',b)):
        if x.get('decision')!='PASS_S_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN':
            raise ValueError('S_RUNNER_NOT_PASSED_'+label)
        for key,value in REQUIRED.items():
            if type(x.get(key)) is not type(value) or x.get(key)!=value:
                raise ValueError('S_RUNNER_CONTRACT_'+label+'_'+key)
        h=x.get('canonical_sha256',{})
        if not isinstance(h,dict) or tuple(h)!=PATHS or any(not isinstance(v,str) or len(v)!=64 for v in h.values()):
            raise ValueError('S_RUNNER_FIVE_HASHES_'+label)
        code=x.get('source_code_git_blob_sha1',{})
        if (not isinstance(code,dict) or len(code)!=3 or
            any(not isinstance(v,str) or len(v)!=40 for v in code.values())):
            raise ValueError('S_RUNNER_CODE_BLOBS_'+label)
        if not isinstance(x.get('typed_mark_csv_sha256'),str) or len(x['typed_mark_csv_sha256'])!=64:
            raise ValueError('S_RUNNER_VENDOR_CSV_SHA_'+label)
    for key in ('canonical_sha256','typed_mark_csv_sha256','source_code_git_blob_sha1',
                'official_source','diagnostics'):
        if a.get(key)!=b.get(key):raise ValueError('S_CROSSRUNNER_DRIFT_'+key)
    return {'decision':'PASS_S_TWO_RUNNER_SOURCE_ONLY_NOT_FROZEN',
            'target_hashes':a['canonical_sha256'],
            'typed_mark_csv_sha256':a['typed_mark_csv_sha256'],
            'code_blobs':a['source_code_git_blob_sha1'],
            'official_hours':18288,'native_funding_events':9144,
            'historical_pnl_computed':False,'validation_2025_read':False,
            'external_benchmarks_used':False,'frozen':False}
def main(args):
    result={'decision':'BLOCKED_S_CROSSRUNNER_NO_FREEZE','historical_pnl_computed':False,
            'validation_2025_read':False,'external_benchmarks_used':False,'frozen':False}
    try:
        if len(args)!=3:raise ValueError('S_CROSSRUNNER_EXPECTS_TWO_RECEIPTS_AND_OUTPUT')
        a=json.loads(Path(args[0]).read_text());b=json.loads(Path(args[1]).read_text())
        result=compare(a,b)
    except Exception as e:
        result['reason']=type(e).__name__+': '+str(e)[:250]
    out=Path(args[2]) if len(args)>=3 else Path('phase1072_s_crossrunner_comparison.json')
    out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'decision':result['decision'],'reason':result.get('reason')},sort_keys=True))
    return 0 if result['decision'].startswith('PASS_') else 2
if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
