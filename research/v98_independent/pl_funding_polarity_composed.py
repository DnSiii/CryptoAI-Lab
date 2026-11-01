#!/usr/bin/env python3
"""PL premium-dislocation seven-slot composed V98 training. 2025 exposed; no holdout."""
import csv, datetime as dt, hashlib, json, math
from pathlib import Path
import numpy as np
from ot_breadth_dispersion import source_gate, physical, independent_accounting, COSTS, ORDERS, HOURS, WARMUP, STEP
from ot_independent_oracle import independent_fills

ASSETS=("BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT")
SOURCE_ORDER=tuple(sorted(ASSETS))
PREMIUM_SHA="c301a38642f229ca2746ae33baaf58e4bb21ac280a1a99dbbc328cc074caaad4"
CLOCK=tuple(range(WARMUP,HOURS,STEP))
BOOKS={"PL_full":(0,1,2,3),"PL_core_only":(0,),
       "PL_minus_opportunity":(0,2,3),"PL_minus_RV":(0,1,3),
       "PL_minus_stress":(0,1,2)}
PRIORITY={"negative_carry":(1,2,3),"positive_carry":(3,2,1),"mixed_carry":(2,1,3)}

def load_premium(path, expected_time):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=PREMIUM_SHA:
        raise ValueError("PL_PREMIUM_SOURCE_SHA_MISMATCH")
    p=np.empty((HOURS,4),float)
    start=dt.datetime(2022,12,1,tzinfo=dt.timezone.utc)
    with path.open(newline="") as f:
        rows=csv.DictReader(f)
        if rows.fieldnames!=["asset","bar_open_utc","premium_open","premium_high","premium_low","premium_close","source_zip_sha256"]:
            raise ValueError("PL_PREMIUM_SCHEMA")
        count=0
        for row in rows:
            hour,j=divmod(count,4)
            if hour>=HOURS or row["asset"]!=SOURCE_ORDER[j]:
                raise ValueError("PL_PREMIUM_ORDER")
            timestamp=dt.datetime.fromisoformat(row["bar_open_utc"])
            if timestamp!=start+dt.timedelta(hours=hour) or timestamp!=expected_time[hour].to_pydatetime():
                raise ValueError("PL_PREMIUM_CLOCK")
            o,h,l,c=[float(row[k]) for k in ("premium_open","premium_high","premium_low","premium_close")]
            if not all(math.isfinite(x) and abs(x)<1 for x in (o,h,l,c)) or l>min(o,c)+1e-10 or h<max(o,c)-1e-10:
                raise ValueError("PL_PREMIUM_GEOMETRY")
            if len(row["source_zip_sha256"])!=64:
                raise ValueError("PL_PREMIUM_VENDOR_PROVENANCE")
            p[hour,ASSETS.index(row["asset"])]=c
            count+=1
    if count!=HOURS*4 or not np.isfinite(p).all():
        raise ValueError("PL_PREMIUM_COMPLETENESS")
    return p

