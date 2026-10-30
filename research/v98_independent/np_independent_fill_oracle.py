#!/usr/bin/env python3
"""V98 Independent NP all-hour strategy-to-fill oracle, not promotion.

Uses independent source-weight reconstruction and independent cash-aware sizing;
does NOT import the NP physical runner or V98 atomic planner. 2023-24 only.
"""
import argparse,itertools,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load,HOURS,WARMUP
from np_independent_source_gate import replay
def verify(d,rows):
    targets,entries,refresh=replay(d)
    updates=np.zeros((HOURS,4),bool)
    updates[1:]=np.any(np.abs(targets[1:]-targets[:-1])>1e-12,axis=2)
    updates[:,0]|=refresh
    expected_t=WARMUP+1
    matched=0;rebalanced=0;forced=0;max_qty_error=0.
    for row in rows:
        t=int(row.get('t',-1))
        if t!=expected_t:raise ValueError('NP_FILL_ORACLE_MISSING_OR_DUPLICATE_HOUR')
        before=np.asarray(row['qty_before'],float)
        actual=np.asarray(row['qty_after'],float)
        if before.shape!=(4,4) or actual.shape!=(4,4) or not np.isfinite(before).all() or not np.isfinite(actual).all():
            raise ValueError('NP_FILL_ORACLE_QTY')
        px=d['o'][t];equity_before=float(row['equity_before'])
        if not math.isfinite(equity_before) or equity_before<=0:raise ValueError('NP_FILL_ORACLE_EQUITY')
        opening=equity_before+float(np.sum(before*(px-d['c'][t-1])))
        if opening<=0:raise ValueError('NP_FILL_ORACLE_OPEN_EQUITY')
        pre_gross=float(np.sum(np.abs(before)*px))
        if max(pre_gross,float(np.sum(np.abs(before.sum(axis=0))*px)))>opening*(1+1e-9):
            raise ValueError('NP_FILL_ORACLE_PREEXISTING_GROSS')
        guard=bool(pre_gross>.84*opening or
                   (bool(np.any(d['event'][t])) and pre_gross>.82*opening))
        need=bool(np.any(updates[t-1]) or guard)
        expected=before.copy()
        if need:
            # Independent NP projection reconstruction (NP project import).
            raw=before*px/opening
            raw[updates[t-1]]=targets[t-1][updates[t-1]]
            if np.abs(targets[t-1]).sum()>.84+1e-10:
                raise ValueError('NP_FILL_ORACLE_SOURCE_CAP')
            cap=.82 if guard else .84
            w=raw.copy()
            core=float(np.abs(w[0]).sum())
            if core>cap:w[0]*=cap/core
            remaining=max(0.,cap-float(np.abs(w[0]).sum()))
            optional=float(np.abs(w[1:]).sum())
            if optional>remaining and optional>0:w[1:]*=remaining/optional
            if np.abs(w).sum()>cap+1e-10:raise ValueError('NP_FILL_ORACLE_VIRTUAL_CAP')
            if np.any(w*raw< -1e-12):raise ValueError('NP_FILL_ORACLE_SIGN_FLIP')
            desired=w*opening/px
            old_net=before.sum(axis=0)
            pre_net=float(np.sum(np.abs(old_net)*px))
            funding_event=bool(np.any(d['event'][t]))
            def feasible(s):
                z=desired*s
                new_net=z.sum(axis=0)
                turnover=float(np.sum(np.abs(new_net-old_net)*px))
                virt_gross=float(np.sum(np.abs(z)*px))
                net_gross=float(np.sum(np.abs(new_net)*px))
                reserve=.03*max(pre_net,net_gross) if funding_event else 0.
                remain=opening-turnover*.0006-reserve
                return (remain>0 and virt_gross<=.90*remain+1e-8
                        and net_gross<=.90*remain+1e-8
                        and virt_gross<=.84*opening+1e-8)
            if not feasible(0.):raise ValueError('NP_FILL_ORACLE_CANNOT_CLOSE')
            if feasible(1.):scale=1.
            else:
                low,high=0.,1.
                for _ in range(72):
                    mid=(low+high)/2
                    if feasible(mid):low=mid
                    else:high=mid
                scale=low
            expected=desired*scale
            traded=np.abs(expected.sum(axis=0)-before.sum(axis=0))>1e-12
            if np.any(traded & (d['q'][t]<=0)):
                raise ValueError('NP_FILL_ORACLE_ZERO_VOLUME_EXECUTION')
            rebalanced+=1
            if (t-1-WARMUP)%336==0 and updates[t-1,0]:forced+=1
        error=float(np.max(np.abs(expected-actual)))
        max_qty_error=max(max_qty_error,error)
        if not np.allclose(expected,actual,rtol=1e-9,atol=1e-8):
            raise ValueError('NP_FILL_ORACLE_QTY_MISMATCH_AT_T_'+str(t)+'_ERROR_'+str(error))
        matched+=1;expected_t+=1
    if matched!=HOURS-WARMUP-1:raise ValueError('NP_FILL_ORACLE_INCOMPLETE_LEDGER')
    if forced!=53:raise ValueError('NP_FILL_ORACLE_FORCED_REFRESH_NOT_27')
    return {'decision':'PASS_INDEPENDENT_ALL_HOUR_STRATEGY_TO_FILL_REPLAY_NOT_ECONOMIC_APPROVAL',
        'hours_replayed':matched,'independent_target_weights':True,
        'independent_execution_sizing':True,'one_way_netting':True,'quantity_mismatches':0,
        'max_absolute_qty_error':max_qty_error,'rebalance_events':rebalanced,
        'core_refreshes_executed':forced,'core_refreshes_preregistered':53,
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
    # Independently tamper the very first actual fill: oracle must fail before any future hour.
    with open(a.ledger_jsonl) as f:first=json.loads(next(f))
    bad=json.loads(json.dumps(first))
    bad['qty_after'][0][0]+=.01
    try:verify(d,[bad])
    except ValueError as e:
        if 'QTY_MISMATCH' not in str(e):raise
    else:raise AssertionError('NP_FILL_ORACLE_TAMPER_UNEETECTED')
    out['synthetic_fill_tamper_detected']=True
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
