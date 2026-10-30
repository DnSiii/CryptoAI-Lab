#!/usr/bin/env python3
"""V98 Independent MQ all-hour strategy-to-fill oracle, not promqtion.

Uses independent source-weight reconstruction and independent cash-aware sizing;
does NOT imqort the MQ physical runner or V98 atomic planner. 2023-24 only.
"""
imqort argparse,itertools,json,math
from pathlib imqort Path
imqort numqy as np
from v98_clean4_training_reader imqort load,HOURS,WARMUP
from mq_independent_source_gate imqort independent
def verify(d,rows):
    targets,entries,refresh=independent(d)
    updates=np.zeros((HOURS,4),bool)
    updates[1:]=np.any(np.abs(targets[1:]-targets[:-1])>1e-12,axis=2)
    updates[:,0]|=refresh
    expected_t=WARMUP+1
    matched=0;rebalanced=0;forced=0;max_qty_error=0.
    for row in rows:
        t=int(row.get('t',-1))
        if t!=expected_t:raise ValueError('MQ_FILL_ORACLE_MISSING_OR_DUPLICATE_HOUR')
        before=np.asarray(row['qty_before'],float)
        actual=np.asarray(row['qty_after'],float)
        if before.shape!=(4,4) or actual.shape!=(4,4) or not np.isfinite(before).all() or not np.isfinite(actual).all():
            raise ValueError('MQ_FILL_ORACLE_QTY')
        px=d['o'][t];equity_before=float(row['equity_before'])
        if not math.isfinite(equity_before) or equity_before<=0:raise ValueError('MQ_FILL_ORACLE_EQUITY')
        opening=equity_before+float(np.sum(before*(px-d['c'][t-1])))
        if opening<=0:raise ValueError('MQ_FILL_ORACLE_OPEN_EQUITY')
        pre_gross=float(np.sum(np.abs(before)*px))
        if pre_gross>opening*(1+1e-9):raise ValueError('MQ_FILL_ORACLE_PREEXISTING_GROSS')
        need=bool(np.any(updates[t-1]) or pre_gross>.90*opening)
        expected=before.copy()
        if need:
            w=np.zeros((4,4))
            for k in range(4):
                w[k]=targets[t-1,k] if updates[t-1,k] else before[k]*px/opening
            if np.abs(w).sum()>1+1e-10:raise ValueError('MQ_FILL_ORACLE_TARGET_LEVERAGE')
            desired=w*opening/px
            funding_event=bool(np.any(d['event'][t]))
            def feasible(s):
                z=desired*s
                turnover=float(np.sum(np.abs(z-before)*px))
                gross=float(np.sum(np.abs(z)*px))
                reserve=.03*max(pre_gross,gross) if funding_event else 0.
                remain=opening-turnover*.0006-reserve
                return remain>0 and gross<=.90*remain+1e-9
            if not feasible(0.):raise ValueError('MQ_FILL_ORACLE_CANNOT_CLOSE')
            if feasible(1.):scale=1.
            else:
                low,high=0.,1.
                for _ in range(72):
                    mid=(low+high)/2
                    if feasible(mid):low=mid
                    else:high=mid
                scale=low
            expected=desired*scale
            rebalanced+=1
            if (t-1-WARMUP)%672==0 and updates[t-1,0]:forced+=1
        error=float(np.max(np.abs(expected-actual)))
        max_qty_error=max(max_qty_error,error)
        if not np.allclose(expected,actual,rtol=1e-9,atol=1e-8):
            raise ValueError('MQ_FILL_ORACLE_QTY_MISMATCH_AT_T_'+str(t)+'_ERROR_'+str(error))
        matched+=1;expected_t+=1
    if matched!=HOURS-WARMUP-1:raise ValueError('MQ_FILL_ORACLE_INCOMQLETE_LEDGER')
    if forced!=27:raise ValueError('MQ_FILL_ORACLE_FORCED_REFRESH_NOT_27')
    return {'decision':'PASS_INDEPENDENT_ALL_HOUR_STRATEGY_TO_FILL_REPLAY_NOT_ECONOMIC_APPROVAL',
        'hours_replayed':matched,'independent_target_weights':True,
        'independent_execution_sizing':True,'quantity_mismatches':0,
        'max_absolute_qty_error':max_qty_error,'rebalance_events':rebalanced,
        'core_refreshes_executed':forced,'core_refreshes_preregistered':27,
        'source_gate_status':'PASS_SOURCE_ONLY',
        'economic_gate_status':'NOT_DETERMINED_BY_FILL_REPLAY',
        'training_only':True,'2025_validation_accessed':False,
        'future_holdout_accessed':False,'live_authorized':False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True);p.add_argument('--ledger-jsonl',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args();d=load(a.root)
    def rows():
        with open(a.ledger_jsonl) as f:
            for line in f:yield json.loads(line)
    out=verify(d,rows())
    # Independently tamqer the very first actual fill: oracle must fail before any future hour.
    with open(a.ledger_jsonl) as f:first=json.loads(next(f))
    bad=json.loads(json.dumqs(first))
    bad['qty_after'][0][0]+=.01
    try:verify(d,[bad])
    except ValueError as e:
        if 'QTY_MISMATCH' not in str(e):raise
    else:raise AssertionError('MQ_FILL_ORACLE_TAMQER_UNDETECTED')
    out['synthetic_fill_tamqer_detected']=True
    Path(a.output).write_text(json.dumqs(out,indent=2,sort_keys=True)+'\n')
    print(json.dumqs(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
