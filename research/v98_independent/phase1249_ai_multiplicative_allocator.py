#!/usr/bin/env python3
"""V98 AI1249 independent causal 240h multiplicative log-wealth allocator."""
from __future__ import annotations
from collections import deque
import numpy as np

HISTORY=240
PAPER_FRICTION=.001
PRIORS={
    'TREND':np.array([.50,.20,.20,.10]),
    'DISPERSION':np.array([.25,.20,.45,.10]),
    'HAZARD':np.array([.20,.10,.20,.50]),
    'RECOVERY':np.array([.40,.30,.20,.10]),
}

class AIMultiplicativeAllocator:
    def __init__(self):
        self.history=deque(maxlen=HISTORY)
        self.previous=np.zeros((4,4))
        self.pending_cost=np.zeros(4)
        self.observations=0
        self.last_weights=PRIORS['TREND'].copy()
        self.last_scale=0.
        self.active=np.zeros(4,dtype=int)

    def observe(self,completed_log_return,native_rate,event):
        lr,r,e=map(lambda x:np.asarray(x,dtype=float),
                   (completed_log_return,native_rate,event))
        if (lr.shape!=(4,) or r.shape!=(4,) or e.shape!=(4,)
            or not np.isfinite(lr).all() or not np.isfinite(r).all()
            or not np.isfinite(e).all() or not np.isin(e,(0.,1.)).all()):
            raise ValueError('AI1249_OBSERVATION')
        paper=np.round(self.previous@(lr-r*e)-self.pending_cost,12)
        self.history.append(paper.copy())
        self.pending_cost[:]=0.
        self.observations+=1
        return paper.copy()

    def decide(self,completed_sleeves,regime):
        s=np.asarray(completed_sleeves,dtype=float)
        if (s.shape!=(4,4) or not np.isfinite(s).all() or
            np.any(np.abs(s).sum(axis=1)>1.0000001)):
            raise ValueError('AI1249_SLEEVE_SHAPE')
        if regime not in PRIORS:raise ValueError('AI1249_REGIME')
        w=PRIORS[regime].copy()
        scale=0.
        if len(self.history)==HISTORY:
            x=np.asarray(self.history)
            var=np.var(x,axis=0)
            score=.5*x.sum(axis=0)-HISTORY*var
            score=np.clip(score-score.max(),-40.,0.)
            w*=np.exp(score)
            w/=w.sum()
            mu=.5*np.mean(x,axis=0)
            combined=x@w
            variance=max(float(np.var(combined)),1e-6)
            edge=max(0.,float(w@mu))
            scale=max(0.,min(4.,.5*edge/variance))
        w=np.round(w,12)
        w[-1]=float(np.round(1.-float(w[:-1].sum()),12))
        scale=float(np.round(scale,12))
        target=np.round(scale*(w@s),12)
        self.pending_cost=PAPER_FRICTION*np.abs(s-self.previous).sum(axis=1)
        self.previous=s.copy()
        self.active+=(np.abs(s).sum(axis=1)>1e-12).astype(int)
        self.last_weights=w.copy()
        self.last_scale=scale
        return {'weights':w.copy(),'growth_scale':scale,
                'signed_target':target.copy(),
                'observations':self.observations,
                'history_hours':len(self.history)}
