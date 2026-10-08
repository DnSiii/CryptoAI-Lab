"""Phase195-F standalone fail-closed source-input tests; synthetic only."""
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

path = Path(__file__).resolve().parents[1]/'tools'/'v99_phase195f_input_firewall.py'
spec = importlib.util.spec_from_file_location('phase195f_firewall', path)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
H = lambda i:'0x'+format(i,'064x')
rows = [dict(operator='A',height=17_000_000+i,hash=H(i+10),
             parent_hash=H(i+9),timestamp=t,header_only=i!=1,
             receipts_root=H(100) if i==1 else None,
             native_event_count=0 if i==1 else None,
             native_event_sha256='a'*64 if i==1 else None)
        for i,t in enumerate((m.START-1,m.START,m.END))]
rows[1].update({key:True for key in m.FLAGS})


def run(rr, raw=None):
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'a.jsonl'
        lines=[json.dumps(x,sort_keys=True) for x in rr]
        if raw is not None: lines[1]=raw
        p.write_text('\n'.join(lines)+'\n')
        return m.verify(p)

assert run(rows)['no_economic_trial_authorized']
for s in ('0x+1','0x1_0','0x01','0xA','0x1 ','0x'):
    try: m.canonical_quantity(s)
    except ValueError: pass
    else: raise AssertionError('quantity_accepted:'+s)
assert m.canonical_quantity('0xff')==255
failures={}

def reject(name,rr,expected,raw=None):
    try:run(rr,raw)
    except ValueError as e:assert str(e)==expected,(name,str(e))
    else:raise AssertionError('mutation_accepted:'+name)
    failures[name]=expected

x=copy.deepcopy(rows);x[1]['timestamp']=x[0]['timestamp']
reject('equal_timestamp',x,'nonincreasing_block_timestamp')
x=copy.deepcopy(rows);x[0]['native_event_sha256']='a'*64
reject('sentinel_digest',x,'sentinel_contains_out_of_train_receipt_claim')
x=copy.deepcopy(rows);x[2]['all_receipts_present']=True
reject('sentinel_flag',x,'sentinel_contains_out_of_train_receipt_claim')
x=copy.deepcopy(rows);x[1]['parent_hash']=H(999)
reject('broken_parent',x,'header_chain_gap_or_reorg')
raw=json.dumps(rows[1])[:-1]+',"height":0}'
reject('duplicate_key',rows,'duplicate_json_key:height',raw)
raw=json.dumps(rows[1])[:-1]+',"unknown":NaN}'
reject('nonfinite_json',rows,'nonfinite_json_number:NaN',raw)
print(json.dumps({'decision':'PASS_PHASE195F_STANDALONE_SYNTHETIC',
    'rejections':failures,'economic_trials':0,'real_chain_verified':False},sort_keys=True))