def signals(d,premium):
    c=np.asarray(d["c"],float)
    rate=np.asarray(d["rate"],float);event=np.asarray(d["event"],bool)
    if (c.shape!=(HOURS,4) or premium.shape!=(HOURS,4) or
        rate.shape!=(HOURS,4) or event.shape!=(HOURS,4) or
        not np.isfinite(premium).all() or not np.isfinite(rate).all() or np.any(c<=0)):
        raise ValueError("PL_SIGNAL_GEOMETRY")
    p=np.log(c);out={}
    for t in CLOCK:
        # Exclude funding event t (even if present); only settled t-8...t-168.
        if not np.all(event[t-168:t:8]) or np.any(rate[t-167:t:8]!=0):
            raise ValueError("PL_FUNDING_CAUSAL_EVENT_CLOCK")
        f=np.mean(rate[t-168:t:8],axis=0)
        f3=np.mean(rate[t-24:t:8],axis=0)
        m=premium[t-1]  # premium bar at t is incomplete
        r24=p[t]-p[t-24];r72=p[t]-p[t-72]
        r168=p[t]-p[t-168];r336=p[t]-p[t-336]
        hourly=np.diff(p[t-336:t+1],axis=0)
        quality=np.abs(r336)/np.maximum(np.std(hourly,axis=0)*math.sqrt(336),.04)
        raw=np.zeros((4,4),float)
        long=(r336>.08)&(f<0)&(m<0)&(r72>0)
        short=(r336<-.08)&(f>0)&(m>0)&(r72<0)
        eligible=sorted((j for j in range(4) if long[j] or short[j]),
                        key=lambda j:(-quality[j],j))
        for j,w in zip(eligible[:2],(.46,.28)):
            raw[0,j]=w if long[j] else -w
        negative=sorted((j for j in range(4) if f3[j]<-.00006 and f[j]<0 and m[j]<0 and r72[j]>.025),
                        key=lambda j:(f3[j],j))
        positive=sorted((j for j in range(4) if f3[j]>.00006 and f[j]>0 and m[j]>0 and r72[j]<-.025),
                        key=lambda j:(-f3[j],j))
        if negative:raw[1,negative[0]]=.24
        elif positive:raw[1,positive[0]]=-.24
        high=min(range(4),key=lambda j:(-f[j],j))
        low=min(range(4),key=lambda j:(f[j],j))
        if high!=low and f[high]-f[low]>.00010 and abs(r168[high]-r168[low])<.10:
            raw[2,low]=.14;raw[2,high]=-.14
        if r24[0]<-.08 and f[0]>.00005 and m[0]<0:
            raw[3,0]=-.18
        elif r24[0]>.08 and f[0]<-.00005 and m[0]>0:
            raw[3,0]=.18
        med=float(np.median(f))
        mode="negative_carry" if med<-.00003 else "positive_carry" if med>.00003 else "mixed_carry"
        out[t]=(raw,mode,(f,f3))
    if len(out)!=157:raise ValueError("PL_WEEKLY_CLOCK")
    return out

def allocate(raw,mode,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or not np.isfinite(raw).all():
        raise ValueError("PL_ALLOCATOR_GEOMETRY")
    held=np.zeros((4,4),float)
    if 0 in active:held[0]=raw[0]
    core=float(np.abs(held[0]).sum())
    if core>.74+1e-10:raise ValueError("PL_CORE_GROSS")
    room=min(.32,max(0.,.84-core))
    for slot in PRIORITY[mode]:
        if slot not in active or room<=1e-12:continue
        gross=float(np.abs(raw[slot]).sum())
        if gross<=1e-12:continue
        take=min(room,gross)
        held[slot]=raw[slot]*(take/gross)
        room-=take
    if np.abs(held).sum()>.84+1e-10 or np.abs(held[1:]).sum()>.32+1e-10:
        raise ValueError("PL_GROSS")
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
            raise ValueError("PL_FUTURE_LEAK")
    books=target_books(a)
    if any(len(v)!=157 or any(np.abs(w).sum()>.84+1e-10 for w in v.values()) for v in books.values()):
        raise ValueError("PL_SYNTHETIC_GROSS")
    return {"decision":"PASS_PL_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,"books":5,
            "premium_bar_t_excluded":True,"future_mutation_safe":True,"pnl_computed":False}

def run(d,premium):
    source=source_gate(d)
    decisions=signals(d,premium)
    books=target_books(decisions)
    from pl_funding_polarity_independent_oracle import independent_decisions
    oracle=independent_decisions(d,premium,decisions,books)
    if oracle["mismatches"]:raise ValueError("PL_INDEPENDENT_ORACLE")
    print("PL_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PL_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PL_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    accounting=independent_accounting(d,ledger) if ledger is not None and len(ledger)==HOURS-WARMUP-1 else None
    fills=independent_fills(d,ledger) if accounting is not None else None
    failures=[];marginals={}
    slots=(("Opportunity","PL_minus_opportunity"),("Relative_Value","PL_minus_RV"),("Stress_Recovery","PL_minus_stress"))
    for tier in COSTS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["PL_full"]
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
    out={"architecture":"PL","preregistration":"pl_funding_polarity_prereg_20261101.md",
         "premium_source_sha256":PREMIUM_SHA,"premium_asset_hours":int(premium.size),
         "premium_last_closed_bar_at_decision":"t-1",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,
         "marginals":marginals,"independent_decision_oracle":oracle,
         "independent_accounting":accounting,"independent_fills":fills,
         "gate_failures":failures,
         "decision":"REJECT_PL_TRAINING" if failures else "PASS_PROVISIONAL_PL_TRAINING_NOT_VALIDATED",
         "2025_exposed_training_only":True,"exact_event_mark_attested":False,
         "2026_plus_accessed":False,"holdout_accessed":False,
         "external_benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PL_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":print(json.dumps(synthetic_test(),sort_keys=True))
