#!/usr/bin/env python3
"""V98 NO 2025 independent read-only signed all-hour settlement oracle.
Imports frozen training-era independent accounting replay, NEVER 2025 physical runner.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_no_2025_validation_reader import load,TRAIN_HOURS,TOTAL,HOURS_2025
from no_independent_net_settlement_oracle import replay,synthetic_tests

def run(training_root,validation_root,ledger_path,receipt_path):
    assert synthetic_tests()
    d=load(training_root,validation_root)
    receipt=json.loads(Path(receipt_path).read_text())
    if receipt.get('architecture')!='NO' or receipt.get('validation_year')!=2025 or len(receipt.get('cells',[]))!=30:
        raise ValueError('NO_2025_INDEPENDENT_RECEIPT_SCOPE')
    cell=next(x for x in receipt['cells'] if x['book']=='NO_full' and x['tier']=='base' and x['order']=='carried_before_fill')
    if not cell['passed']:raise ValueError('NO_2025_NO_COMPLETE_ORIGINAL_LEDGER')
    lo=np.full((TOTAL,4),np.nan);hi=np.full((TOTAL,4),np.nan)
    lo[TRAIN_HOURS:]=d['lo'];hi[TRAIN_HOURS:]=d['hi']
    with open(ledger_path) as f:
        rows=[json.loads(line) for line in f]
    if len(rows)!=HOURS_2025:raise ValueError('NO_2025_INDEPENDENT_LEDGER_LENGTH')
    out=replay(d,rows,lo,hi,.0004,.0002,'carried_before_fill',
        start=TRAIN_HOURS,end=TOTAL,initial_equity=10000.)
    for k in ('final_equity','turnover','fees','slippage','funding'):
        if not math.isclose(out[k],cell[k],rel_tol=1e-9,abs_tol=1e-5):
            raise ValueError('NO_2025_INDEPENDENT_'+k.upper()+'_MISMATCH')
    closes=np.array([float(x['equity_close']) for x in rows])
    daily=closes[23::24];dr=np.diff(np.r_[10000.,daily])/np.r_[10000.,daily[:-1]]
    if len(dr)!=365 or int((dr>0).sum())!=cell['positive_days'] or cell['daily_count']!=365:
        raise ValueError('NO_2025_INDEPENDENT_UTC_DAILY_BOUNDARY')
    out.update({'decision':'PASS_NO_2025_INDEPENDENT_ALL_HOUR_SETTLEMENT_NOT_FINAL_VALIDATION',
        'original_physical_decision':receipt['decision'],
        'daily_utc_count':365,'positive_days':int((dr>0).sum()),
        '2025_validation_only':True,'future_2026_holdout_accessed':False,
        'live_authorized':False,'source_signals_independently_reconstructed':False})
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('training-root','validation-root','ledger-jsonl','receipt','output'):
        p.add_argument('--'+name,required=True)
    a=p.parse_args()
    out=run(a.training_root,a.validation_root,a.ledger_jsonl,a.receipt)
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
