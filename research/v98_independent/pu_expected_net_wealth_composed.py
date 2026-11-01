#!/usr/bin/env python3
"""PU: preregistered expected-net-wealth seven-slot composed V98 exposed training."""
import json, math, itertools
import numpy as np
from ot_breadth_dispersion import source_gate,physical,independent_accounting,COSTS,ORDERS,HOURS,WARMUP,STEP
from ot_independent_oracle import independent_fills

CLOCK=tuple(range(WARMUP,HOURS,STEP))
BOOKS={"PU_full":(0,1,2,3),"PU_core_only":(0,),
       "PU_minus_opportunity":(0,2,3),"PU_minus_RV":(0,1,3),
       "PU_minus_stress":(0,1,2)}
PRIORITY={"up":(1,2,3),"down":(3,2,1),"mixed":(2,1,3)}
H=168

def signals(d):
    c=np.asarray(d["c"],float);q=np.asarray(d["q"],float);rate=np.asarray(d["rate"],float)
    if c.shape!=(HOURS,4) or q.shape!=(HOURS,4) or rate.shape!=(HOURS,4):
        raise ValueError("PU_SOURCE_SHAPE")
    if not all(np.isfinite(a).all() for a in (c,q,rate)) or np.any(c<=0) or np.any(q<0):
        raise ValueError("PU_SOURCE_GEOMETRY")
    p=np.log(c);out={}
    ages=np.arange(335,-1,-1,dtype=float)
    ew=np.exp2(-ages/168.);ew/=ew.sum()
    for t in CLOCK:
        hourly=p[t-335:t+1]-p[t-336:t]
        mu=ew@hourly
        demean=hourly-mu
        emp=(demean*ew[:,None]).T@demean
        cov=.5*emp+.5*np.diag(np.diag(emp))
        f=rate[t-160:t+1:8].mean(axis=0)/8.
        edge=mu-f
        r24=p[t]-p[t-24];r72=p[t]-p[t-72]
        r168=p[t]-p[t-168];r336=p[t]-p[t-336]
        prior168=p[t-168]-p[t-336]
        ratio=q[t-71:t+1].sum(axis=0)/np.maximum(q[t-143:t-71].sum(axis=0),1.)
        raw=np.zeros((4,4),float)
        scores=H*(np.abs(edge)-.5*np.diag(cov))
        eligible=[j for j in range(4) if scores[j]>.015 and abs(r336[j])>=.04
                  and edge[j]*r336[j]>0]
        eligible.sort(key=lambda j:(-scores[j],j))
        for j,w in zip(eligible[:2],(.42,.20)):
            raw[0,j]=w if edge[j]>0 else -w
        acceleration=r168-prior168
        options=[j for j in range(4) if abs(acceleration[j])>=.12 and ratio[j]>=1.20
                 and acceleration[j]*edge[j]>0]
        if options:
            j=min(options,key=lambda k:(-abs(acceleration[k]),k))
            raw[1,j]=.16 if acceleration[j]>0 else -.16
        hi=min(range(4),key=lambda j:(-f[j],j))
        lo=min(range(4),key=lambda j:(f[j],j))
        if hi!=lo and (f[hi]-f[lo])*8>=.0015:
            raw[2,lo]=.10;raw[2,hi]=-.10
        if int(np.sum(r72<=-.10))>=3 and r24[0]<=-.04:
            raw[3,0]=-.14
        elif int(np.sum(r72<=-.08))>=3 and r24[0]>=.04:
            raw[3,0]=.14
        breadth=int(np.sum(r336>0))
        mode="up" if breadth>=3 else "down" if breadth<=1 else "mixed"
        out[t]=(raw,mode,mu,cov,f)
    if len(out)!=157:raise ValueError("PU_DECISION_CLOCK")
    return out

def allocate(raw,mode,mu,cov,f,prev,active):
    if raw.shape!=(4,4) or mode not in PRIORITY or any(x.shape!=(4,) for x in (mu,f,prev)) or cov.shape!=(4,4):
        raise ValueError("PU_ALLOC_INPUT")
    if not all(np.isfinite(x).all() for x in (raw,mu,cov,f,prev)):
        raise ValueError("PU_ALLOC_NONFINITE")
    choices=[]
    for bits in itertools.product((0,1),repeat=3):
        w=np.zeros((4,4),float)
        if 0 in active:w[0]=raw[0]
        room=min(.28,max(0.,.84-float(np.abs(w).sum())))
        for slot in PRIORITY[mode]:
            if slot not in active or not bits[slot-1] or room<=1e-12:continue
            gross=float(np.abs(raw[slot]).sum())
            if gross<=1e-12:continue
            take=min(gross,room)
            w[slot]=raw[slot]*(take/gross)
            room-=take
        net=w.sum(axis=0)
        turn=float(np.abs(net-prev).sum())
        gross=float(np.abs(w).sum())
        if gross>.84+1e-10 or float(np.abs(w[1:]).sum())>.28+1e-10:
            raise ValueError("PU_GROSS")
        util=H*(float(np.dot(net,mu-f))-.5*float(net@cov@net))-.0006*turn
        choices.append((util,turn,gross,bits,w,net))
    baseline=next(x for x in choices if x[3]==(0,0,0))
    best=min(choices,key=lambda x:(-round(x[0],12),x[1],x[2],x[3]))
    if best[0]<=baseline[0]+1e-12:best=baseline
    return best[4].copy()

