#!/usr/bin/env python3
"""Independent NQ five-book shadow settlement and causal score oracle.
Does not import NQ shadow implementation, V98 planner or physical runner for
independent reconstruction. Uses the original only for final comparison.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from v98_clean4_training_reader import load
from v98_mark_envelope_settlement import read_envelope
from nq_independent_source_gate import replay
from nq_sources import BOOKS,HOURS,WARMUP
from nq_online_shadow_marginal import build as original_shadow

def independently_reconstruct(d,lo,hi):
    raw,activity,decisions=replay(d)
    books=tuple(BOOKS)
    n=len(d['o'])
    q=np.zeros((5,4,4));nav=np.full(5,10000.)
    curves=np.full((n,5),np.nan);curves[WARMUP]=nav
    scores=np.full((n,3),np.nan)
    weights=np.zeros_like(raw)
    multipliers=np.full(3,.5)
    def weight(t):
        w=raw[t].copy();w[1:]*=multipliers[:,None]
        room=.84-float(np.abs(w[0]).sum())
        opt=float(np.abs(w[1:]).sum())
        if opt>room and opt>0:w[1:]*=room/opt
        return w
    current=weight(WARMUP);weights[WARMUP]=current
    fills=0
    for t in range(WARMUP+1,n):
        px=d['o'][t];ev=bool(d['event'][t].any())
        for b,book in enumerate(books):
            before=q[b].copy()
            oldnet=before.sum(axis=0)
            nav[b]+=float(np.dot(oldnet,px-d['c'][t-1]))
            if nav[b]<=0:raise ValueError('NQ_INDEPENDENT_SHADOW_OPEN_INSOLVENT')
            gross=float(np.sum(np.abs(before)*px))
            guard=bool(gross>.84*nav[b] or (ev and gross>.82*nav[b]))
            enabled=np.zeros(4,bool);enabled[list(BOOKS[book])]=True
            updated=enabled & decisions[t-1]
            new=before.copy()
            if updated.any() or guard:
                source=raw[t-1].copy();source[~enabled]=0.
                mix=before*px/nav[b]
                mix[updated]=source[updated]
                if np.abs(source).sum()>.84+1e-10:
                    raise ValueError('NQ_INDEPENDENT_SHADOW_RAW_GROSS')
                cap=.82 if guard else .84
                w=mix.copy()
                core=float(np.abs(w[0]).sum())
                if core>cap:w[0]*=cap/core
                room=max(0.,cap-float(np.abs(w[0]).sum()))
                opt=float(np.abs(w[1:]).sum())
                if opt>room and opt>0:w[1:]*=room/opt
                desired=w*nav[b]/px
                def assessment(scale):
                    candidate=desired*scale
                    newnet=candidate.sum(axis=0)
                    turn=float(np.sum(np.abs(newnet-oldnet)*px))
                    reserve=.03*max(float(np.sum(np.abs(oldnet)*px)),
                                    float(np.sum(np.abs(newnet)*px))) if ev else 0.
                    available=nav[b]-turn*.0006-reserve
                    ok=available>0 and max(float(np.sum(np.abs(candidate)*px)),
                        float(np.sum(np.abs(newnet)*px)))<=.90*available+1e-8
                    ok=ok and float(np.sum(np.abs(candidate)*px))<=.84*nav[b]+1e-8
                    return ok,turn,candidate,reserve
                if not assessment(0.)[0]:
                    raise ValueError('NQ_INDEPENDENT_SHADOW_CANNOT_CLOSE')
                if assessment(1.)[0]:scale=1.
                else:
                    low,high=0.,1.
                    for _ in range(72):
                        mid=(low+high)/2.
                        if assessment(mid)[0]:low=mid
                        else:high=mid
                    scale=low
                ok,turn,new,reserve=assessment(scale)
                if not ok:raise ValueError('NQ_INDEPENDENT_SHADOW_NO_SCALE')
                nav[b]-=turn*.0006
                fills+=1
            else:reserve=0.
            newnet=new.sum(axis=0)
            if ev:
                obligation=oldnet*d['rate'][t]*d['event'][t]
                cash=-float(np.dot(obligation,np.where(obligation>=0,hi[t],lo[t])))
                if cash < -reserve-1e-7 and (updated.any() or guard):
                    raise ValueError('NQ_INDEPENDENT_SHADOW_FUNDING_RESERVE')
                nav[b]+=cash
            q[b]=new
            nav[b]+=float(np.dot(newnet,d['c'][t]-px))
            if nav[b]<=0 or not np.isfinite(nav[b]):
                raise ValueError('NQ_INDEPENDENT_SHADOW_CLOSE_INSOLVENT')
            curves[t,b]=nav[b]
        if (t-WARMUP)%168==0:
            if t-1344>=WARMUP:
                for j in range(3):
                    value=math.log(curves[t,0]/curves[t-1344,0])-math.log(
                        curves[t,j+2]/curves[t-1344,j+2])
                    scores[t,j]=value
                    multipliers[j]=1. if value>0 else .25
            else:multipliers[:]=.5
            current=weight(t)
        weights[t]=current
    return {'equity':curves,'scores':scores,'weights':weights,'fills':fills}

def verify(d,lo,hi):
    raw,activity,decisions=replay(d)
    updates=np.tile(decisions[:,None],(1,4))
    original=original_shadow(d,raw,updates,lo,hi)
    independent=independently_reconstruct(d,lo,hi)
    for field,orig in (('equity',original['shadow_equity']),
                       ('scores',original['scores']),('weights',original['weights'])):
        new=independent[field]
        if not np.allclose(orig,new,rtol=1e-8,atol=1e-7,equal_nan=True):
            idx=np.argwhere(~np.isclose(orig,new,rtol=1e-8,atol=1e-7,equal_nan=True))
            raise ValueError('NQ_INDEPENDENT_SHADOW_'+field.upper()+'_MISMATCH_'+str(idx[:5]))
    return {'decision':'PASS_INDEPENDENT_FIVE_BOOK_SHADOW_ACCOUNTING_AND_LAGGED_SCORES',
        'hours_reconciled':HOURS-WARMUP-1,'books_reconciled':5,
        'score_decisions':int(np.isfinite(independent['scores']).any(axis=1).sum()),
        'reference_fills':independent['fills'],
        'max_equity_abs_mismatch':float(np.nanmax(np.abs(
            original['shadow_equity']-independent['equity']))),
        'future_funding_used_for_decision':False,'training_only':True,
        '2025_or_future_holdout_accessed':False,'not_final_validation':True}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True);p.add_argument('--envelope-csv',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args();d=load(a.root);lo,hi,_=read_envelope(a.envelope_csv,d)
    result=verify(d,lo,hi)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
