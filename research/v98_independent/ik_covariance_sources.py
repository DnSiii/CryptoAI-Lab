#!/usr/bin/env python3
"""IK independent covariance diversification / acceleration / residual-dislocation / beta-contagion source.
Frozen preregistration: ik_covariance_residual_prereg_20261027.md. TRAINING 2023-2024 only.
"""
from __future__ import annotations
import numpy as np

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
HOURS=18288
WARMUP=744
CLOCK=336
GROSS={"STRESS":.72,"RECOVERY":.94,"NORMAL":.90}
PRIOR={"STRESS":np.array([.62,.08,.10,.20]),
       "RECOVERY":np.array([.50,.20,.15,.15]),
       "NORMAL":np.array([.55,.20,.15,.10])}

def bundle(opening,high,low,close,rate,event,quote):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<=WARMUP or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("IK_INVALID_NATIVE_SOURCE")
    n=len(c)
    lc=np.log(c)
    signed=r*e
    prefix=np.vstack((np.zeros((1,4)),np.cumsum(signed,axis=0)))
    def net(t,w):
        return lc[t]-lc[t-w]-(prefix[t+1]-prefix[t-w+1])
    signals=np.zeros((n,4,4),dtype=float)
    updates=np.zeros((n,4),dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    budgets=np.zeros((n,4),dtype=float)
    validity=np.ones((n,4),dtype=bool)
    for t in range(WARMUP,n,CLOCK):
        x=np.diff(lc[t-336:t+1],axis=0)-signed[t-335:t+1]
        cov=np.cov(x,rowvar=False,ddof=1)
        diag=np.maximum(np.diag(cov),(0.0002)**2)
        cov=.75*cov+.25*np.diag(diag)
        cov[np.diag_indices(4)]=np.maximum(np.diag(cov),(0.0002)**2)
        vol=np.sqrt(np.diag(cov))
        corr=np.clip(cov/np.outer(vol,vol),-1.,1.)
        invvol=1./vol
        penalty=1./(1.+np.maximum(0.,np.sum(corr,axis=1))/4.)
        core=invvol*penalty
        signals[t,0]=core/core.sum()
        n24=net(t,24);n48=net(t,48);n72=net(t,72);n168=net(t,168)
        med72=float(np.median(n72))
        corr_off=(corr.sum()-np.trace(corr))/12.
        regime=("STRESS" if med72<0 and corr_off>.60 else
                "RECOVERY" if med72<0 and float(np.median(n24))>0 else "NORMAL")
        qwindow=q[t-335:t+1]
        range_window=np.log(h[t-335:t+1]/l[t-335:t+1])
        valid=bool(np.all(qwindow>0) and np.all(range_window>0)
                   and np.isfinite(range_window).all())
        validity[t,1:]=valid
        if valid:
            accel=n48-(48./168.)*n168
            eligible=(accel>0)&(n168>0)
            if np.any(eligible):
                scale=.001+np.sqrt(np.sum(x[-48:]**2,axis=0))
                score=np.where(eligible,accel/scale,-np.inf)
                signals[t,1,int(np.argmax(score))]=1.
            beta=np.clip(cov[1:,0]/cov[0,0],.25,2.)
            resid48=n48[1:]-beta*n48[0]
            resid336=x[:,1:]-x[:,[0]]*beta
            sigma=np.sqrt(np.sum(resid336**2,axis=0)*48./336.)
            z=resid48/np.maximum(sigma,.0001)
            if np.min(z)<-.25:
                j=1+int(np.argmin(z))
                b=float(beta[j-1])
                signals[t,2,j]=1./(1.+b)
                signals[t,2,0]=-b/(1.+b)
            market=x.mean(axis=1)
            marketvar=max(float(np.var(market,ddof=1)),(0.0002)**2)
            mcenter=market-market.mean()
            betam=np.mean((x-x.mean(axis=0))*mcenter[:,None],axis=0)/marketvar
            if med72<0:
                signals[t,3,int(np.argmin(betam))]=1.
            else:
                signals[t,3,int(np.argmax(betam))]=1.
        regimes[t]=regime
        budgets[t]=PRIOR[regime]
        updates[t]=True
        gross=np.abs(signals[t]).sum(axis=1)
        if (not np.isfinite(signals[t]).all() or
            not np.isfinite(budgets[t]).all() or
            not np.isclose(budgets[t].sum(),1.,atol=1e-12) or
            not np.all(np.isclose(gross,0.,atol=1e-12)|
                       np.isclose(gross,1.,atol=1e-12)) or
            not np.isclose(signals[t,0].sum(),1.,atol=1e-12)):
            raise ValueError("IK_SEVEN_SLOT_FINANCING_INVALID")
    return signals,updates,regimes,budgets,validity

def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .05*np.sin(t[:,None]/97.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    a=bundle(o,h,l,c,r,e,q)
    c2,o2,h2,l2,q2,r2=[x.copy() for x in (c,o,h,l,q,r)]
    for x in (c2,o2,h2,l2):x[3200:]*=1.8
    q2[3200:]*=4.;r2[3200:]*=-1.
    b=bundle(o2,h2,l2,c2,r2,e,q2)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("IK_FUTURE_MUTATION_CAUSALITY_"+str(i))
    epochs=np.arange(WARMUP,n,CLOCK)
    if not np.all(a[1][epochs]) or not np.allclose(
        a[3][epochs].sum(axis=1),1.,atol=1e-12):
        raise ValueError("IK_EPOCH_BUDGET_CONSERVATION")
    gross=np.abs(a[0][epochs]).sum(axis=2)
    if not np.all(np.isclose(gross,0.,atol=1e-12)|
                  np.isclose(gross,1.,atol=1e-12)):
        raise ValueError("IK_OPTIONAL_GROSS_CONSERVATION")
    if not np.allclose(gross[:,0],1.,atol=1e-12):
        raise ValueError("IK_CORE_GROSS_CONSERVATION")
    qgap=q.copy();qgap[700,2]=0.
    g=bundle(o,h,l,c,r,e,qgap)
    if (np.any(g[0][WARMUP,1:]) or g[4][WARMUP,1:].any()
        or not np.isclose(g[0][WARMUP,0].sum(),1.)):
        raise ValueError("IK_ZERO_QUOTE_QUARANTINE")
    return True

if __name__=="__main__":
    assert static_check()
    print("IK_COVARIANCE_RESIDUAL_CAUSAL_AND_QUARANTINE_PASS")
