#!/usr/bin/env python3
"""PK premium-dislocation seven-slot composed V98 training. 2025 exposed; no holdout."""
import csv, datetime as dt, hashlib, json, math
from pathlib import Path
import numpy as np
from ot_breadth_dispersion import source_gate, physical, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP
from ot_independent_oracle import independent_fills

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
PREMIUM_SHA="c301a38642f229ca2746ae33baaf58e4bb21ac280a1a99dbbc328cc074caaad4"
CLOCK=tuple(range(WARMUP,HOURS,STEP))
BOOKS={"PK_full":(0,1,2,3),"PK_core_only":(0,),
       "PK_minus_opportunity":(0,2,3),"PK_minus_RV":(0,1,3),
       "PK_minus_stress":(0,1,2)}
PRIORITY={"discount":(1,3,2),"crowded":(2,3,1),"balanced":(2,1,3)}

def load_premium(path, expected_time):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=PREMIUM_SHA:
        raise ValueError("PK_PREMIUM_SOURCE_SHA_MISMATCH")
    p=np.empty((HOURS,4),float)
    start=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
    with path.open(newline="") as f:
        rows=csv.DictReader(f)
        if rows.fieldnames!=["asset","bar_open_utc","premium_open","premium_high","premium_low","premium_close","source_zip_sha256"]:
            raise ValueError("PK_PREMIUM_SCHEMA")
        count=0
        for row in rows:
            hour,j=divmod(count,4)
            if hour>=HOURS or row["asset"]!=ASSETS[j]:
                raise ValueError("PK_PREMIUM_ORDER")
            timestamp=dt.datetime.fromisoformat(row["bar_open_utc"])
            if timestamp!=start+dt.timedelta(hours=hour) or timestamp!=expected_time[hour].to_pydatetime():
                raise ValueError("PK_PREMIUM_CLOCK")
            o,h,l,c=[float(row[k]) for k in ("premium_open","premium_high","premium_low","premium_close")]
            if not all(math.isfinite(x) and abs(x)<1 for x in (o,h,l,c)) or l>min(o,c)+1e-10 or h<max(o,c)-1e-10:
                raise ValueError("PK_PREMIUM_GEOMETRY")
            if len(row["source_zip_sha256"])!=64:
                raise ValueError("PK_PREMIUM_VENDOR_PROVENANCE")
            p[hour,j]=c
            count+=1
    if count!=HOURS*4 or not np.isfinite(p).all():
        raise ValueError("PK_PREMIUM_COMPLETENESS")
    return p

def signals(d,premium):
    c=np.asarray(d["c"],float)
    if c.shape!=(HOURS,4) or premium.shape!=(HOURS,4) or not np.isfinite(premium).all() or np.any(c<=0):
        raise ValueError("PK_SIGNAL_GEOMETRY")
    p=np.log(c);out={}
    for t in CLOCK:
        # Premium OHLC bar indexed t is not complete at price-close decision t.
        current=premium[t-1]
        baseline=np.median(premium[t-168:t],axis=0)
        sigma=np.maximum(np.std(premium[t-672:t],axis=0),.0002)
        z=(current-baseline)/sigma
        drift=current-premium[t-25]
        r24=p[t]-p[t-24];r72=p[t]-p[t-72];r336=p[t]-p[t-336]
        raw=np.zeros((4,4),float)
        hourly=np.diff(p[t-336:t+1],axis=0)
        quality=r336/np.maximum(np.std(hourly,axis=0)*math.sqrt(336),.04)
        eligible=sorted((j for j in range(4) if r336[j]>0 and z[j]<.5 and r72[j]>-.06),
                        key=lambda j:(-quality[j],j))
        for j,w in zip(eligible[:2],(.40,.22)):raw[0,j]=w
        opportunity=sorted((j for j in range(4) if z[j]<-1. and drift[j]>0 and r24[j]>0),
                           key=lambda j:(z[j],j))
        if opportunity:raw[1,opportunity[0]]=.20
        high=min((1,2,3),key=lambda j:(-z[j],j))
        low=min((1,2,3),key=lambda j:(z[j],j))
        if high!=low and z[high]-z[low]>1.6 and drift[low]>drift[high]:
            raw[2,high]=-.12;raw[2,low]=.12
        if r72[0]<-.10 and z[0]<-1.2 and drift[0]>0:
            raw[3,0]=.18
        elif r72[0]>.10 and z[0]>1.2 and drift[0]<0:
            raw[3,0]=-.18
        median=float(np.median(z))
        mode="discount" if median<-.6 else "crowded" if median>.6 else "balanced"
        out[t]=(raw,mode,(z,drift))
    if len(out)!=157:raise ValueError("PK_WEEKLY_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PK_ALLOCATOR_GEOMETRY")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    core=float(np.abs(held[0]).sum())
    if core>.62+1e-10:raise ValueError("PK_CORE_GROSS")
    room=min(.30,max(0.,.84-core))
    for slot in PRIORITY[mode]:
        if slot not in active or room<=1e-12:continue
        gross=float(np.abs(raw[slot]).sum())
        if gross<=1e-12:continue
        take=min(room,gross)
        held[slot]=raw[slot]*(take/gross)
        room-=take
    if np.abs(held).sum()>.84+1e-10 or np.abs(held[1:]).sum()>.30+1e-10:
        raise ValueError("PK_GROSS")
    return held

