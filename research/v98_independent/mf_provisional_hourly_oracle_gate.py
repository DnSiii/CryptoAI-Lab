#!/usr/bin/env python3
"""MF provisional-only independent all-hour settlement replay and receipt reconciliation."""
import argparse,json,math
from pathlib import Path
from v98_clean4_training_reader import load
from v98_mark_envelope_settlement import read_envelope
from v98_independent_hourly_settlement_oracle import replay
def run(root,envelope,ledger,receipt):
    r=json.loads(Path(receipt).read_text())
    if r.get('architecture')!='MF' or r.get('decision')!='PASS_PROVISIONAL_TRAINING_NOT_VALIDATED':
        raise ValueError('MF_ORACLE_NOT_PROVISIONAL')
    if len(r['cells'])!=30 or r['source_gate']['decision']!='PASS_SOURCE_ONLY':
        raise ValueError('MF_ORACLE_INVALID_RECEIPT')
    cell=next(z for z in r['cells'] if z['book']=='MF_full' and
              z['tier']=='base' and z['order']=='carried_before_fill')
    if not cell['passed']:raise ValueError('MF_ORACLE_FAILED_PHYSICAL_CELL')
    d=load(root);lo,hi,_=read_envelope(envelope,d)
    with open(ledger) as f:
        result=replay(d,(json.loads(line) for line in f),lo,hi,
                      .0004,.0002,'carried_before_fill')
    for name in ('final_equity','turnover','fees','slippage','funding'):
        if not math.isclose(result[name],cell[name],rel_tol=1e-9,abs_tol=1e-5):
            raise ValueError('MF_ORACLE_INDEPENDENT_'+name.upper()+'_MISMATCH')
    result['decision']='PASS_PROVISIONAL_INDEPENDENT_BASE_FULL_ALL_HOUR_ACCOUNTING_NOT_STRATEGY_ORACLE'
    result['strategy_signals_independently_replayed']=False
    result['2025_validation_accessed']=False
    result['future_holdout_accessed']=False
    result['live_authorized']=False
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('root','envelope-csv','ledger-jsonl','receipt','output'):
        p.add_argument('--'+key,required=True)
    a=p.parse_args()
    result=run(a.root,a.envelope_csv,a.ledger_jsonl,a.receipt)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
