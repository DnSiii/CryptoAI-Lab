"""Phase195-E structural continuity adversarial tests; synthetic only."""
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

p=Path(__file__).resolve().parents[1]/'tools'/'v99_phase195_train_coverage_structural.py'
spec=importlib.util.spec_from_file_location('coverage_gate',p)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
S=1700000000
DAY=86400
H=lambda i:'0x'+format(i,'064x')
rows=[]
for i,stamp in enumerate([S-1,S,S+DAY,S+2*DAY,S+3*DAY,S+4*DAY,S+5*DAY,S+6*DAY]):
    inside=S<=stamp<S+6*DAY
    row={'height':17000000+i,'hash':H(i+10),'parent_hash':H(i+9),
         'timestamp':stamp,'header_only':not inside,
         'receipts_root':H(100+i) if inside else None,
         'native_event_count':0 if inside else None,
         'native_event_sha256':('a'*64) if inside else None}
    if inside:row.update({k:True for k in (
        'local_receipts_root_checked','all_receipts_present',
        'both_native_topics_checked','all_unrelated_logs_included')})
    rows.append(row)


def run(a,b):
    with tempfile.TemporaryDirectory() as tmp:
        paths=[Path(tmp)/'a.jsonl',Path(tmp)/'b.jsonl']
        for path,rr,op in zip(paths,(a,b),('operatorA','operatorB')):
            path.write_text(''.join(json.dumps(dict(z,operator=op),sort_keys=True)+'\n' for z in rr))
        return m.verify_pair(*paths,start=S,end=S+6*DAY,interior_days=4,folds=2)

assert run(rows,rows)['interior_train_days']==4
assert run(rows,rows)['chronological_fold_days']==[2,2]
assert run(rows,rows)['no_economic_trial_authorized'] is True
cases={}

def must_reject(name,a,b,reason):
    try:run(a,b)
    except ValueError as exc:assert str(exc)==reason,(name,str(exc),reason)
    else:raise AssertionError('mutation_accepted:'+name)
    cases[name]=reason

x=copy.deepcopy(rows);x.pop(3);must_reject('missing_block',x,x,'header_chain_gap_or_reorg')
x=copy.deepcopy(rows);x[3]['hash']=H(999);must_reject('operator_mismatch',rows,x,'operator_disagreement_hash')
x=copy.deepcopy(rows);x[3]['parent_hash']=H(999);must_reject('broken_link',x,x,'header_chain_gap_or_reorg')
x=copy.deepcopy(rows);x[3]['timestamp']=S+4*DAY+10;must_reject('timestamp_disorder',x,x,'nonincreasing_block_timestamp')
x=copy.deepcopy(rows);x[3]['all_unrelated_logs_included']=False;must_reject('unproven_receipts',x,x,'unproven_complete_block')
x=copy.deepcopy(rows);x[0]['native_event_count']=0;must_reject('outside_train_event_query',x,x,'sentinel_contains_out_of_train_events')
x=copy.deepcopy(rows);x.pop();must_reject('missing_end_sentinel',x,x,'missing_after_boundary_header_sentinel')
x=copy.deepcopy(rows);x[3]['native_event_count']=1;must_reject('event_count_disagreement',rows,x,'operator_disagreement_native_event_count')
x=copy.deepcopy(rows);x[3]['timestamp']=S+DAY+1;must_reject('missing_calendar_day',x,x,'missing_train_calendar_day')
print(json.dumps({'decision':'PASS_PHASE195E_SYNTHETIC_CONTINUITY',
                  'negative_controls':cases,'economic_trials':0,
                  'real_chain_verified':False},sort_keys=True))
