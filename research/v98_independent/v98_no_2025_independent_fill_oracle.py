#!/usr/bin/env python3
"""V98 NO 2025 independent source-to-net-fill oracle.
Independent signal reconstruction and sizing, no 2025 physical-runner import.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_no_2025_validation_reader import load,TRAIN_HOURS,TOTAL,HOURS_2025
WARMUP=744

def source_replay(d):
    # Independent reconstruction; does not import the physical validator.
    close=d['c'];target=np.zeros((TOTAL,4,4));forced=np.zeros(TOTAL,bool)
    held=np.zeros((4,4));multipliers=np.ones(3)
    for t in range(WARMUP,TOTAL):
        k=t-WARMUP
        if k%336==0:
            if np.any(d['q'][t]<=0):raise ValueError('NO_2025_FILL_CORE_VOLUME')
            held[0]=[.16,.16,.16,.16];forced[t]=True
        if k%168==0:
            if np.any(d['q'][t]<=0):raise ValueError('NO_2025_FILL_WEEK_VOLUME')
            r24=np.log(close[t]/close[t-24])
            r168=np.log(close[t]/close[t-168])
            held[1:]=0.
            leader=sorted((1,2,3),key=lambda j:(-r168[j],j))[0]
            if r168[leader]>0:held[1,leader]=.12
            if t%8 or not np.all(d['event'][t-160:t+1:8]):
                raise ValueError('NO_2025_FILL_UNSETTLED_FUNDING')
            carry=np.array([sum(float(d['rate'][x,j]) for x in range(t-160,t+1,8))/21
                            for j in range(4)])
            ranking=sorted(range(4),key=lambda j:(carry[j],j))
            held[2,ranking[0]]=.04
            held[2,ranking[-1]]=-.04
            held[3,0]=.10 if r24[0]>0 and r168[0]>0 else 0.
            multipliers=np.array([1.,1.,1.] if sum(x>0 for x in r168)>=2
                                 else [.5,1.,.5])
        w=held.copy()
        for slot in (1,2,3):w[slot]*=multipliers[slot-1]
        room=.84-float(np.abs(w[0]).sum())
        optional=float(np.abs(w[1:]).sum())
        if room<0:raise ValueError('NO_2025_FILL_CORE_CAP')
        if optional>room and optional>0:w[1:]*=room/optional
        target[t]=w
    updates=np.zeros((TOTAL,4),bool)
    updates[1:]=np.any(np.abs(target[1:]-target[:-1])>1e-12,axis=2)
    updates[:,0]|=forced
    return target,updates,forced

def verify(d,rows):
    targets,updates,forced=source_replay(d)
    before_expected=np.zeros((4,4))
    expected_t=TRAIN_HOURS
    matched=rebalance=core_refreshes=0;max_error=0.
    for row in rows:
        t=int(row.get('t',-1))
        if t!=expected_t:raise ValueError('NO_2025_FILL_MISSING_OR_DUPLICATE_HOUR')
        before=np.asarray(row['qty_before'],float)
        actual=np.asarray(row['qty_after'],float)
        if before.shape!=(4,4) or actual.shape!=(4,4) or not np.isfinite(before).all() or not np.isfinite(actual).all():
            raise ValueError('NO_2025_FILL_QTY')
        if not np.allclose(before,before_expected,rtol=0,atol=1e-10):
            raise ValueError('NO_2025_FILL_CARRY_QTY')
        px=d['o'][t];equity_before=float(row['equity_before'])
        if not math.isfinite(equity_before) or equity_before<=0:raise ValueError('NO_2025_FILL_EQUITY')
        opening=equity_before+float(np.sum(before*(px-d['c'][t-1])))
        if opening<=0:raise ValueError('NO_2025_FILL_OPEN_EQUITY')
        pre_gross=float(np.sum(np.abs(before)*px))
        if max(pre_gross,float(np.sum(np.abs(before.sum(axis=0))*px)))>opening*(1+1e-9):
            raise ValueError('NO_2025_FILL_PREEXISTING_GROSS')
        guard=bool(pre_gross>.84*opening or (bool(np.any(d['event'][t])) and pre_gross>.82*opening))
        need=bool(t==TRAIN_HOURS or np.any(updates[t-1]) or guard)
        expected=before.copy()
        if need:
            # Independent of shared project() and atomic plan_virtual() implementations.
            raw=before*px/opening
            mask=np.ones(4,bool) if t==TRAIN_HOURS else updates[t-1]
            raw[mask]=targets[t-1][mask]
            if np.abs(targets[t-1]).sum()>.84+1e-10:
                raise ValueError('NO_2025_FILL_SOURCE_CAP')
            cap=.82 if guard else .84
            w=raw.copy()
            core=float(np.abs(w[0]).sum())
            if core>cap:w[0]*=cap/core
            remaining=max(0.,cap-float(np.abs(w[0]).sum()))
            optional=float(np.abs(w[1:]).sum())
            if optional>remaining and optional>0:w[1:]*=remaining/optional
            if np.abs(w).sum()>cap+1e-10 or np.any(w*raw< -1e-12):
                raise ValueError('NO_2025_FILL_PROJECTION')
            desired=w*opening/px
            old_net=before.sum(axis=0)
            pre_net=float(np.sum(np.abs(old_net)*px))
            funding_event=bool(np.any(d['event'][t]))
            def feasible(scale):
                z=desired*scale
                new_net=z.sum(axis=0)
                turnover=float(np.sum(np.abs(new_net-old_net)*px))
                virt_gross=float(np.sum(np.abs(z)*px))
                net_gross=float(np.sum(np.abs(new_net)*px))
                reserve=.03*max(pre_net,net_gross) if funding_event else 0.
                remain=opening-turnover*.0006-reserve
                return (remain>0 and virt_gross<=.90*remain+1e-8
                        and net_gross<=.90*remain+1e-8
                        and virt_gross<=.84*opening+1e-8)
            if not feasible(0.):raise ValueError('NO_2025_FILL_CANNOT_CLOSE')
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
                raise ValueError('NO_2025_FILL_ZERO_VOLUME')
            rebalance+=1
            if t>TRAIN_HOURS and forced[t-1]:core_refreshes+=1
        error=float(np.max(np.abs(expected-actual)))
        max_error=max(max_error,error)
        if not np.allclose(expected,actual,rtol=1e-9,atol=1e-8):
            raise ValueError('NO_2025_FILL_QTY_MISMATCH_T_'+str(t)+'_ERROR_'+str(error))
        matched+=1;expected_t+=1;before_expected=actual
    if matched!=HOURS_2025:raise ValueError('NO_2025_FILL_INCOMPLETE')
    return {'decision':'PASS_NO_2025_INDEPENDENT_SOURCE_TO_NET_FILL_NOT_FINAL_VALIDATION',
        'hours_replayed':matched,'independent_source_reconstruction':True,
        'independent_execution_sizing':True,'quantity_mismatches':0,
        'max_absolute_qty_error':max_error,'rebalances':rebalance,
        'core_refreshes_during_2025':core_refreshes,
        '2025_validation_only':True,'2026_future_holdout_accessed':False,
        'live_authorized':False}

def main():
    p=argparse.ArgumentParser()
    for name in ('training-root','validation-root','ledger-jsonl','output'):
        p.add_argument('--'+name,required=True)
    a=p.parse_args();d=load(a.training_root,a.validation_root)
    with open(a.ledger_jsonl) as f:rows=[json.loads(line) for line in f]
    out=verify(d,rows)
    tampered=[dict(rows[0])]
    tampered[0]['qty_after']=[list(x) for x in rows[0]['qty_after']]
    tampered[0]['qty_after'][0][0]+=.01
    try:verify(d,tampered)
    except ValueError as exc:
        if 'QTY_MISMATCH' not in str(exc):raise
    else:raise AssertionError('NO_2025_FILL_TAMPER_UNDETECTED')
    out['synthetic_fill_tamper_detected']=True
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
