#!/usr/bin/env python3
"""KH prospective seven-slot temporal 1m taker-buy flow engine; source assembly, NO PnL."""
from __future__ import annotations
import calendar,csv,hashlib,io,json,math,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
RAW=ROOT/"v98_intrabar_full_1m_raw"
WARMUP=744
CLOCK=168
HOURS=18288
GROSS={"NORMAL":.88,"STRESS":.70,"RECOVERY":.82}
PATHS=("KH_core_only","KH_full","KH_minus_opportunity","KH_minus_RV","KH_minus_stress")
ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
MONTHS=("2022-12",)+tuple(f"{y}-{m:02d}" for y in (2023,2024) for m in range(1,13))
START=int(datetime(2022,12,1,tzinfo=timezone.utc).timestamp()*1000)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def build_intrabar():
    """Full original 100 monthly archives; no 2025; no synthetic missing-bar repair."""
    p=(ROOT/"v98_intrabar_full_1m_primary_receipt.json")
    a=(ROOT/"v98_intrabar_full_1m_independent_receipt.json")
    first=json.loads(p.read_text());second=json.loads(a.read_text())
    if (first.get("decision")!="PASS_FULL_1M_SOURCE_REQUIRES_INDEPENDENT_AUDIT" or
        second.get("decision")!="PASS_FULL_1M_INDEPENDENT_SOURCE_ONLY_NOT_PNL" or
        first.get("canonical_manifest_sha256")!=second.get("canonical_manifest_sha256")):
        raise ValueError("KH_FULL_1M_SOURCE_GATE_NOT_PASSED")
    early=np.zeros((HOURS,4));late=np.zeros_like(early)
    late_ret=np.zeros_like(early);valid=np.zeros((HOURS,4),dtype=bool)
    for j,asset in enumerate(ASSETS):
        for month in MONTHS:
            y,m=map(int,month.split("-"));days=calendar.monthrange(y,m)[1]
            begin=int(datetime(y,m,1,tzinfo=timezone.utc).timestamp()*1000)
            name=f"{asset}-1m-{month}.zip"
            raw=(RAW/name).read_bytes()
            side=(RAW/(name+".CHECKSUM")).read_text().split()[0].lower()
            prior=next((r for r in first["records"] if r["asset"]==asset and r["month"]==month),None)
            if prior is None or prior.get("status")!="PASS" or sha(raw)!=side or prior.get("sha256")!=side:
                raise ValueError("KH_ORIGINAL_1M_ARCHIVE_PIN_"+name)
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                files=[f for f in z.namelist() if not f.endswith("/")]
                if len(files)!=1 or files[0].split("/")[-1]!=name[:-4]+".csv":
                    raise ValueError("KH_1M_MEMBER_"+name)
                reader=csv.reader(io.TextIOWrapper(z.open(files[0]),encoding="utf-8-sig"))
                count=0;eq=eb=lq=lb=0.;close44=None
                for row in reader:
                    if row and row[0].strip().lower() in ("open_time","opentime"):continue
                    if len(row)<11:raise ValueError("KH_1M_SCHEMA")
                    if int(row[0])!=begin+count*60000:
                        raise ValueError("KH_1M_TIME_ORDER_"+name)
                    q=float(row[7]);buy=float(row[10]);cl=float(row[4])
                    if not np.isfinite([q,buy,cl]).all() or q<0 or buy<0 or buy>q+1e-6*max(1,q) or cl<=0:
                        raise ValueError("KH_1M_TAKER_QUOTE_"+name)
                    k=count%60;hour=(begin-START)//3600000+count//60
                    if not 0<=hour<HOURS:raise ValueError("KH_HOUR_FIREWALL")
                    if k<15:eq+=q;eb+=buy
                    if k>=45:lq+=q;lb+=buy
                    if k==44:close44=cl
                    if k==59:
                        if close44 is None:raise ValueError("KH_MINUTE44")
                        if eq>0 and lq>0 and eb<=eq*(1+1e-6) and lb<=lq*(1+1e-6):
                            early[hour,j]=eb/eq;late[hour,j]=lb/lq
                            late_ret[hour,j]=math.log(cl/close44)
                            valid[hour,j]=True
                        eq=eb=lq=lb=0.;close44=None
                    count+=1
                if count!=days*1440:raise ValueError("KH_MONTH_COVERAGE_"+name)
    return early,late,late_ret,valid,{"full_primary_sha256":sha(p.read_bytes()),
        "full_independent_sha256":sha(a.read_bytes()),
        "canonical_manifest_sha256":first["canonical_manifest_sha256"],
        "original_months":100,"minutes":4389120,"hours":73152}