def target_books(decisions):
    result={}
    for name,active in BOOKS.items():
        prev=np.zeros(4,float);book={}
        for t,(raw,mode,mu,cov,f) in decisions.items():
            w=allocate(raw,mode,mu,cov,f,prev,active)
            book[t]=w;prev=w.sum(axis=0)
        result[name]=book
    return result

def synthetic_test():
    t=np.arange(HOURS,dtype=float)[:,None];j=np.arange(4,dtype=float)[None,:]
    c=100*np.exp(.000025*t*(1+j/7)+.08*np.sin(t/41+j)+.015*np.cos(t/13+j))
    q=np.broadcast_to(1e6*(1+.3*np.sin(t/17+j)),(HOURS,4)).copy()
    rate=np.broadcast_to(.00008+.00004*np.sin(t/100+j),(HOURS,4)).copy()
    a=signals({"c":c,"q":q,"rate":rate})
    b=c.copy();b[15000:]*=np.array([1.7,.8,1.3,.6])
    v=q.copy();v[15000:]*=3.;r=rate.copy();r[15000:]*=5.
    mutated=signals({"c":b,"q":v,"rate":r})
    for k in CLOCK:
        if k>=15000:continue
        if a[k][1]!=mutated[k][1] or not np.array_equal(a[k][0],mutated[k][0]):
            raise ValueError("PU_FUTURE_SIGNAL_LEAK")
        for x,y in zip(a[k][2:],mutated[k][2:]):
            if not np.array_equal(x,y):raise ValueError("PU_FUTURE_FORECAST_LEAK")
    first=target_books(a);second=target_books(mutated)
    for name,book in first.items():
        if len(book)!=157:raise ValueError("PU_BOOK_CLOCK")
        for k,w in book.items():
            if np.abs(w).sum()>.84+1e-10:raise ValueError("PU_GROSS_TEST")
            if k<15000 and not np.array_equal(w,second[name][k]):
                raise ValueError("PU_FUTURE_ALLOCATOR_LEAK")
    return {"decision":"PASS_PU_SYNTHETIC_CAUSALITY_NOT_PNL","decisions":157,
            "books":5,"future_mutation_safe":True,"pnl_computed":False}

def run(d):
    source=source_gate(d)
    decisions=signals(d);books=target_books(decisions)
    from pu_expected_net_wealth_oracle import independent_decisions
    oracle=independent_decisions(d,decisions,books)
    if oracle["mismatches"]:raise ValueError("PU_INDEPENDENT_DECISION_ORACLE")
    print("PU_ORACLE",json.dumps(oracle,sort_keys=True),flush=True)
    cells=[];ledger=None
    for tier in COSTS:
        for order in ORDERS:
            for book in BOOKS:
                capture=tier=="base" and order=="carried_before_fill" and book=="PU_full"
                row,detail=physical(d,books[book],book,tier,order,record=capture)
                cells.append(row)
                if capture:ledger=detail
                print("PU_CELL",tier,order,book,row["passed"],row.get("cagr"),row.get("failure"),flush=True)
    accounting=independent_accounting(d,ledger) if ledger is not None and len(ledger)==HOURS-WARMUP-1 else None
    fills=independent_fills(d,ledger) if accounting is not None else None
    failures=[];marginals={}
    slots=(("Opportunity","PU_minus_opportunity"),("Relative_Value","PU_minus_RV"),
           ("Stress_Recovery","PU_minus_stress"))
    for tier in COSTS:
        for order in ORDERS:
            group={r["book"]:r for r in cells if r["tier"]==tier and r["order"]==order}
            label=tier+"/"+order
            if not all(r["passed"] for r in group.values()):
                failures.append(label+":physical");continue
            full=group["PU_full"]
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
    out={"architecture":"PU","preregistration":"pu_expected_net_wealth_prereg_20261101.md",
         "source":source,"weekly_decisions":len(decisions),"cells":cells,"marginals":marginals,
         "independent_decision_oracle":oracle,"independent_accounting":accounting,
         "independent_fills":fills,"gate_failures":failures,
         "decision":"REJECT_PU_TRAINING" if failures else "PASS_PROVISIONAL_PU_TRAINING_NOT_VALIDATED",
         "2025_exposed_training_only":True,"exact_event_mark_attested":False,
         "2026_plus_accessed":False,"holdout_accessed":False,
         "external_benchmarks_accessed":False,"paper_or_live_authorized":False}
    print("PU_RESULT_JSON",json.dumps(out,separators=(",",":"),allow_nan=False),flush=True)
    return out

if __name__=="__main__":
    print(json.dumps(synthetic_test(),sort_keys=True))
