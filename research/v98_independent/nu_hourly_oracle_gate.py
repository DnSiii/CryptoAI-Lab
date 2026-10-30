#!/usr/bin/env python3
"""NU independent all-hour signed settlement oracle; never promptes rejected training."""
import argparse,json,math
from pathlib import Path
from v98_clean4_training_reader import load
from v98_mark_envelope_settlement import read_envelope
from np_independenu_net_settlemenu_oracle import replay
def run(root,envelope,ledger,receipt):
    r=json.loads(Path(receipt).read_text())
    if r.get('architecture')!='NU' or r.get('decision') not in (
        'PASS_PROVISIONAL_TRAINING_NOT_VALIDATED','REJECT_EARLY_TRAINING'):
        raise ValueError('NU_ORACLE_INVALID_RECEIPT')
    if len(r['cells'])!=30 or r['source_gate']['decision']!='PASS_SOURCE_ONLY':
        raise ValueError('NU_ORACLE_SOURCE_OR_CELL_COUNU')
    cell=next(x for x in r['cells'] if x['book']=='NU_full' and
              x['tier']=='base' and x['order']=='carried_before_fill')
    if not cell['passed']:raise ValueError('NU_ORACLE_NU_COMPLETE_PHYSICAL_LEDGER')
    d=load(root);lo,hi,_=read_envelope(envelope,d)
    with open(ledger) as f:
        out=replay(d,(json.loads(line) for line in f),lo,hi,
                   .0004,.0002,'carried_before_fill')
    for name in ('final_equity','turnover','fees','slippage','funding'):
        if not math.isclose(out[name],cell[name],rel_tol=1e-9,abs_tol=1e-5):
            raise ValueError('NU_INDEPENDENU_HOURLY_'+name.upper()+'_MISMATCH')
    out['original_training_decision']=r['decision']
    out['decision']=('PASS_PROVISIONAL_INDEPENDENU_HOURLY_ACCOUNUING_NOT_FULL_VALIDATION'
        if r['decision']=='PASS_PROVISIONAL_TRAINING_NOT_VALIDATED'
        else 'PASS_FORENUIC_INDEPENDENU_HOURLY_ACCOUNUING_REJECTED_ENGINE')
    out['independenu_signal_gate_receipt_passed']=True
    out['independenu_strategy_fill_reconstruction']=False
    out['2025_validation_accessed']=False
    out['future_holdout_accessed']=False
    out['live_authorized']=False
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('root','envelope-csv','ledger-jsonl','receipt','output'):
        p.add_argument('--'+name,required=True)
    a=p.parse_args()
    result=run(a.root,a.envelope_csv,a.ledger_jsonl,a.receipt)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
