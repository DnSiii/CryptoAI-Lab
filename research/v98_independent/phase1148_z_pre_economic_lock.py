#!/usr/bin/env python3
"""Z source-only immutable manifest builder; NO economic PnL or 2025 data."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from phase1143_z_sevenslot_source import PATHS,CAPITAL

REQUIRED_FILES=(
    'phase1143_z_sevenslot_source.py',
    'phase1145_z_authenticated_source.py',
    'phase1146_z_inventory_ledger.py',
    'phase1147_z_ledger_adversarial.py',
    'phase1148_z_pre_economic_lock.py',
)

def blob_sha(path):
    raw=Path(path).read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()

def lock(receipts,root,extra_code=()):
    """Require four independent source-only attestations; no PnL before freeze."""
    if len(receipts)!=4:raise PermissionError('Z1148_FOUR_SOURCE_RECEIPTS_REQUIRED')
    rr=[json.loads(Path(p).read_text()) if isinstance(p,(str,Path)) else p for p in receipts]
    expected={p+'__'+m for p in PATHS for m in CAPITAL}
    for r in rr:
        if (r.get('decision')!='PASS_Z_AUTHENTICATED_SOURCE_ONLY_NOT_FROZEN'
            or r.get('historical_pnl_computed') is not False
            or r.get('validation_2025_read') is not False
            or r.get('holdout_accessed') is not False
            or r.get('external_benchmarks_used') is not False
            or r.get('official_hours')!=18288 or r.get('native_funding_events')!=9144
            or r.get('typed_mark_shape')!=[18288,4,2]
            or set(r.get('canonical_sha256',{}))!=expected
            or not all(isinstance(x,str) and len(x)==64 for x in r['canonical_sha256'].values())):
            raise PermissionError('Z1148_SOURCE_PROVENANCE_OR_GEOMETRY')
    for field in ('canonical_sha256','typed_mark_csv_sha256','native_funding_events',
                  'official_hours','diagnostics','governor_calls'):
        if any(r[field]!=rr[0][field] for r in rr[1:]):
            raise PermissionError('Z1148_INDEPENDENT_RUNNER_DRIFT_'+field)
    base=Path(root)
    files=tuple(dict.fromkeys(REQUIRED_FILES+tuple(extra_code)))
    for f in files:
        if '/' in f or '..' in f or not f.startswith('phase') or not f.endswith('.py'):
            raise PermissionError('Z1148_NON_NAMESPACED_CODE')
    hashes={f:blob_sha(base/f) for f in files}
    return {'phase':1148,'decision':'FROZEN_Z_SOURCE_AND_EXECUTION_PRE_ECONOMIC',
        'source_receipt_count':4,'canonical_sha256':rr[0]['canonical_sha256'],
        'typed_mark_csv_sha256':rr[0]['typed_mark_csv_sha256'],
        'native_funding_events':9144,'typed_mark_shape':[18288,4,2],
        'official_hours':18288,'code_blob_sha1':hashes,
        'path_order':list(PATHS),'capital_modes':CAPITAL,
        'fee_tiers':{'base':.0007,'severe':.0012,'supersevere':.002},
        'funding_orders':['carried_before_fill','new_after_fill'],
        'training_folds':[2023,2024],'historical_pnl_computed':False,
        'validation_2025_read':False,'holdout_accessed':False,
        'external_benchmarks_used':False,'promotion_eligible':False}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('receipts',nargs=4)
    p.add_argument('--root',default=str(Path(__file__).resolve().parent))
    p.add_argument('--out',required=True)
    p.add_argument('--extra-code',action='append',default=[])
    a=p.parse_args()
    result=lock(a.receipts,a.root,a.extra_code)
    Path(a.out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'decision':result['decision'],
        'target_count':len(result['canonical_sha256']),
        'code_files':len(result['code_blob_sha1'])},sort_keys=True))
