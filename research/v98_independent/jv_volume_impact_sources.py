#!/usr/bin/env python3
"""JV preregistered intrahour quote-volume concentration seven-slot V98 independent.
Completed hour t features only; next actual t+1 open, 2023-2024 TRAINING only.
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
CLOCK=336
GROSS={"NORMAL":.90,"STRESS":.72,"RECOVERY":.85}
PATHS=("JV_core_only","JV_full","JV_minus_opportunity","JV_minus_RV","JV_minus_stress")
PIN="2cfc45817b5f8ec3ddc3c51332393693c5f06077c85bad43f2ae0b454c7720d2"
COLS=("volume_hhi","signed_volume_impulse","late_volume_share","directional_efficiency")

def load_verified():
    p=HERE/"jv_volume_impact_hourly.csv"
    raw=p.read_bytes()
    receipt=json.loads((HERE/"jv_volume_impact_source_receipt.json").read_text())
    if (hashlib.sha256(raw).hexdigest()!=PIN or
        receipt.get("source_feature_sha256")!=PIN or
        receipt.get("decision")!="PASS_JV_VOLUME_IMPACT_SOURCE_ONLY_NOT_ECONOMIC" or
        receipt.get("valid_asset_hours")!=67296 or
        receipt.get("full_asset_hours")!=HOURS*4 or
        receipt.get("vendor_archives_authenticated")!=100):
        raise ValueError("JV_NATIVE_5M_SOURCE_PIN_OR_PROVENANCE")
    df=pd.read_csv(p)
    stamps=pd.date_range(START,periods=HOURS,freq="h",tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ").to_numpy()
    f=np.full((HOURS,4,4),np.nan,dtype=float)
    m=np.zeros((HOURS,4),dtype=bool)
    for j,asset in enumerate(ASSETS):
        rows=df.loc[df["asset"]==asset].reset_index(drop=True)
        if (len(rows)!=HOURS or not np.array_equal(rows["open_time"].to_numpy(),stamps)
            or not rows["source_valid"].isin([0,1]).all()):
            raise ValueError("JV_SOURCE_ALIGNMENT_"+asset)
        x=rows[list(COLS)].to_numpy(dtype=float)
        mask=rows["source_valid"].to_numpy(dtype=int).astype(bool)
        if (not np.isfinite(x[mask]).all() or np.isfinite(x[~mask]).any()
            or np.any(x[mask,0]<0) or np.any(x[mask,0]>1.+1e-8)
            or np.any(x[mask,2]<0) or np.any(x[mask,2]>1.+1e-8)):
            raise ValueError("JV_SOURCE_MASK_OR_SCHEMA_"+asset)
        f[:,j,:]=x;m[:,j]=mask
    if not np.array_equal(m[:,0],m[:,1]) or not np.array_equal(m[:,1],m[:,2]) or not np.array_equal(m[:,2],m[:,3]):
        raise ValueError("JV_CROSS_ASSET_QUARANTINE")
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
        raise ValueError("JV_INVALID_NATIVE_1H")
    n=len(c)
    f,m=load_verified() if source is None else source
    f=np.asarray(f,dtype=float);m=np.asarray(m,dtype=bool)
    if f.shape!=(n,4,4) or m.shape!=(n,4):
        raise ValueError("JV_NATIVE_5M_SHAPE")
    if (not np.isfinite(f[m]).all() or np.isfinite(f[~m]).any()
        or np.any(f[m,0]<0) or np.any(f[m,0]>1.+1e-8)
        or np.any(f[m,2]<0) or np.any(f[m,2]>1.+1e-8)):
        raise ValueError("JV_NATIVE_5M_MASK_CONTRACT")
    ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e
    targets=np.zeros((n,5,4),dtype=float)
    updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool)
    experts_at=np.zeros((n,4,4),dtype=float)
    for t in range(WARMUP,n,CLOCK):
        x672=net[t-671:t+1]
        x336=net[t-335:t+1]
        down=np.maximum(np.sqrt(np.mean(np.minimum(x336,0.)**2,axis=0)),.001)
        score=np.sum(x672,axis=0)/down
        leaders=np.argsort(-score,kind="stable")[:2]
        core=np.zeros(4);core[leaders]=(.65,.35)
        experts=np.zeros((4,4));experts[0]=core
        good=bool(m[t-167:t+1].all())
        valid[t]=good
        regime="NORMAL";budgets=np.zeros(3)
        if good:
            obs=f[t-167:t+1]
            recent=obs[-72:]
            hhi=recent[:,:,0];impulse=recent[:,:,1]
            late=recent[:,:,2];eff=recent[:,:,3]
            opp=np.mean(impulse*np.maximum(late-1./3.,0.),axis=0)
            if np.any(opp>0):
                experts[1,int(np.argmax(opp))]=1.;budgets[0]=.16
            ranks=np.argsort(np.mean(eff,axis=0),kind="stable")
            experts[2,int(ranks[-1])]=.5
            experts[2,int(ranks[0])]=-.5
            budgets[1]=.12
            market72=float(np.sum(np.mean(net[t-71:t+1],axis=1)))
            market24=float(np.sum(np.mean(net[t-23:t+1],axis=1)))
            hhi24=float(np.mean(f[t-23:t+1,:,0]))
            hhi168=float(np.mean(obs[:,:,0]))
            regime=("STRESS" if market72<-.025 and hhi24>hhi168 else
                    "RECOVERY" if market24>.01 and market72<0. else "NORMAL")
            if regime=="STRESS":
                chosen=int(np.argmin(np.mean(hhi,axis=0)))
            elif regime=="RECOVERY":
                chosen=int(np.argmax(np.mean(impulse,axis=0)))
            else:
                chosen=int(np.argmax(np.mean(eff-hhi,axis=0)))
            experts[3,chosen]=1.;budgets[2]=.14
        regimes[t]=regime
        experts_at[t]=experts
        for path in range(5):
            if path==0 or not good:target=core.copy()
            else:
                b=budgets.copy()
                if path>=2:b[path-2]=0.
                target=(1.-b.sum())*core+b@experts[1:]
            if not np.isfinite(target).all() or np.abs(target).sum()>1.+1e-10:
                raise ValueError("JV_GROSS_CONSERVATION")
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
    f=np.zeros((n,4,4),dtype=float)
    f[:,:,0]=.13;f[:,:,1]=.002;f[:,:,2]=.40;f[:,:,3]=.35
    m=np.ones((n,4),dtype=bool)
    a=bundle(o,h,l,c,r,e,q,(f,m))
    cc,oo,hh,ll,qq,rr,ff=[v.copy() for v in (c,o,h,l,q,r,f)]
    for v in (cc,oo,hh,ll):v[2500:]*=1.8
    qq[2500:]*=4.;rr[2500:]*=-1.;ff[2500:,:,1]*=2.
    b=bundle(oo,hh,ll,cc,rr,e,qq,(ff,m))
    for i in range(5):
        if not np.array_equal(a[i][:2500],b[i][:2500]):
            raise ValueError("JV_FUTURE_MUTATION_"+str(i))
    fgap=f.copy();fgap[700,2,:]=np.nan
    mgap=m.copy();mgap[700,2]=False
    g=bundle(o,h,l,c,r,e,q,(fgap,mgap))
    if g[3][WARMUP] or not np.allclose(g[0][WARMUP],g[0][WARMUP,0]):
        raise ValueError("JV_QUARANTINE_NOT_PROPAGATED")
    return True

if __name__=="__main__":
    assert static_check()
    print("JV_CAUSAL_INTRAHOUR_VOLUME_IMPACT_PASS")
