#!/usr/bin/env python3
"""JR preregistered seven-slot 5m path/initiative engine. Completed t -> t+1 open."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
from phase803_training_ohlc_official_replay import ASSETS
from phase1260_aj_authenticated_source_digest import HOURS,START

HERE=Path(__file__).resolve().parent
WARMUP=744;CLOCK=168
GROSS={"NORMAL":.95,"STRESS":.70,"RECOVERY":.90}
PATHS=("JR_core_only","JR_full","JR_minus_opportunity","JR_minus_RV","JR_minus_stress")

def load_verified():
    path=HERE/"native_5m_masked_verified_hourly_features.csv"
    raw=path.read_bytes()
    receipt=json.loads((HERE/"native_5m_masked_source_receipt.json").read_text())
    if (receipt["decision"]!="MASKED_5M_SOURCE_ONLY_NO_ECONOMIC_AUTHORIZATION"
        or hashlib.sha256(raw).hexdigest()!=receipt["feature_csv_sha256"]
        or receipt["asset_hours_expected"]!=HOURS*4):
        raise ValueError("JR_MASKED_5M_SOURCE_SHA_OR_CONTRACT")
    df=pd.read_csv(path)
    times=pd.date_range(START,periods=HOURS,freq="h",tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy()
    features=np.full((HOURS,4,6),np.nan,dtype=float)
    valid=np.zeros((HOURS,4),dtype=bool)
    columns=("early_trough_pct","late_rebound_log","late_selloff_log",
             "path_realized_vol","first_half_taker_share","second_half_taker_share")
    for k,asset in enumerate(ASSETS):
        rows=df.loc[df["asset"]==asset].reset_index(drop=True)
        if (len(rows)!=HOURS or not np.array_equal(rows["open_time"].to_numpy(),times)
            or not rows["source_valid"].isin([0,1]).all()):
            raise ValueError("JR_MASKED_5M_HOURLY_ALIGNMENT_"+asset)
        x=rows[list(columns)].to_numpy(dtype=float)
        m=rows["source_valid"].to_numpy(dtype=int).astype(bool)
        if (not np.isfinite(x[m]).all() or np.isfinite(x[~m]).any()
            or np.any(x[m,3]<0) or np.any(x[m,4:]<0)
            or np.any(x[m,4:]>1+1e-8)):
            raise ValueError("JR_MASKED_5M_FEATURE_INTEGRITY_"+asset)
        features[:,k,:]=x;valid[:,k]=m
    return features,valid

def bundle(opening,high,low,close,rate,event,quote,source=None):
    o,h,l,c,r,e,q=[np.asarray(v,dtype=float) for v in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1
        or any(v.shape!=c.shape for v in (o,h,l,r,e,q))
        or any(not np.isfinite(v).all() for v in (o,h,l,c,r,e,q))
        or np.any(o<=0) or np.any(c<=0) or np.any(l<=0)
        or np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c))
        or np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JR_INVALID_NATIVE_1H")
    n=len(c)
    f,m=load_verified() if source is None else source
    f=np.asarray(f,dtype=float);m=np.asarray(m,dtype=bool)
    if f.shape!=(n,4,6) or m.shape!=(n,4):
        raise ValueError("JR_NATIVE_5M_SHAPE")
    if not np.isfinite(f[m]).all() or np.isfinite(f[~m]).any():
        raise ValueError("JR_NATIVE_5M_MASK_CONTRACT")
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    experts_at=np.zeros((n,4,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        x336=net[t-335:t+1];x168=net[t-167:t+1]
        down=np.maximum(np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0)),.001)
        score=np.sum(x336,axis=0)/down
        leaders=np.argsort(-score,kind="stable")[:2]
        core=np.zeros(4);core[leaders]=[.70,.30]
        experts=np.zeros((4,4),dtype=float);experts[0]=core
        good=bool(m[t-167:t+1].all())
        valid[t]=good
        regime="NORMAL";budgets=np.zeros(3)
        if good:
            recent=f[t-47:t+1]
            early=recent[:,:,0];rebound=recent[:,:,1]
            selloff=recent[:,:,2];vol=recent[:,:,3]
            shift=recent[:,:,5]-recent[:,:,4]
            opp=np.mean(np.maximum(rebound+early,0.)*np.maximum(shift,0.),axis=0)/np.maximum(
                np.mean(vol,axis=0),.001)
            if np.any(opp>0):
                experts[1,int(np.argmax(opp))]=1.;budgets[0]=.16
            rv=np.mean(shift,axis=0)/np.maximum(np.mean(vol,axis=0),.001)
            hi=int(np.argmax(rv));lo=int(np.argmin(rv))
            if hi==lo:raise ValueError("JR_RV_DISTINCT_ASSETS")
            experts[2,hi]=.5;experts[2,lo]=-.5;budgets[1]=.14
            v24=float(np.mean(f[t-23:t+1,:,3]))
            v168=float(np.mean(f[t-167:t+1,:,3]))
            ratio=v24/max(v168,1e-9)
            market24=float(np.mean(net[t-23:t+1].sum(axis=0)))
            market72=float(np.mean(net[t-71:t+1].sum(axis=0)))
            regime=("STRESS" if market24<-.01 or ratio>1.5 else
                    "RECOVERY" if market24>.01 and market72<0. else "NORMAL")
            if regime=="STRESS":
                liquidation=np.mean(selloff[-24:]*vol[-24:],axis=0)
                experts[3,int(np.argmin(liquidation))]=-1.
            elif regime=="RECOVERY":
                absorb=np.mean(np.maximum(rebound[-24:],0.)*
                               np.maximum(shift[-24:],0.),axis=0)
                if np.any(absorb>0):experts[3,int(np.argmax(absorb))]=1.
            if np.any(experts[3]):
                budgets[2]=.08+.12*min(1.,max(0.,ratio-1.))
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
                raise ValueError("JR_PORTFOLIO_GROSS_CONSERVATION")
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
    f=np.zeros((n,4,6),dtype=float)
    f[:,:,0]=-.02;f[:,:,1]=.03;f[:,:,2]=-.01;f[:,:,3]=.01
    f[:,:,4]=.40;f[:,:,5]=.60
    m=np.ones((n,4),dtype=bool)
    a=bundle(o,h,l,c,r,e,q,(f,m))
    cc,oo,hh,ll,qq,rr,ff=[v.copy() for v in (c,o,h,l,q,r,f)]
    for v in (cc,oo,hh,ll):v[2500:]*=1.8
    qq[2500:]*=4.;rr[2500:]*=-1.;ff[2500:]*=2.
    b=bundle(oo,hh,ll,cc,rr,e,qq,(ff,m))
    for i in range(5):
        if not np.array_equal(a[i][:2500],b[i][:2500]):
            raise ValueError("JR_FUTURE_MUTATION_"+str(i))
    fgap=f.copy();fgap[700,2]=np.nan
    mgap=m.copy();mgap[700,2]=False
    g=bundle(o,h,l,c,r,e,q,(fgap,mgap))
    if g[3][WARMUP] or not np.allclose(g[0][WARMUP],g[0][WARMUP,0]):
        raise ValueError("JR_QUARANTINE_NOT_PROPAGATED")
    return True

if __name__=="__main__":
    assert static_check()
    print("JR_NATIVE_5M_PATH_CAUSAL_SOURCE_PASS")
