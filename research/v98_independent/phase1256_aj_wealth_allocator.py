#!/usr/bin/env python3
"""V98 Independent AJ1256: uncapped half-Kelly log-wealth sleeve allocator."""
from __future__ import annotations
from collections import deque
import numpy as np

HISTORY=168
PAPER_FRICTION=.0015
PRIORS={
    'TREND':np.array([.45,.20,.20,.15]),
    'RANGE':np.array([.25,.20,.40,.15]),
    'CRISIS':np.array([.15,.10,.20,.55]),
    'REBOUND':np.array([.35,.35,.20,.10]),
}

class AJWealthAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.previous=np.zeros((4,4))
        self.pending_cost=np.zeros(4)
        self.observations=0
        self.last_weights=PRIORS['RANGE'].copy()
        self.last_scale=0.
        self.active=np.zeros(4,dtype=int)

    def observe(self,completed_log_return,native_rate,event):
        lr=np.asarray(completed_log_return,dtype=float)
        r=np.asarray(native_rate,dtype=float)
        e=np.asarray(event,dtype=float)
        if (lr.shape!=(4,) or r.shape!=(4,) or e.shape!=(4,) or
            not np.isfinite(lr).all() or not np.isfinite(r).all() or
            not np.isfinite(e).all() or not np.isin(e,(0.,1.)).all()):
            raise ValueError('AJ1256_OBSERVATION')
        paper=self.previous@(lr-r*e)-self.pending_cost
        if not np.isfinite(paper).all():
            raise ValueError('AJ1256_PAPER_NONFINITE')
        self.history.append(paper.copy())
        self.pending_cost[:]=0.
        self.observations+=1
        return paper.copy()

    def decide(self,completed_sleeves,regime):
        s=np.asarray(completed_sleeves,dtype=float)
        if (s.shape!=(4,4) or not np.isfinite(s).all() or
            np.any(np.abs(s).sum(axis=1)>1.0000001)):
            raise ValueError('AJ1256_SOURCE_SHAPE')
        if regime not in PRIORS:
            raise ValueError('AJ1256_REGIME')
        w=PRIORS[regime].copy()
        scale=0.
        if len(self.history)==HISTORY:
            x=np.asarray(self.history)
            cs=np.cumsum(x,axis=0)
            peaks=np.maximum.accumulate(np.vstack((np.zeros((1,4)),cs)),
                                         axis=0)[1:]
            dd=np.max(peaks-cs,axis=0)
            score=2*(cs[-1]-2*dd)
            score=score-float(np.max(score))
            w*=np.exp(np.clip(score,-700.,0.))
            w/=float(np.sum(w))
            combined=x@w
            edge=max(0.,.5*float(np.mean(combined)))
            variance=max(float(np.var(combined)),1e-6)
            scale=edge/variance  # no artificial upside cap; governor is binding
        w=np.round(w,12)
        w[-1]=float(np.round(1.-float(w[:-1].sum()),12))
        scale=float(np.round(scale,12))
        target=scale*(w@s)
        if not np.isfinite(target).all():
            raise ValueError('AJ1256_TARGET_NONFINITE')
        self.pending_cost=PAPER_FRICTION*np.abs(s-self.previous).sum(axis=1)
        self.previous=s.copy()
        self.active+=(np.abs(s).sum(axis=1)>1e-12).astype(int)
        self.last_weights=w.copy()
        self.last_scale=scale
        return {'weights':w.copy(),'growth_scale':scale,
                'signed_target':target.copy(),
                'history_hours':len(self.history),
                'observations':self.observations}
