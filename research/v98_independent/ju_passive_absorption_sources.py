#!/usr/bin/env python3
"""JU precommitted passive-absorption seven-slot V98 independent, 2023-24 TRAINING only.
All features from completed hour t; governor executes only at next actual hour open.
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
PATHS=("JU_core_only","JU_full","JU_minus_opportunity","JU_minus_RV","JU_minus_stress")
PIN="423b2394d8478157361c2d7c72238771ffb2ec01fcad6ae53142733e03840e6c"
COLS=("early_trough_pct","late_rebound_log","late_selloff_log",
      "path_realized_vol","first_half_taker_share","second_half_taker_share")

def load_verified():
    p=HERE/"native_5m_masked_verified_hourly_features.csv"
    raw=p.read_bytes()
    receipt=json.loads((HERE/"native_5m_masked_source_receipt.json").read_text())
    if (hashlib.sha256(raw).hexdigest()!=PIN or
        receipt.get("feature_csv_sha256")!=PIN or
        receipt.get("decision")!="MASKED_5M_SOURCE_ONLY_NO_ECONOMIC_AUTHORIZATION" or
        receipt.get("asset_hours_source_valid")!=67296 or
        receipt.get("asset_hours_expected")!=HOURS*4 or
        receipt.get("archives_verified")+receipt.get("archives_quarantined")!=100):
        raise ValueError("JU_MASKED_NATIVE_5M_PIN_OR_PROVENANCE")
    df=pd.read_csv(p)
    stamps=pd.date_range(START,periods=HOURS,freq="h",tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy()
    f=np.full((HOURS,4,6),np.nan,dtype=float)
    m=np.zeros((HOURS,4),dtype=bool)
    for j,asset in enumerate(ASSETS):
        rows=df.loc[df["asset"]==asset].reset_index(drop=True)
        if (len(rows)!=HOURS or not np.array_equal(rows["open_time"].to_numpy(),stamps)
            or not rows["source_valid"].isin([0,1]).all()):
            raise ValueError("JU_SOURCE_ALIGNMENT_"+asset)
        x=rows[list(COLS)].to_numpy(dtype=float)
        mask=rows["source_valid"].to_numpy(dtype=int).astype(bool)
        if (not np.isfinite(x[mask]).all() or np.isfinite(x[~mask]).any()
            or np.any(x[mask,3]<0) or np.any(x[mask,4:]<0)
            or np.any(x[mask,4:]>1.+1e-8)):
            raise ValueError("JU_SOURCE_MASK_OR_SCHEMA_"+asset)
        f[:,j,:]=x;m[:,j]=mask
    return f,m

def bundle(opening,high,low,close,rate,event,quote,source=None):
    o,h,l,c,r,e,q=[np.asarray(x,dtype=float) for x in
                   (opening,high,low,close,rate,event,quote)]
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1))):
        raise ValueError("JU_INVALID_NATIVE_1H")
    n=len(c)
    f,m=load_verified() if source is None else source
    f=np.asarray(f,dtype=float);m=np.asarray(m,dtype=bool)
    if f.shape!=(n,4,6) or m.shape!=(n,4):
        raise ValueError("JU_NATIVE_5M_SHAPE")
    if (not np.isfinite(f[m]).all() or np.isfinite(f[~m]).any()
        or np.any(f[m,3]<0) or np.any(f[m,4:]<0)
        or np.any(f[m,4:]>1.+1e-8)):
        raise ValueError("JU_NATIVE_5M_MASK_CONTRACT")
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    experts_at=np.zeros((n,4,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        x504=net[t-503:t+1]
        x168=net[t-167:t+1]
        downside=np.maximum(np.sqrt(np.mean(np.minimum(x168,0.)**2,axis=0)),.001)
        score=np.sum(x504,axis=0)/downside
        leaders=np.argsort(-score,kind="stable")[:2]
        core=np.zeros(4,dtype=float);core[leaders]=(.65,.35)
        experts=np.zeros((4,4),dtype=float);experts[0]=core
        good=bool(m[t-167:t+1].all())
        valid[t]=good
        regime="NORMAL"
        budgets=np.zeros(3,dtype=float)
        if good:
            obs=f[t-167:t+1]
            last=obs[-48:]
            sell=np.maximum(0.,.5-last[:,:,5])*np.maximum(0.,last[:,:,1])/np.maximum(last[:,:,3],.001)
            buy=np.maximum(0.,last[:,:,5]-.5)*np.maximum(0.,-last[:,:,2])/np.maximum(last[:,:,3],.001)
            sell_score=np.mean(sell,axis=0)
            buy_score=np.mean(buy,axis=0)
            opp=int(np.argmax(sell_score))
            if sell_score[opp]>0.:
                experts[1,opp]=1.;budgets[0]=.16
            long=int(np.argmax(sell_score))
            shorts=np.argsort(-buy_score,kind="stable")
            short=int(next(k for k in shorts if k!=long))
            experts[2,long]=.5;experts[2,short]=-.5
            budgets[1]=.12
            market72=float(np.sum(np.mean(net[t-71:t+1],axis=1)))
            market24=float(np.sum(np.mean(net[t-23:t+1],axis=1)))
            v24=float(np.mean(f[t-23:t+1,:,3]))
            v168=float(np.mean(obs[:,:,3]))
            ratio=v24/max(v168,1e-12)
            regime=("STRESS" if market72<-.025 or ratio>1.6 else
                    "RECOVERY" if market24>.01 and market72<0. else "NORMAL")
            if regime=="STRESS":
                chosen=int(np.argmin(np.mean(obs[:,:,3],axis=0)))
            elif regime=="RECOVERY":
                chosen=int(np.argmax(sell_score))
            else:
                order=np.argsort(-np.sum(x168,axis=0),kind="stable")
                chosen=int(next(k for k in order if k!=leaders[0]))
            experts[3,chosen]=1.;budgets[2]=.14
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
                raise ValueError("JU_GROSS_CONSERVATION")
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
    f[:,:,4]=.55;f[:,:,5]=.40
    m=np.ones((n,4),dtype=bool)
    a=bundle(o,h,l,c,r,e,q,(f,m))
    cc,oo,hh,ll,qq,rr,ff=[v.copy() for v in (c,o,h,l,q,r,f)]
    for v in (cc,oo,hh,ll):v[2500:]*=1.8
    qq[2500:]*=4.;rr[2500:]*=-1.;ff[2500:,:,1:4]*=2.
    b=bundle(oo,hh,ll,cc,rr,e,qq,(ff,m))
    for i in range(5):
        if not np.array_equal(a[i][:2500],b[i][:2500]):
            raise ValueError("JU_FUTURE_MUTATION_"+str(i))
    fgap=f.copy();fgap[700,2,:]=np.nan
    mgap=m.copy();mgap[700,2]=False
    g=bundle(o,h,l,c,r,e,q,(fgap,mgap))
    if g[3][WARMUP] or not np.allclose(g[0][WARMUP],g[0][WARMUP,0]):
        raise ValueError("JU_QUARANTINE_NOT_PROPAGATED")
    return True

if __name__=="__main__":
    assert static_check()
    print("JU_CAUSAL_PASSIVE_ABSORPTION_SOURCE_PASS")