def target_books(decisions):
    return {name:{t:allocate(raw,mode,active) for t,(raw,mode,_) in decisions.items()}
            for name,active in BOOKS.items()}

def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None]
    j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.00003*t*(1+j/5)+.09*np.sin(t/53+j))
    prem=np.broadcast_to(.0003*np.sin(t/27+j)+.0001*np.cos(t/91),(HOURS,4)).copy()
    d={"c":c,"rate":np.zeros((HOURS,4)),"event":np.zeros((HOURS,4),bool)}
    a=signals(d,prem)
    d2={k:v.copy() for k,v in d.items()};p2=prem.copy()
    d2["c"][15000:]*=np.array([1.3,.8,1.5,.7])
    d2["rate"][15000::8]=.03;d2["event"][15000::8]=True
    p2[15000:]+=.05
    b=signals(d2,p2)
    for k in CLOCK:
        if k>=15000:continue
        x,y=a[k],b[k]
        if x[1]!=y[1] or not np.array_equal(x[0],y[0]) or any(not np.array_equal(v,w) for v,w in zip(x[2],y[2])):
            raise ValueError("PK_FUTURE_LEAK")
    books=target_books(a)
    if any(len(v)!=157 or any(np.abs(w).sum()>.84+1e-10 for w in v.values()) for v in books.values()):
        raise ValueError("PK_SYNTHETIC_GROSS")
    return {"decision":"PASS_PK_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,"books":5,
            "premium_bar_t_excluded":True,"future_mutation_safe":True,"pnl_computed":False}

def run(d,premium):
    source=source_gate(d)
    decisions=signals(d,premium)
    books=target_books(decisions)
    from pk_premium_dislocation_independent_oracle import independent_decisions
    oracle=independent_decisions(d,premium,decisions,books)
    if oracle["mismatches"]:raise ValueError("PK_INDEPENDENT_ORACLE")
    print("PK_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PK_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PK_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    accounting=independent_accounting(d,ledger) if ledger is not None and len(ledger)==HOURS-WARMUP-1 else None
    fills=independent_fills(d,ledger) if accounting is not None else None
    failures=[];marginals={}
    slots=(("Opportunity","PK_minus_opportunity"),("Relative_Value","PK_minus_RV"),("Stress_Recovery","PK_minus_stress"))
    for tier in COSTS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["PK_full"]
            marginals[label]={slot:full["log_growth"]-group[book]["log_growth"] for slot,book in slots}
            if tier not in ("base","severe"):continue
            if full["cagr"]<=(.80 if tier=="base" else .60):failures.append(label+":CAGR")
            if full["turnover"]>1000000:failures.append(label+":turnover")
            if tier=="severe":
                if full["max_dd"]<=-.45:failures.append(label+":drawdown")
                if any(v<=0 for v in full["year_returns"].values()):failures.append(label+":annual")
            for slot,book in slots:
                if marginals[label][slot]<=.02:failures.append(label+":"+slot+":marginal")
                for year in ("2023","2024","2025"):
                    delta=math.log1p(full["year_returns"][year])-math.log1p(group[book]["year_returns"][year])
                    if delta<-.03:failures.append(label+":"+slot+":"+year+":annual_marginal")
    if accounting is None or accounting["cash_identity_mismatches"]:failures.append("independent_hourly_accounting")
    if fills is None or fills["independent_fee_slippage_funding_mismatches"]:failures.append("independent_fills_and_funding")
    out={"architecture":"PK","preregistration":"pk_premium_dislocation_prereg_20261101.md",
         "premium_source_sha256":PREMIUM_SHA,"premium_asset_hours":int(premium.size),
         "premium_last_closed_bar_at_decision":"t-1",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"independent_decision_oracle":oracle,
         "independent_accounting":accounting,"independent_fills":fills,
         "gate_failures":failures,
         "decision":"REJECT_PK_TRAINING" if failures else "PASS_PROVISIONAL_PK_TRAINING_NOT_VALIDATED",
         "2025_exposed_training_only":True,"exact_event_mark_attested":False,
         "2026_plus_accessed":False,"holdout_accessed":False,
         "external_benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PK_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