def bundle(opening,high,low,close,rate,event,quote,early,late,late_ret,valid_hour):
    o,h,l,c,r,e,q,eb,lb,lr=[np.asarray(x,dtype=float) for x in
        (opening,high,low,close,rate,event,quote,early,late,late_ret)]
    v=np.asarray(valid_hour,dtype=bool)
    if (c.ndim!=2 or c.shape[1]!=4 or len(c)<WARMUP+1 or
        any(x.shape!=c.shape for x in (o,h,l,r,e,q,eb,lb,lr,v)) or
        any(not np.isfinite(x).all() for x in (o,h,l,c,r,e,q,eb,lb,lr)) or
        np.any(o<=0) or np.any(c<=0) or np.any(l<=0) or
        np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or
        np.any(q<0) or np.any((e!=0)&(e!=1)) or
        np.any(eb<0) or np.any(lb<0) or np.any(eb>1.000001) or np.any(lb>1.000001)):
        raise ValueError("KH_INVALID_CANONICAL_OR_INTRABAR")
    n=len(c);ret=np.zeros_like(c);ret[1:]=np.diff(np.log(c),axis=0)
    net=ret-r*e;market=net.mean(axis=1)
    targets=np.zeros((n,5,4));updates=np.zeros(n,dtype=bool)
    regimes=np.full(n,"NORMAL",dtype="<U10")
    valid=np.zeros(n,dtype=bool);budgets=np.zeros((n,3))
    for t in range(WARMUP,n,CLOCK):
        downside=np.maximum(np.sqrt(np.mean(np.minimum(net[t-335:t+1],0.)**2,axis=0)),.002)
        rank=net[t-671:t+1].sum(axis=0)/downside
        leaders=np.argsort(-rank,kind="stable")[:2]
        core=np.zeros(4);inverse=1./downside[leaders]
        core[leaders]=inverse/inverse.sum()
        m72=float(market[t-71:t+1].sum())
        m24=float(market[t-23:t+1].sum())
        prior72=float(market[t-95:t-23].sum())
        regime=("STRESS" if m72<-.03 else
                "RECOVERY" if m24>.012 and prior72<0 else "NORMAL")
        good=bool(np.all(v[t-71:t+1]))
        valid[t]=good
        experts=np.zeros((3,4));b=np.zeros(3)
        if good:
            change=lb-eb
            opp=np.mean(np.maximum(change[t-71:t+1],0.)*
                        np.maximum(lr[t-71:t+1],0.),axis=0)
            if np.max(opp)>0:
                experts[0,int(np.argmax(opp))]=1.
                strength=float(np.mean(np.maximum(change[t-71:t+1],0.)))
                b[0]=.12+.06*np.clip(strength/.10,0.,1.)
            meanchange=change[t-71:t+1].mean(axis=0)
            spread=float(meanchange.max()-meanchange.min())
            if spread>.03:
                k=int(np.argmax(meanchange));s=int(np.argmin(meanchange))
                experts[1,k]=.5;experts[1,s]=-.5
                b[1]=.08+.04*np.clip((spread-.03)/.12,0.,1.)
            if regime=="STRESS":
                score=change[t-23:t+1].mean(axis=0)-.5*np.maximum(-lr[t-23:t+1],0.).mean(axis=0)
            elif regime=="RECOVERY":
                score=(np.maximum(lr[t-23:t+1],0.)*lb[t-23:t+1]).mean(axis=0)
            else:
                score=lb[t-71:t+1].mean(axis=0)-.5*lr[t-71:t+1].std(axis=0)
            experts[2,int(np.argmax(score))]=1.
            b[2]=.08+.02*np.clip(abs(m72)/.06,0.,1.)
        budgets[t]=b
        for path in range(5):
            bp=b.copy()
            if path==0:bp[:]=0.
            elif path>=2:bp[path-2]=0.
            weights=(1.-float(bp.sum()))*core+bp@experts
            if not np.isfinite(weights).all() or np.abs(weights).sum()>1.+1e-10 or bp.sum()>.4+1e-12:
                raise ValueError("KH_GROSS_OR_FINITE")
            targets[t,path]=weights
        if not good and not np.allclose(targets[t],targets[t,0]):
            raise ValueError("KH_INVALID_INTRABAR_OPTIONAL_LEAK")
        regimes[t]=regime;updates[t]=True
    return targets,updates,regimes,valid,budgets
def static_check():
    n=3800;t=np.arange(n,dtype=float)
    c=100*np.exp(t[:,None]*np.array([[.0002,.0003,.0004,.0005]])+
                 .045*np.sin(t[:,None]/87.+np.arange(4)))
    o=c*(1.-.002*np.sin(t[:,None]/11.+np.arange(4)))
    h=np.maximum(o,c)*1.01;l=np.minimum(o,c)*.99
    q=1e6*(1.2+.35*np.sin(t[:,None]/37.+np.arange(4)))
    r=np.full_like(c,.0001);e=np.zeros_like(c);e[::8]=1.
    eb=.48+.10*np.sin(t[:,None]/91.+np.arange(4))
    lb=.52+.10*np.sin(t[:,None]/61.+np.arange(4))
    lr=.004*np.sin(t[:,None]/19.+np.arange(4))
    valid=np.ones_like(c,dtype=bool)
    a=bundle(o,h,l,c,r,e,q,eb,lb,lr,valid)
    cc,oo,hh,ll,qq,rr,ee,bb,lr2=[z.copy() for z in (c,o,h,l,q,r,eb,lb,lr)]
    for z in (cc,oo,hh,ll):z[3200:]*=1.8
    qq[3200:]*=4.;rr[3200:]*=-1.
    ee[3200:]=.9;bb[3200:]=.1;lr2[3200:]*=-2.
    b=bundle(oo,hh,ll,cc,rr,e,qq,ee,bb,lr2,valid)
    for i in range(5):
        if not np.array_equal(a[i][:3200],b[i][:3200]):
            raise ValueError("KH_FUTURE_MUTATION_"+str(i))
    bad=valid.copy();bad[700,2]=False
    gap=bundle(o,h,l,c,r,e,q,eb,lb,lr,bad)
    if gap[3][WARMUP] or not np.allclose(gap[0][WARMUP],gap[0][WARMUP,0]):
        raise ValueError("KH_QUARANTINE")
    if np.any(np.abs(a[0][np.arange(WARMUP,n,CLOCK)]).sum(axis=2)>1.+1e-10):
        raise ValueError("KH_GROSS")
    return True
if __name__=="__main__":
    assert static_check()
    print("KH_TEMPORAL_1M_CAUSAL_SYNTHETIC_PASS")
