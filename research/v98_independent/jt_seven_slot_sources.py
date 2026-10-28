#!/usr/bin/env python3
"""JT preregistered complete cross-asset propagation seven-slot engine, source/targets only.
Completed t features -> actual t+1 open; 2023-2024 training only.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from phase803_training_ohlc_official_replay import ASSETS
from phase1260_aj_authenticated_source_digest import HOURS,START

HERE=Path(__file__).resolve().parent
WARMUP=744
CLOCK=168
GROSS={"NORMAL":.90,"STRESS":.72,"RECOVERY":.85}
PATHS=("JT_core_only","JT_full","JT_minus_opportunity","JT_minus_RV","JT_minus_stress")
PIN="7599bc71a93539e0ba65a48aa61be391c56c0967fc9aebfa87c7c67aff575e30"
COLS=("down_beta","down_resilience","cojump_frequency","up_capture")

def load_verified():
    p=HERE/"jt_downside_resilience_hourly.csv"
    raw=p.read_bytes()
    receipt=json.loads((HERE/"jt_cross_asset_5m_propagation_source_receipt.json").read_text())
    if (hashlib.sha256(raw).hexdigest()!=PIN
        or receipt.get("source_feature_sha256")!=PIN
        or receipt.get("decision")!="PASS_JT_DOWNSIDE_SOURCE_ONLY_NOT_ECONOMIC"
        or receipt.get("valid_alt_asset_hours")!=50472
        or receipt.get("full_alt_asset_hours")!=HOURS*3):
        raise ValueError("JT_SOURCE_SHA_OR_RECEIPT")
    df=pd.read_csv(p)
    stamps=pd.date_range(START,periods=HOURS,freq="h",tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy()
    f=np.full((HOURS,3,4),np.nan,dtype=float)
    mask=np.zeros((HOURS,3),dtype=bool)
    for j,asset in enumerate(ASSETS[1:]):
        rows=df.loc[df["asset"]==asset].reset_index(drop=True)
        if (len(rows)!=HOURS or not np.array_equal(rows["open_time"].to_numpy(),stamps)
            or not rows["source_valid"].isin([0,1]).all()):
            raise ValueError("JT_SOURCE_ALIGNMENT_"+asset)
        m=rows["source_valid"].to_numpy(dtype=int).astype(bool)
        x=rows[list(COLS)].to_numpy(dtype=float)
        if not np.isfinite(x[m]).all() or np.isfinite(x[~m]).any():
            raise ValueError("JT_SOURCE_MASK_"+asset)
        f[:,j,:]=x;mask[:,j]=m
    if not np.array_equal(mask[:,0],mask[:,1]) or not np.array_equal(mask[:,1],mask[:,2]):
        raise ValueError("JT_CROSS_ASSET_MONTH_MASK")
    return f,mask

def bundle(opening,high,low,close,rate,event,quote,source=None):
    o,h,l,c,r,e,q=[np.asarray(z,dtype=float) for z in
                    (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(z.shape!=c.shape for z in (o,h,l,r,e,q))
        or any(not np.isfinite(z).all() for z in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JT_INVALID_NATIVE_1H")
    n=len(c)
    f,m=load_verified() if source is None else source
    f=np.asarray(f,dtype=float);m=np.asarray(m,dtype=bool)
    if f.shape!=(n,3,4) or m.shape!=(n,3):
        raise ValueError("JT_NATIVE_5M_SHAPE")
    if not np.isfinite(f[m]).all() or np.isfinite(f[~m]).any():
        raise ValueError("JT_NATIVE_5M_MASK_CONTRACT")
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    experts_at=np.zeros((n,4,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        prior=net[t-503:t+1]
        recent=net[t-167:t+1]
        vol=np.maximum(np.sqrt(np.mean(np.minimum(recent,0.)**2,axis=0)),.001)
        score=np.sum(prior,axis=0)/vol
        leaders=np.argsort(-score,kind="stable")[:2]
        core=np.zeros(4);core[leaders]=(.65,.35)
        experts=np.zeros((4,4),dtype=float);experts[0]=core
        good=bool(m[t-167:t+1].all())
        valid[t]=good
        regime="NORMAL";budgets=np.zeros(3,dtype=float)
        if good:
            obs=f[t-47:t+1]
            beta=np.mean(obs[:,:,0],axis=0)
            resilience=obs[:,:,1]
            rs=np.mean(resilience,axis=0)/np.maximum(np.std(resilience,axis=0),.0001)
            winner=int(np.argmax(rs))
            if rs[winner]>0:
                experts[1,winner+1]=1.
                budgets[0]=.18
            rank=np.argsort(beta,kind="stable")
            experts[2,int(rank[0])+1]=.5
            experts[2,int(rank[-1])+1]=-.5
            budgets[1]=.14
            btc24=float(np.sum(net[t-23:t+1,0]))
            btc72=float(np.sum(net[t-71:t+1,0]))
            cojump24=float(np.mean(f[t-23:t+1,:,2]))
            regime=("STRESS" if btc24<-.01 or cojump24>.25 else
                    "RECOVERY" if btc24>.01 and btc72<0. else "NORMAL")
            if regime=="STRESS":
                chosen=int(np.argmax(np.mean(resilience,axis=0)))
            elif regime=="RECOVERY":
                chosen=int(np.argmax(np.mean(obs[:,:,3],axis=0)))
            else:
                chosen=int(np.argmin(beta))
            experts[3,chosen+1]=1.
            budgets[2]=.16
        regimes[t]=regime
        experts_at[t]=experts
        for path in range(5):
            if path==0 or not good:
                target=core.copy()
            else:
                b=budgets.copy()
                if path>=2:b[path-2]=0.
                target=(1.-b.sum())*core+b@experts[1:]
            if not np.isfinite(target).all() or np.abs(target).sum()>1.+1e-10:
                raise ValueError("JT_GROSS_CONSERVATION")
            targets[t,path]=target
        updates[t]=True
    return targets,updates,regimes,valid,experts_at

def static_check():
    n=3000;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .04*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.2*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    f=np.zeros((n,3,4),dtype=float)
    f[:,:,0]=1.2;f[:,:,1]=.001;f[:,:,2]=.20;f[:,:,3]=1.1
    m=np.ones((n,3),dtype=bool)
    a=bundle(o,h,l,c,r,e,q,(f,m))
    cc,oo,hh,ll,qq,rr,ff=[v.copy() for v in (c,o,h,l,q,r,f)]
    for v in (cc,oo,hh,ll):v[2500:]*=1.8
    qq[2500:]*=4.;rr[2500:]*=-1.;ff[2500:]*=2.
    b=bundle(oo,hh,ll,cc,rr,e,qq,(ff,m))
    for i in range(5):
        if not np.array_equal(a[i][:2500],b[i][:2500]):
            raise ValueError("JT_FUTURE_MUTATION_"+str(i))
    fgap=f.copy();fgap[700,1,:]=np.nan
    mgap=m.copy();mgap[700,1]=False
    g=bundle(o,h,l,c,r,e,q,(fgap,mgap))
    if g[3][WARMUP] or not np.allclose(g[0][WARMUP],g[0][WARMUP,0]):
        raise ValueError("JT_QUARANTINE_NOT_PROPAGATED")
    return True

if __name__=="__main__":
    assert static_check()
    print("JT_CAUSAL_SOURCE_PASS")
