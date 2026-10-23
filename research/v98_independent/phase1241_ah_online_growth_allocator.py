#!/usr/bin/env python3
"""V98 Independent AH1241 causal online net-log-growth sleeve allocator."""
from __future__ import annotations
from collections import deque
import numpy as np

SLEEVES=('growth','opportunity','relative_value','stress')
PRIORS={
    'TREND':np.array([.55,.20,.15,.10]),
    'DISPERSION':np.array([.30,.20,.40,.10]),
    'HAZARD':np.array([.25,.10,.15,.50]),
}
HISTORY=168
PAPER_FRICTION=.001

def _sleeves(x):
    a=np.asarray(x,dtype=float)
    if a.shape!=(4,4) or not np.isfinite(a).all():
        raise ValueError('AH1241_SLEEVES')
    if np.any(np.abs(a).sum(axis=1)>1.0000001):
        raise ValueError('AH1241_UNNORMALIZED_SOURCE')
    return a

class AHOnlineGrowthAllocator:
    def __init__(self):
        self.paper=deque(maxlen=HISTORY)
        self.signals=np.zeros((4,4))
        self.pending_cost=np.zeros(4)
        self.last_weights=PRIORS['TREND'].copy()
        self.last_scale=0.
        self.observations=0
        self.decisions=0
        self.active=np.zeros(4,dtype=int)

    def observe(self,completed_log_return,native_rate,funding_event):
        lr,r,e=map(lambda x:np.asarray(x,dtype=float),
                   (completed_log_return,native_rate,funding_event))
        if (lr.shape!=(4,) or r.shape!=(4,) or e.shape!=(4,)
            or not np.isfinite(lr).all() or not np.isfinite(r).all()
            or not np.isfinite(e).all() or not np.isin(e,(0.,1.)).all()):
            raise ValueError('AH1241_OBSERVATION')
        # All signed returns are from signals decided at the PREVIOUS close.
        paper=self.signals@(lr-r*e)-self.pending_cost
        self.paper.append(paper.copy())
        self.pending_cost[:]=0.
        self.observations+=1
        return paper.copy()

    def decide(self,completed_close_sleeves,regime):
        s=_sleeves(completed_close_sleeves)
        if regime not in PRIORS:
            raise ValueError('AH1241_REGIME')
        w=PRIORS[regime].copy()
        scale=0.
        if len(self.paper)==HISTORY:
            x=np.asarray(self.paper)
            mu=.5*np.mean(x,axis=0)
            cov=np.cov(x,rowvar=False,bias=True)
            cov=.5*cov+.5*np.diag(np.diag(cov))
            cov+=np.eye(4)*1e-6
            for _ in range(32):
                grad=mu-cov@w
                z=np.clip(100.*grad,-20.,20.)
                w*=np.exp(z)
                w/=w.sum()
            combined=x@w
            variance=max(float(np.var(combined)),1e-6)
            positive_mu=max(0.,float(w@mu))
            scale=max(0.,min(3.,.5*positive_mu/variance))
        # The proposed scalar is only an intent. The separate risk governor
        # must approve collateral, all 81 corners, exit depth and funding.
        target=scale*(w@s)
        self.pending_cost=PAPER_FRICTION*np.abs(s-self.signals).sum(axis=1)
        self.signals=s.copy()
        self.last_weights=w.copy()
        self.last_scale=scale
        self.active+=(np.abs(s).sum(axis=1)>1e-12).astype(int)
        self.decisions+=1
        return {'sleeve_weights':w.copy(),'growth_scale':float(scale),
                'signed_target':target.copy(),
                'observations':self.observations,
                'paper_history':len(self.paper)}
