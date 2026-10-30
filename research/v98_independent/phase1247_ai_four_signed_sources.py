#!/usr/bin/env python3
"""V98 AI1247 independent causal four-sleeve signed source and regime router."""
from __future__ import annotations
import numpy as np

ASSETS=('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT')
STATES=('TREND','DISPERSION','HAZARD','RECOVERY')

def _close(x):
    c=np.asarray(x,dtype=float)
    if c.ndim!=2 or c.shape[1]!=4 or not np.isfinite(c).all() or np.any(c<=0):
        raise ValueError('AI1247_CLOSE')
    return c

def _native(c,rate,event):
    r,e=map(lambda x:np.asarray(x,dtype=float),(rate,event))
    if (r.shape!=c.shape or e.shape!=c.shape or
        not np.isfinite(r).all() or not np.isfinite(e).all() or
        not np.isin(e,(0.,1.)).all()):
        raise ValueError('AI1247_NATIVE')
    return r,e

def growth_core(close,rate,event):
    c=_close(close);r,e=_native(c,rate,event)
    n=len(c);out=np.zeros((n,4))
    lr=np.diff(np.log(c),axis=0)
    for t in range(240,n):
        raw=lr[t-240:t].sum(axis=0)-(r[t-239:t+1]*e[t-239:t+1]).sum(axis=0)
        confirm=lr[t-48:t].sum(axis=0)
        scale=max(float(np.median(np.abs(raw))),1e-4)
        s=np.where(raw*confirm>0,np.clip(raw/scale,-3.,3.),0.)
        gross=float(np.abs(s).sum())
        if gross>1e-12:out[t]=np.round(s/gross,12)
    return out

def opportunity(close,high,low):
    c=_close(close)
    h,l=map(lambda x:np.asarray(x,dtype=float),(high,low))
    if (h.shape!=c.shape or l.shape!=c.shape or
        not np.isfinite(h).all() or not np.isfinite(l).all() or
        np.any(l<=0) or np.any(l>c) or np.any(h<c)):
        raise ValueError('AI1247_OHLC')
    n=len(c);out=np.zeros((n,4))
    lr=np.diff(np.log(c),axis=0)
    sign=np.zeros(4);ttl=np.zeros(4,dtype=int)
    for t in range(96,n):
        impulse=(np.sqrt(np.mean(lr[t-8:t]**2,axis=0))>
            1.5*np.maximum(np.sqrt(np.mean(lr[t-72:t]**2,axis=0)),1e-8))
        up=c[t]>np.max(h[t-36:t],axis=0)
        down=c[t]<np.min(l[t-36:t],axis=0)
        events=np.where(impulse&up,1.,np.where(impulse&down,-1.,0.))
        new=events!=0
        sign[new]=events[new]
        ttl[new]=6
        active=np.where(ttl>0,sign,0.)
        gross=float(np.abs(active).sum())
        if gross>0:out[t]=np.round(active/gross,12)
        ttl=np.maximum(0,ttl-1)
    return out

def relative_value(close):
    c=_close(close);n=len(c)
    out=np.zeros((n,4));betas=np.zeros((n,4))
    logc=np.log(c);lr=np.diff(logc,axis=0)
    for t in range(240,n):
        x=lr[t-240:t];market=x[:,0]
        center=market-market.mean()
        var=float(np.mean(center**2))
        if var<1e-10:continue
        y=x-x.mean(axis=0)
        beta=np.clip(np.mean(y*center[:,None],axis=0)/var,-3.,3.)
        beta[0]=1.
        betas[t]=beta
        residual=((logc[t]-logc[t-72])-
            beta*(logc[t,0]-logc[t-72,0]))
        resid=x-beta[None,:]*market[:,None]
        sigma=np.maximum(np.sqrt(72*np.mean(resid**2,axis=0)),1e-4)
        raw=-residual/sigma
        A=np.vstack((np.ones(4),beta))
        neutral=raw-A.T@(np.linalg.pinv(A@A.T,rcond=1e-12)@(A@raw))
        gross=float(np.abs(neutral).sum())
        if gross>1e-10:
            out[t]=np.round(neutral/gross,9)
            if abs(out[t].sum())>1e-8 or abs(out[t]@beta)>1e-8:
                raise ValueError('AI1247_RV_NEUTRALITY')
    return out,betas

def _semivariance_ratio(m):
    down=float(np.mean(np.minimum(m,0.)**2))
    up=float(np.mean(np.maximum(m,0.)**2))
    return down/max(up,1e-8)

def stress_factor(close):
    c=_close(close);n=len(c)
    lr=np.diff(np.log(c),axis=0)
    m=lr.mean(axis=1)
    out=np.zeros((n,4))
    active=False;benign=0
    for t in range(72,n):
        trigger=bool(_semivariance_ratio(m[t-72:t])>1.2 or
            float(m[t-48:t].sum())<-.05)
        if trigger:active=True;benign=0
        elif active:
            benign+=1
            if benign>=24:active=False;benign=0
        if active:out[t]=np.full(4,-.25)
    return out

def regime_router(close,rate,event):
    c=_close(close);r,e=_native(c,rate,event)
    n=len(c);lr=np.diff(np.log(c),axis=0)
    states=np.full(n,'TREND',dtype='<U10')
    breadth=np.zeros(n);dispersion=np.zeros(n)
    for t in range(96,n):
        x=lr[t-96:t]
        m=x.mean(axis=1)
        drift48=float(m[-48:].sum())
        d=float(np.std(x.sum(axis=0)))
        center=m-m.mean()
        sigma=max(float(np.sqrt(np.mean(center**2))),1e-4)
        skew=float(np.mean((center/sigma)**3))
        ratio=_semivariance_ratio(m)
        rates=(r[t-95:t+1]*e[t-95:t+1])
        nonzero=rates[rates!=0]
        breadth[t]=float(np.mean(nonzero>0)) if len(nonzero) else 0.
        dispersion[t]=d
        if drift48<-.06 and ratio>1.2:states[t]='HAZARD'
        elif drift48>.05 and skew>.5:states[t]='RECOVERY'
        elif d>.06:states[t]='DISPERSION'
    return {'state':states,'funding_breadth':breadth,'dispersion':dispersion}

def source_bundle(close,high,low,rate,event):
    c=_close(close)
    return (growth_core(c,rate,event),opportunity(c,high,low),
            relative_value(c)[0],stress_factor(c),
            regime_router(c,rate,event))
